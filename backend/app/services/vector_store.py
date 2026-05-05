"""
Vector store service using FAISS for semantic search.
"""

import json
import pickle
from pathlib import Path

import faiss
import numpy as np

from app.config import get_settings
from app.services.embedding import generate_single_embedding, generate_embeddings

settings = get_settings()

# Initialize GCS client if bucket is configured
_gcs_client = None
if settings.GCP_STORAGE_BUCKET:
    from google.cloud import storage
    _gcs_client = storage.Client(project=settings.GCP_PROJECT_ID)


class FAISSVectorStore:
    """FAISS-based vector store for document retrieval."""

    def __init__(self, document_id: str, dimension: int = 1536):
        """Initialize vector store for a specific document.

        Args:
            document_id: Unique document identifier.
            dimension: Embedding dimension (1536 for text-embedding-3-small).
        """
        self.document_id = document_id
        self.dimension = dimension
        self.index_dir = Path(settings.FAISS_INDEX_DIR) / document_id
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.json"
        self.texts_path = self.index_dir / "texts.pkl"

        self.index = None
        self.metadata_list: list[dict] = []
        self.texts: list[str] = []

    def _ensure_dir(self):
        """Create index directory if it doesn't exist."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

    async def build_index(self, chunks: list[dict]) -> int:
        """Build FAISS index from text chunks.

        Args:
            chunks: List of dicts with 'text' and 'metadata' keys.

        Returns:
            Number of vectors indexed.
        """
        if not chunks:
            return 0

        self._ensure_dir()

        # Extract texts and metadata
        texts = [chunk["text"] for chunk in chunks]
        metadata = [chunk["metadata"] for chunk in chunks]

        # Generate embeddings in batches
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await generate_embeddings(batch)
            all_embeddings.extend(embeddings)

        # Create FAISS index
        vectors = np.array(all_embeddings, dtype=np.float32)
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine with normalized vectors)

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)
        self.index.add(vectors)

        self.texts = texts
        self.metadata_list = metadata

        # Save to disk
        self._save()

        return len(texts)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for similar chunks using a query string.

        Args:
            query: Search query text.
            top_k: Number of results to return.

        Returns:
            List of result dicts with 'text', 'metadata', and 'score' keys.
        """
        if self.index is None:
            self._load()

        if self.index is None or self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = await generate_single_embedding(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)

        # Search
        scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "text": self.texts[idx],
                "metadata": self.metadata_list[idx],
                "score": float(score),
            })

        return results

    def _save(self):
        """Save index and metadata to disk or Cloud Storage."""
        self._ensure_dir()
        
        # Save locally first
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata_list, f)
        with open(self.texts_path, "wb") as f:
            pickle.dump(self.texts, f)
        
        # Upload to GCS if configured
        if _gcs_client and settings.GCP_STORAGE_BUCKET:
            self._upload_to_gcs()

    def _upload_to_gcs(self):
        """Upload index files to Google Cloud Storage."""
        bucket = _gcs_client.bucket(settings.GCP_STORAGE_BUCKET)
        prefix = f"faiss_indices/{self.document_id}"
        
        # Upload index
        blob = bucket.blob(f"{prefix}/index.faiss")
        blob.upload_from_filename(str(self.index_path))
        
        # Upload metadata
        blob = bucket.blob(f"{prefix}/metadata.json")
        blob.upload_from_filename(str(self.metadata_path))
        
        # Upload texts
        blob = bucket.blob(f"{prefix}/texts.pkl")
        blob.upload_from_filename(str(self.texts_path))

    def _load(self):
        """Load index and metadata from disk or Cloud Storage."""
        # Try local first
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "r") as f:
                self.metadata_list = json.load(f)
            with open(self.texts_path, "rb") as f:
                self.texts = pickle.load(f)
            return
        
        # Try GCS if configured
        if _gcs_client and settings.GCP_STORAGE_BUCKET:
            self._download_from_gcs()

    def _download_from_gcs(self):
        """Download index files from Google Cloud Storage."""
        try:
            bucket = _gcs_client.bucket(settings.GCP_STORAGE_BUCKET)
            prefix = f"faiss_indices/{self.document_id}"
            
            self._ensure_dir()
            
            # Download index
            blob = bucket.blob(f"{prefix}/index.faiss")
            if blob.exists():
                blob.download_to_filename(str(self.index_path))
                
                # Download metadata
                blob = bucket.blob(f"{prefix}/metadata.json")
                blob.download_to_filename(str(self.metadata_path))
                
                # Download texts
                blob = bucket.blob(f"{prefix}/texts.pkl")
                blob.download_to_filename(str(self.texts_path))
                
                # Load into memory
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, "r") as f:
                    self.metadata_list = json.load(f)
                with open(self.texts_path, "rb") as f:
                    self.texts = pickle.load(f)
        except Exception:
            # Silently fail if not found in GCS
            pass

    def delete(self):
        """Delete the index from disk and Cloud Storage."""
        import shutil
        if self.index_dir.exists():
            shutil.rmtree(self.index_dir)
        
        # Also delete from GCS if configured
        if _gcs_client and settings.GCP_STORAGE_BUCKET:
            try:
                bucket = _gcs_client.bucket(settings.GCP_STORAGE_BUCKET)
                prefix = f"faiss_indices/{self.document_id}"
                for blob in bucket.list_blobs(prefix=prefix):
                    blob.delete()
            except Exception:
                pass


def get_vector_store(document_id: str) -> FAISSVectorStore:
    """Factory function to get a vector store instance for a document."""
    return FAISSVectorStore(document_id=document_id)
