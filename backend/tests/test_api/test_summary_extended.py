"""
Extended tests for summary API.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.main import app
from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_summary_db():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_summary_not_found(async_client, override_auth, mock_summary_db):
    """Test getting summary for non-existent document."""
    override_db(mock_summary_db)
    
    doc_id = str(uuid.uuid4())
    mock_summary_db.get.return_value = None
    
    response = await async_client.get(f"/api/documents/{doc_id}/summary")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_summary_wrong_owner(async_client, override_auth, mock_summary_db):
    """Test getting summary for document owned by another user."""
    override_db(mock_summary_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),  # Different user
        filename="test.pdf",
        status="ready",
        summary="Test summary",
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc
    
    response = await async_client.get(f"/api/documents/{doc_id}/summary")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_summary_not_found(async_client, override_auth, mock_summary_db):
    """Test regenerating summary for non-existent document."""
    override_db(mock_summary_db)
    
    doc_id = str(uuid.uuid4())
    mock_summary_db.get.return_value = None
    
    response = await async_client.post(f"/api/documents/{doc_id}/summary")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_summary_wrong_owner(async_client, override_auth, mock_summary_db):
    """Test regenerating summary for document owned by another user."""
    override_db(mock_summary_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),  # Different user
        filename="test.pdf",
        status="ready",
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc
    
    response = await async_client.post(f"/api/documents/{doc_id}/summary")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_summary_video(async_client, override_auth, mock_summary_db):
    """Test regenerating summary for video with transcript."""
    override_db(mock_summary_db)
    
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.mp4",
        file_type="video",
        status="ready",
        transcript={"full_text": "Video transcript content"},
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc
    
    with patch("app.api.summary.summarize_text") as mock_summarize:
        mock_summarize.return_value = "Video summary"
        
        response = await async_client.post(f"/api/documents/{doc_id}/summary")
        
        assert response.status_code == 200
        assert response.json()["summary"] == "Video summary"
