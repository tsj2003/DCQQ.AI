"""
File utility functions.
"""

from pathlib import Path

from app.config import get_settings

settings = get_settings()


def ensure_upload_dir():
    """Create upload directory if it doesn't exist."""
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def ensure_faiss_dir():
    """Create FAISS index directory if it doesn't exist."""
    Path(settings.FAISS_INDEX_DIR).mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return Path(filename).suffix.lower()


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
