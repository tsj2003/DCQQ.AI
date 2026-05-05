"""
Extended tests for utilities - covering all edge cases.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.file_utils import ensure_faiss_dir, get_file_extension
from app.utils.timestamp_utils import seconds_to_hhmmss


class TestEnsureFaissDir:
    def test_creates_faiss_directory(self):
        """Test that FAISS directory is created."""
        with patch("app.utils.file_utils.settings") as mock_settings:
            mock_settings.FAISS_INDEX_DIR = "/tmp/faiss_test"
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                ensure_faiss_dir()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGetFileExtension:
    def test_returns_lowercase_extension(self):
        """Test that file extension is returned in lowercase."""
        assert get_file_extension("file.PDF") == ".pdf"
        assert get_file_extension("file.MP3") == ".mp3"
        assert get_file_extension("file.TXT") == ".txt"

    def test_handles_no_extension(self):
        """Test file with no extension."""
        assert get_file_extension("filename") == ""

    def test_handles_multiple_dots(self):
        """Test file with multiple dots."""
        assert get_file_extension("archive.tar.gz") == ".gz"


class TestSecondsToHhmmss:
    def test_converts_seconds_to_hhmmss(self):
        """Test seconds to HH:MM:SS conversion."""
        assert seconds_to_hhmmss(0) == "00:00:00"
        assert seconds_to_hhmmss(3661) == "01:01:01"
        assert seconds_to_hhmmss(3600) == "01:00:00"
        assert seconds_to_hhmmss(7200) == "02:00:00"
        assert seconds_to_hhmmss(59) == "00:00:59"
