"""
Tests for file utilities.
"""

from unittest.mock import patch
from app.utils.file_utils import ensure_upload_dir, human_readable_size


def test_ensure_upload_dir(tmp_path):
    """ensure_upload_dir should create the configured upload directory."""
    upload_dir = str(tmp_path / "uploads")

    with patch("app.utils.file_utils.settings") as mock_settings:
        mock_settings.UPLOAD_DIR = upload_dir
        ensure_upload_dir()

    import os
    assert os.path.exists(upload_dir)

    # Calling again should not fail
    with patch("app.utils.file_utils.settings") as mock_settings:
        mock_settings.UPLOAD_DIR = upload_dir
        ensure_upload_dir()

    assert os.path.exists(upload_dir)


def test_human_readable_size():
    assert human_readable_size(500) == "500.0 B"
    assert human_readable_size(1024) == "1.0 KB"
    assert human_readable_size(1536) == "1.5 KB"
    assert human_readable_size(1048576) == "1.0 MB"
    assert human_readable_size(1073741824) == "1.0 GB"
