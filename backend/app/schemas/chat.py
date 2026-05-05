"""
Pydantic schemas for chat.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimestampRef(BaseModel):
    """Timestamp reference for audio/video content."""
    start: float
    end: float
    text: str


class SourceRef(BaseModel):
    """Source reference for PDF content."""
    page: int | None = None
    text: str


class ChatMessageRequest(BaseModel):
    """Chat message input."""
    content: str


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: UUID
    role: str
    content: str
    timestamps: list[TimestampRef] | None = None
    sources: list[SourceRef] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionCreate(BaseModel):
    """Create chat session request."""
    document_id: UUID
    title: str | None = None


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    id: UUID
    document_id: UUID
    title: str | None
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    """List of chat sessions."""
    sessions: list[ChatSessionResponse]
    total: int
