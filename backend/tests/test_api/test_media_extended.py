"""
Extended tests for media API.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.main import app
from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_media_db():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_media_file_not_found(async_client, override_auth, mock_media_db):
    """Test streaming non-existent media file."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_media_db.get.return_value = None
    
    response = await async_client.get(f"/api/media/{doc_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_media_file_wrong_owner(async_client, override_auth, mock_media_db):
    """Test streaming media owned by another user."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),  # Different user
        filename="test.mp4",
        file_type="video",
        file_path="/tmp/test.mp4",
        created_at=datetime.now(timezone.utc),
    )
    mock_media_db.get.return_value = mock_doc
    
    response = await async_client.get(f"/api/media/{doc_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_media_file_not_audio_video(async_client, override_auth, mock_media_db):
    """Test streaming non-media file type."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        created_at=datetime.now(timezone.utc),
    )
    mock_media_db.get.return_value = mock_doc
    
    response = await async_client.get(f"/api/media/{doc_id}")
    
    assert response.status_code == 400
    assert "not a media file" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_transcript_not_found(async_client, override_auth, mock_media_db):
    """Test getting transcript for non-existent document."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_media_db.get.return_value = None
    
    response = await async_client.get(f"/api/media/{doc_id}/transcript")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_transcript_no_transcript(async_client, override_auth, mock_media_db):
    """Test getting transcript when document has none."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.mp4",
        file_type="video",
        transcript=None,
        created_at=datetime.now(timezone.utc),
    )
    mock_media_db.get.return_value = mock_doc
    
    response = await async_client.get(f"/api/media/{doc_id}/transcript")
    
    assert response.status_code == 404
    assert "not available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_transcript_pdf_document(async_client, override_auth, mock_media_db):
    """Test getting transcript for PDF (not a media file)."""
    override_db(mock_media_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        transcript=None,
        created_at=datetime.now(timezone.utc),
    )
    mock_media_db.get.return_value = mock_doc
    
    response = await async_client.get(f"/api/media/{doc_id}/transcript")
    
    # PDFs return 400 because they're not media files
    assert response.status_code == 400
