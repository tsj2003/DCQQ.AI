"""
Document ORM model for uploaded files (PDF, audio, video).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    """Document model for uploaded PDF, audio, and video files."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pdf, audio, video
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="processing"
    )  # processing, ready, error
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="documents")
    chat_sessions = relationship(
        "ChatSession", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, filename={self.filename}, type={self.file_type})>"
        )
