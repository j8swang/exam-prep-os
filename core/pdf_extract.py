"""PDF text extraction using pdfplumber."""

from pathlib import Path
from typing import BinaryIO

import pdfplumber


def extract_text_from_pdf(path: str | Path | BinaryIO) -> list[dict]:
    """
    Extract text from a PDF file, one dict per page.

    Args:
        path: File path or file-like object (e.g. BytesIO from uploads)

    Returns:
        List of dicts with keys: page (1-based), text (str)
    """
    pages: list[dict] = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            pages.append({"page": i + 1, "text": text or ""})

    return pages
