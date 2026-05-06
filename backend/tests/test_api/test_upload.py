"""
Tests for upload API endpoints.
"""

import uuid
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_upload_db():
    session = AsyncMock()

    def track_add(obj):
        """Set defaults that SQLAlchemy would normally set on flush."""
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if hasattr(obj, "id") and obj.id is None:
            obj.id = uuid.uuid4()

    session.add = MagicMock(side_effect=track_add)
    return session


@pytest.mark.asyncio
async def test_upload_document_success(async_client, override_auth, mock_upload_db):
    override_db(mock_upload_db)

    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

    with patch("app.api.upload._process_document") as _mock_process:
        response = await async_client.post("/api/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "pdf"
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_document_unsupported_type(async_client, override_auth):
    files = {"file": ("test.txt", BytesIO(b"text"), "text/plain")}
    response = await async_client.post("/api/documents/upload", files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_documents(async_client, override_auth, mock_upload_db):
    override_db(mock_upload_db)

    mock_doc = Document(
        id=uuid.uuid4(),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=100,
        status="ready",
        created_at=datetime.now(timezone.utc),
    )

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_doc]
    mock_upload_db.execute.return_value = mock_result

    response = await async_client.get("/api/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_get_document(async_client, override_auth, mock_upload_db):
    override_db(mock_upload_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=100,
        status="ready",
        created_at=datetime.now(timezone.utc),
    )
    mock_upload_db.get.return_value = mock_doc

    response = await async_client.get(f"/api/documents/{doc_id}")

    assert response.status_code == 200
    assert response.json()["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_delete_document(async_client, override_auth, mock_upload_db):
    override_db(mock_upload_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=100,
        status="ready",
        created_at=datetime.now(timezone.utc),
    )
    mock_upload_db.get.return_value = mock_doc

    with patch("app.api.upload.os.path.exists", return_value=True):
        with patch("app.api.upload.os.unlink") as mock_unlink:
            with patch("app.api.upload.get_vector_store") as mock_get_store:
                mock_store = MagicMock()
                mock_get_store.return_value = mock_store

                response = await async_client.delete(f"/api/documents/{doc_id}")

                assert response.status_code == 200
                mock_unlink.assert_called_once_with("/tmp/test.pdf")
                mock_store.delete.assert_called_once()
                mock_upload_db.delete.assert_called_once_with(mock_doc)
