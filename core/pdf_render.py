"""Render PDF pages to images for display."""

import io
from pathlib import Path
from typing import BinaryIO

import fitz  # PyMuPDF


def render_pdf_page(
    path_or_bytes: str | Path | BinaryIO | bytes,
    page_num: int,
    dpi: int = 150,
) -> bytes:
    """
    Render a single PDF page to PNG bytes.

    Args:
        path_or_bytes: File path or file-like object or raw bytes
        page_num: 1-based page number
        dpi: Resolution for rendering

    Returns:
        PNG image bytes
    """
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    if isinstance(path_or_bytes, bytes):
        doc = fitz.open(stream=path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(path_or_bytes)

    try:
        page = doc[page_num - 1]  # 0-based index
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()
