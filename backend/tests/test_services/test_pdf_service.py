"""
Tests for PDF service.
"""

from unittest.mock import patch, MagicMock

import pytest
from app.services.pdf_service import (
    chunk_text,
    get_pdf_metadata,
    extract_text_from_pdf,
)


class TestChunkText:
    def test_chunks_text_correctly(self, sample_pdf_pages):
        chunks = chunk_text(sample_pdf_pages, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert "page" in chunk["metadata"]
            assert "source_type" in chunk["metadata"]
            assert chunk["metadata"]["source_type"] == "pdf"

    def test_empty_pages_returns_empty(self):
        chunks = chunk_text([])
        assert chunks == []

    def test_preserves_page_numbers(self, sample_pdf_pages):
        chunks = chunk_text(sample_pdf_pages, chunk_size=500, chunk_overlap=0)
        pages_found = {c["metadata"]["page"] for c in chunks}
        assert 1 in pages_found
        assert 2 in pages_found

    def test_chunk_index_increments(self, sample_pdf_pages):
        chunks = chunk_text(sample_pdf_pages, chunk_size=100, chunk_overlap=10)
        indices = [c["metadata"]["chunk_index"] for c in chunks]
        assert indices == list(range(len(indices)))


class TestExtractTextFromPdf:
    def test_extracts_text_from_pdf(self):
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Extracted text from page"

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)
        mock_doc.load_page = MagicMock(side_effect=[mock_page, mock_page])
        mock_doc.metadata = {"title": "Test PDF"}
        mock_doc.close = MagicMock()

        with patch("app.services.pdf_service.fitz.open", return_value=mock_doc):
            with patch("os.path.exists", return_value=True):
                result = extract_text_from_pdf("/tmp/test.pdf")

        assert len(result) == 2
        assert result[0]["text"] == "Extracted text from page"
        assert result[0]["page"] == 1

    def test_handles_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="PDF file not found"):
                extract_text_from_pdf("/tmp/nonexistent.pdf")

    def test_handles_pdf_open_error(self):
        with patch("os.path.exists", return_value=True):
            with patch("app.services.pdf_service.fitz.open", side_effect=RuntimeError("Cannot open PDF")):
                with pytest.raises(RuntimeError, match="Cannot open PDF"):
                    extract_text_from_pdf("/tmp/invalid.pdf")


class TestGetPdfMetadata:
    def test_extracts_metadata(self):
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "subject": "Test Subject",
        }
        mock_doc.__len__ = MagicMock(return_value=10)
        mock_doc.close = MagicMock()

        with patch("app.services.pdf_service.fitz.open", return_value=mock_doc):
            with patch("os.path.getsize", return_value=1024):
                result = get_pdf_metadata("/tmp/test.pdf")

        assert result["title"] == "Test Document"
        assert result["author"] == "Test Author"
        assert result["page_count"] == 10
        assert result["file_size"] == 1024

    def test_skips_empty_metadata_fields(self):
        mock_doc = MagicMock()
        mock_doc.metadata = {}  # Empty metadata
        mock_doc.__len__ = MagicMock(return_value=5)
        mock_doc.close = MagicMock()

        with patch("app.services.pdf_service.fitz.open", return_value=mock_doc):
            with patch("os.path.getsize", return_value=2048):
                result = get_pdf_metadata("/tmp/test.pdf")

        assert result["title"] == ""
        assert result["author"] == ""
        assert result["page_count"] == 5
        assert result["file_size"] == 2048
