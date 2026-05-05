"""
Summary API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.document import Document
from app.schemas.document import SummaryResponse
from app.services.summary_service import summarize_text

router = APIRouter(prefix="/api/documents", tags=["Summary"])


@router.get("/{document_id}/summary", response_model=SummaryResponse)
async def get_document_summary(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the summary of a document."""
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document is still processing")

    if not doc.summary:
        raise HTTPException(status_code=404, detail="Summary not available")

    return SummaryResponse(
        document_id=doc.id,
        summary=doc.summary,
        word_count=len(doc.summary.split()),
    )


@router.post("/{document_id}/summary", response_model=SummaryResponse)
async def regenerate_summary(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate the summary of a document."""
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document is still processing")

    # Get content for summarization
    content = ""
    if doc.file_type == "pdf":
        from app.services.pdf_service import extract_text_from_pdf
        pages = extract_text_from_pdf(doc.file_path)
        content = "\n\n".join(p["text"] for p in pages)
    elif doc.transcript:
        content = doc.transcript.get("full_text", "")

    if not content:
        raise HTTPException(status_code=400, detail="No content available for summarization")

    summary = await summarize_text(content)
    doc.summary = summary
    await db.flush()

    return SummaryResponse(
        document_id=doc.id,
        summary=summary,
        word_count=len(summary.split()),
    )
