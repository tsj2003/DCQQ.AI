"""
Edge case tests for chat API.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.main import app
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_chat_db():
    session = AsyncMock()
    def track_add(obj):
        if hasattr(obj, 'created_at') and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid.uuid4()
    session.add = MagicMock(side_effect=track_add)
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=mock_ctx)
    return session


@pytest.mark.asyncio
async def test_list_sessions_with_pagination(async_client, override_auth, mock_chat_db):
    """Test listing sessions with limit and offset."""
    override_db(mock_chat_db)

    mock_result = MagicMock()
    mock_doc = Document(
        id=uuid.uuid4(),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        status="ready",
    )
    mock_session = ChatSession(
        id=uuid.uuid4(),
        user_id=uuid.UUID(override_auth),
        document_id=mock_doc.id,
        title="Test Session",
        created_at=datetime.now(timezone.utc),
    )
    mock_result.scalars().all.return_value = [mock_session]
    mock_chat_db.execute.return_value = mock_result

    response = await async_client.get("/api/chat/sessions?limit=5&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "sessions" in data


@pytest.mark.asyncio
async def test_create_session_no_title(async_client, override_auth, mock_chat_db):
    """Test creating session without title uses default."""
    override_db(mock_chat_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="my_document.pdf",
        status="ready",
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_doc

    response = await async_client.post(
        "/api/chat/sessions",
        json={"document_id": doc_id},
    )

    assert response.status_code == 200
    data = response.json()
    # Should use document filename as default title
    assert "title" in data


@pytest.mark.asyncio
async def test_create_session_document_not_ready(async_client, override_auth, mock_chat_db):
    """Test creating session when document is processing."""
    override_db(mock_chat_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_doc

    response = await async_client.post(
        "/api/chat/sessions",
        json={"document_id": doc_id, "title": "Test"},
    )

    assert response.status_code == 400
    assert "still processing" in response.json()["detail"]
