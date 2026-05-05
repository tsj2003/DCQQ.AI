"""
Edge case tests for utilities.
"""

import pytest
from unittest.mock import patch

from app.utils.file_utils import human_readable_size, ensure_faiss_dir
from app.utils.timestamp_utils import mmss_to_seconds


class TestHumanReadableSize:
    def test_tb_size(self):
        """Test terabyte conversion."""
        # 1.5 TB = 1.5 * 1024^4 bytes
        tb_size = int(1.5 * 1024 ** 4)
        result = human_readable_size(tb_size)
        assert "TB" in result

    def test_exact_gb_boundary(self):
        """Test exact GB boundary."""
        result = human_readable_size(1024 ** 3)
        assert result == "1.0 GB"


class TestEnsureFaissDir:
    def test_creates_faiss_dir(self):
        """Test FAISS directory creation."""
        with patch("app.utils.file_utils.settings") as mock_settings:
            mock_settings.FAISS_INDEX_DIR = "/tmp/faiss_test_dir"
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                ensure_faiss_dir()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestMmsstoSeconds:
    def test_hhmmss_format(self):
        """Test HH:MM:SS format parsing."""
        result = mmss_to_seconds("01:30:45")
        assert result == 5445  # 1*3600 + 30*60 + 45

    def test_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            mmss_to_seconds("invalid")

    def test_single_part_raises(self):
        """Test single part raises ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            mmss_to_seconds("30")

    def test_empty_string_raises(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError):
            mmss_to_seconds("")
