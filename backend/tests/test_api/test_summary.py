"""
Tests for summary API endpoints.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

import pytest

from app.models.document import Document
from tests.conftest import override_db


@pytest.fixture
def mock_summary_db():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_get_summary_success(async_client, override_auth, mock_summary_db):
    override_db(mock_summary_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        status="ready",
        summary="This is a summary.",
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc

    response = await async_client.get(f"/api/documents/{doc_id}/summary")

    assert response.status_code == 200
    assert response.json()["summary"] == "This is a summary."


@pytest.mark.asyncio
async def test_get_summary_not_ready(async_client, override_auth, mock_summary_db):
    override_db(mock_summary_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc

    response = await async_client.get(f"/api/documents/{doc_id}/summary")

    assert response.status_code == 400
    assert "still processing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_regenerate_summary(async_client, override_auth, mock_summary_db):
    override_db(mock_summary_db)

    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.UUID(override_auth),
        status="ready",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        created_at=datetime.now(timezone.utc),
    )
    mock_summary_db.get.return_value = mock_doc

    # extract_text_from_pdf is imported locally inside regenerate_summary
    with patch("app.services.pdf_service.extract_text_from_pdf") as mock_extract:
        mock_extract.return_value = [{"text": "Page content"}]

        with patch("app.api.summary.summarize_text") as mock_summarize:
            mock_summarize.return_value = "New summary"

            response = await async_client.post(
                f"/api/documents/{doc_id}/summary"
            )

            assert response.status_code == 200
            assert response.json()["summary"] == "New summary"
            mock_summarize.assert_called_once()
