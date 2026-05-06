"""
Pydantic schemas for documents.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: UUID
    filename: str
    file_type: str
    file_size: int | None
    status: str
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response with transcript."""

    transcript: dict | None = None
    metadata_json: dict | None = None
    error_message: str | None = None


class DocumentListResponse(BaseModel):
    """List of documents."""

    documents: list[DocumentResponse]
    total: int


class SummaryResponse(BaseModel):
    """Document summary response."""

    document_id: UUID
    summary: str
    word_count: int
