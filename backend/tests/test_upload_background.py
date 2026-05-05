"""
Tests for upload background processing.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.api.upload import _process_document, _get_file_type
from app.models.document import Document


class TestGetFileType:
    def test_pdf_type(self):
        assert _get_file_type("doc.pdf") == "pdf"
        assert _get_file_type("doc.PDF") == "pdf"

    def test_audio_types(self):
        assert _get_file_type("song.mp3") == "audio"
        assert _get_file_type("song.wav") == "audio"
        assert _get_file_type("song.m4a") == "audio"

    def test_video_types(self):
        assert _get_file_type("video.mp4") == "video"
        assert _get_file_type("video.mov") == "video"
        assert _get_file_type("video.webm") == "video"

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            _get_file_type("file.txt")
        with pytest.raises(ValueError, match="Unsupported file type"):
            _get_file_type("file.jpg")


@pytest.mark.asyncio
async def test_process_document_not_found():
    """Test processing when document doesn't exist."""
    mock_db = AsyncMock()
    mock_db.get.return_value = None
    
    # Create async_session mock
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    
    with patch("app.api.upload.async_session", return_value=mock_session_cm):
        # Should not raise
        await _process_document(str(uuid.uuid4()), "/tmp/test.pdf", "pdf")


@pytest.mark.asyncio
async def test_process_pdf_success():
    """Test successful PDF processing."""
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    
    mock_db = AsyncMock()
    mock_db.get.return_value = mock_doc
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()
    
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    
    with patch("app.api.upload.async_session", return_value=mock_session_cm):
        with patch("app.api.upload.extract_text_from_pdf") as mock_extract:
            with patch("app.api.upload.chunk_text") as mock_chunk:
                with patch("app.api.upload.get_pdf_metadata") as mock_meta:
                    with patch("app.api.upload.get_vector_store") as mock_get_store:
                        with patch("app.api.upload.summarize_chunks") as mock_summary:
                            mock_extract.return_value = [{"page": 1, "text": "content"}]
                            mock_chunk.return_value = [{"text": "chunk", "metadata": {"page": 1}}]
                            mock_meta.return_value = {"title": "Test"}
                            mock_store = MagicMock()
                            mock_store.build_index = AsyncMock()
                            mock_get_store.return_value = mock_store
                            mock_summary.return_value = "Summary"
                            
                            await _process_document(doc_id, "/tmp/test.pdf", "pdf")
                            
                            assert mock_doc.status == "ready"
                            assert mock_doc.summary == "Summary"
                            mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_audio_success():
    """Test successful audio processing."""
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),
        filename="test.mp3",
        file_type="audio",
        file_path="/tmp/test.mp3",
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    
    mock_db = AsyncMock()
    mock_db.get.return_value = mock_doc
    mock_db.commit = AsyncMock()
    
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    
    with patch("app.api.upload.async_session", return_value=mock_session_cm):
        with patch("app.api.upload.transcribe_media_file") as mock_transcribe:
            with patch("app.api.upload.chunk_transcript") as mock_chunk:
                with patch("app.api.upload.get_vector_store") as mock_get_store:
                    with patch("app.api.upload.summarize_chunks") as mock_summary:
                        mock_transcribe.return_value = {
                            "segments": [{"text": "Hello", "start": 0, "end": 5}],
                            "full_text": "Hello"
                        }
                        mock_chunk.return_value = [{"text": "chunk", "metadata": {"start_time": 0}}]
                        mock_store = MagicMock()
                        mock_store.build_index = AsyncMock()
                        mock_get_store.return_value = mock_store
                        mock_summary.return_value = "Audio summary"
                        
                        await _process_document(doc_id, "/tmp/test.mp3", "audio")
                        
                        assert mock_doc.status == "ready"
                        assert mock_doc.transcript is not None
                        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_document_error_handling():
    """Test error handling during processing."""
    doc_id = str(uuid.uuid4())
    mock_doc = Document(
        id=uuid.UUID(doc_id),
        user_id=uuid.uuid4(),
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        status="processing",
        created_at=datetime.now(timezone.utc),
    )
    
    mock_db = AsyncMock()
    mock_db.get.return_value = mock_doc
    mock_db.commit = AsyncMock()
    
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    
    with patch("app.api.upload.async_session", return_value=mock_session_cm):
        with patch("app.api.upload.extract_text_from_pdf", side_effect=Exception("PDF error")):
            await _process_document(doc_id, "/tmp/test.pdf", "pdf")
            
            assert mock_doc.status == "error"
            assert "PDF error" in mock_doc.error_message
            mock_db.commit.assert_called()
