"""
File upload API endpoints.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db, async_session
from app.middleware.auth_middleware import get_current_user_id
from app.models.document import Document
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.pdf_service import extract_text_from_pdf, chunk_text, get_pdf_metadata
from app.services.transcription import transcribe_media_file, chunk_transcript
from app.services.vector_store import get_vector_store
from app.services.summary_service import summarize_chunks

settings = get_settings()

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {
    "pdf": [".pdf"],
    "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
    "video": [".mp4", ".webm", ".mov", ".avi", ".mkv"],
}


def _get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = Path(filename).suffix.lower()
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    raise ValueError(f"Unsupported file type: {ext}")


async def _process_document(document_id: str, file_path: str, file_type: str):
    """Background task to process uploaded document.

    Extracts text/transcript, generates embeddings, builds vector index, and creates summary.
    """
    async with async_session() as db:
        try:
            doc = await db.get(Document, uuid.UUID(document_id))
            if doc is None:
                return

            chunks = []

            if file_type == "pdf":
                # Extract text from PDF
                pages = extract_text_from_pdf(file_path)
                chunks = chunk_text(pages)
                metadata = get_pdf_metadata(file_path)
                doc.metadata_json = metadata

            elif file_type in ("audio", "video"):
                # Transcribe media file
                transcript = await transcribe_media_file(file_path)
                doc.transcript = transcript
                chunks = chunk_transcript(transcript)
                doc.metadata_json = {
                    "duration": transcript["segments"][-1]["end"]
                    if transcript["segments"]
                    else 0,
                    "segment_count": len(transcript["segments"]),
                }

            # Build vector index
            if chunks:
                vector_store = get_vector_store(document_id)
                await vector_store.build_index(chunks)

                # Generate summary
                summary = await summarize_chunks(chunks)
                doc.summary = summary

            doc.status = "ready"
            await db.commit()

        except Exception as e:
            doc = await db.get(Document, uuid.UUID(document_id))
            if doc:
                doc.status = "error"
                doc.error_message = str(e)
                await db.commit()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, audio, or video file for processing.

    The file is saved to disk and processed asynchronously in the background.
    """
    # Validate file type
    try:
        file_type = _get_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty.",
        )

    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Save file to disk
    doc_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR) / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix
    file_path = upload_dir / f"{doc_id}{file_ext}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(user_id),
        filename=file.filename,
        file_type=file_type,
        file_path=str(file_path),
        file_size=file_size,
        status="processing",
    )
    db.add(document)
    await db.flush()

    # Process in background
    background_tasks.add_task(_process_document, doc_id, str(file_path), file_type)

    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == uuid.UUID(user_id))
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific document."""
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its associated data."""
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.unlink(doc.file_path)

    # Delete vector index
    vector_store = get_vector_store(document_id)
    vector_store.delete()

    # Delete from database
    await db.delete(doc)
    await db.commit()

    return {"detail": "Document deleted successfully"}
