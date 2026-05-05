"""
PDF text extraction and chunking service.
"""

import os

import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF with page-level metadata.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of dicts: [{"page": 1, "text": "..."}, ...]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    doc = fitz.open(file_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()
        if text:
            pages.append({
                "page": page_num + 1,
                "text": text,
            })

    doc.close()
    return pages


def chunk_text(
    pages: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """Split page texts into overlapping chunks with metadata.

    Args:
        pages: List of page dicts from extract_text_from_pdf.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of chunk dicts: [{"text": "...", "metadata": {"page": 1, "chunk_index": 0}}, ...]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    chunk_index = 0

    for page_data in pages:
        page_chunks = splitter.split_text(page_data["text"])
        for chunk_text_content in page_chunks:
            chunks.append({
                "text": chunk_text_content,
                "metadata": {
                    "page": page_data["page"],
                    "chunk_index": chunk_index,
                    "source_type": "pdf",
                },
            })
            chunk_index += 1

    return chunks


def get_pdf_metadata(file_path: str) -> dict:
    """Extract PDF metadata (title, author, page count, etc.)."""
    doc = fitz.open(file_path)
    metadata = {
        "page_count": len(doc),
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "file_size": os.path.getsize(file_path),
    }
    doc.close()
    return metadata
