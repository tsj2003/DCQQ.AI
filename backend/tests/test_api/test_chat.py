"""
Tests for chat API endpoints.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_chat_db():
    session = AsyncMock()
    # Simulate that add + flush triggers default values
    def track_add(obj):
        if hasattr(obj, 'created_at') and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid.uuid4()

    session.add = MagicMock(side_effect=track_add)

    # Mock db.begin() to return a proper async context manager
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=mock_ctx)

    return session


@pytest.mark.asyncio
async def test_create_chat_session_success(async_client, override_auth, mock_chat_db):
    override_db(mock_chat_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        status="ready",
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_doc

    response = await async_client.post(
        "/api/chat/sessions",
        json={"document_id": doc_id, "title": "Test Chat"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Chat"
    assert data["message_count"] == 0


@pytest.mark.asyncio
async def test_create_chat_session_processing_doc(async_client, override_auth, mock_chat_db):
    override_db(mock_chat_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_doc

    response = await async_client.post(
        "/api/chat/sessions",
        json={"document_id": doc_id},
    )

    assert response.status_code == 400
    assert "still processing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_chat_history(async_client, override_auth, mock_chat_db):
    override_db(mock_chat_db)

    session_id = str(uuid.uuid4())
    mock_session = ChatSession(
        id=uuid.UUID(session_id),
        user_id=uuid.UUID(override_auth),
        document_id=uuid.uuid4(),
        title="Test",
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_session

    mock_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=uuid.UUID(session_id),
        role="user",
        content="Hello",
        created_at=datetime.now(timezone.utc),
    )

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_msg]
    mock_chat_db.execute.return_value = mock_result

    response = await async_client.get(
        f"/api/chat/sessions/{session_id}/messages"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_send_message_stream(async_client, override_auth, mock_chat_db):
    override_db(mock_chat_db)

    session_id = str(uuid.uuid4())
    mock_session = ChatSession(
        id=uuid.UUID(session_id),
        user_id=uuid.UUID(override_auth),
        document_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
    )
    mock_chat_db.get.return_value = mock_session

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    mock_chat_db.execute.return_value = mock_result

    async def mock_stream(*args, **kwargs):
        yield 'event: token\ndata: {"content": "Hello", "done": false}\n\n'
        yield 'event: done\ndata: {"content": "Hello", "done": true}\n\n'

    with patch(
        "app.api.chat.chat_with_document_stream", side_effect=mock_stream
    ):
        response = await async_client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"content": "Hi"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
