"""Tests for PDF extraction."""

from core.pdf_extract import extract_text_from_pdf


def test_extract_function_exists():
    """Verify pdf_extract module and function are importable."""
    assert callable(extract_text_from_pdf)
