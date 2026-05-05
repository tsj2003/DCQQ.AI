"""
Media API endpoints — serve uploaded media files for playback.
"""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.models.document import Document

router = APIRouter(prefix="/api/media", tags=["Media"])

MEDIA_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
}


@router.get("/{document_id}")
async def serve_media(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Serve an uploaded media file for playback.

    Supports range requests for seeking within audio/video files.
    """
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_type not in ("audio", "video"):
        raise HTTPException(status_code=400, detail="Document is not a media file")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Media file not found on disk")

    ext = os.path.splitext(doc.file_path)[1].lower()
    media_type = MEDIA_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        doc.file_path,
        media_type=media_type,
        filename=doc.filename,
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/{document_id}/transcript")
async def get_transcript(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the full transcript with timestamps for a media file."""
    doc = await db.get(Document, uuid.UUID(document_id))
    if doc is None or str(doc.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_type not in ("audio", "video"):
        raise HTTPException(status_code=400, detail="Document is not a media file")

    if not doc.transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")

    return doc.transcript
