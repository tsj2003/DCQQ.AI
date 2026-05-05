"""
Tests for vector store service.
"""

import json
import os
import pickle
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import faiss
import numpy as np
import pytest

from app.services.vector_store import FAISSVectorStore, get_vector_store


@pytest.fixture
def mock_embeddings():
    with patch("app.services.vector_store.generate_embeddings") as mock:
        mock.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        yield mock

@pytest.fixture
def mock_single_embedding():
    with patch("app.services.vector_store.generate_single_embedding") as mock:
        mock.return_value = [0.1, 0.2, 0.3]
        yield mock


@pytest.mark.asyncio
async def test_build_index(mock_embeddings, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.settings.FAISS_INDEX_DIR", str(tmp_path))
    
    store = FAISSVectorStore("doc1", dimension=3)
    chunks = [
        {"text": "hello", "metadata": {"page": 1}},
        {"text": "world", "metadata": {"page": 2}},
    ]
    
    count = await store.build_index(chunks)
    assert count == 2
    assert store.index is not None
    assert store.index.ntotal == 2
    
    # Check that files were saved
    assert (tmp_path / "doc1" / "index.faiss").exists()
    assert (tmp_path / "doc1" / "metadata.json").exists()
    assert (tmp_path / "doc1" / "texts.pkl").exists()

@pytest.mark.asyncio
async def test_search(mock_embeddings, mock_single_embedding, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.settings.FAISS_INDEX_DIR", str(tmp_path))
    
    store = FAISSVectorStore("doc2", dimension=3)
    chunks = [
        {"text": "hello", "metadata": {"page": 1}},
        {"text": "world", "metadata": {"page": 2}},
    ]
    await store.build_index(chunks)
    
    results = await store.search("hello", top_k=1)
    assert len(results) == 1
    assert "text" in results[0]
    assert "metadata" in results[0]
    assert "score" in results[0]

@pytest.mark.asyncio
async def test_load_existing_index(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.settings.FAISS_INDEX_DIR", str(tmp_path))
    
    doc_id = "doc3"
    index_dir = tmp_path / doc_id
    index_dir.mkdir()
    
    # Create fake files
    index = faiss.IndexFlatIP(3)
    vectors = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)
    faiss.normalize_L2(vectors)  # in-place normalization
    index.add(vectors)
    faiss.write_index(index, str(index_dir / "index.faiss"))
    
    with open(index_dir / "metadata.json", "w") as f:
        json.dump([{"page": 1}], f)
    with open(index_dir / "texts.pkl", "wb") as f:
        pickle.dump(["test"], f)
        
    store = FAISSVectorStore(doc_id, dimension=3)
    store._load()
    
    assert store.index is not None
    assert store.index.ntotal == 1
    assert store.texts == ["test"]
    assert store.metadata_list == [{"page": 1}]

def test_delete(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.settings.FAISS_INDEX_DIR", str(tmp_path))
    doc_id = "doc4"
    index_dir = tmp_path / doc_id
    index_dir.mkdir()
    
    store = FAISSVectorStore(doc_id, dimension=3)
    store.delete()
    
    assert not index_dir.exists()

def test_get_vector_store():
    store = get_vector_store("doc_test")
    assert isinstance(store, FAISSVectorStore)
    assert store.document_id == "doc_test"
