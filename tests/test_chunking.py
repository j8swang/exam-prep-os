"""Tests for chunking module."""

import pytest

from core.chunking import chunk_pages
from core.models import Chunk


def test_chunk_pages_basic():
    pages = [{"page": 1, "text": "Hello world. Short chunk."}]
    chunks = chunk_pages(pages, "test.pdf", chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 1
    assert chunks[0].source_file == "test.pdf"
    assert chunks[0].page == 1
    assert "Hello" in chunks[0].text


def test_chunk_pages_empty():
    chunks = chunk_pages([], "test.pdf")
    assert chunks == []


def test_chunk_pages_skip_empty_text():
    pages = [{"page": 1, "text": ""}, {"page": 2, "text": "  "}]
    chunks = chunk_pages(pages, "test.pdf")
    assert chunks == []
