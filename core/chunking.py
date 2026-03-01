"""Text chunking with configurable size and overlap."""

from core.config import CHUNK_OVERLAP, CHUNK_SIZE
from core.models import Chunk


def chunk_pages(
    pages: list[dict],
    source_file: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    Split pages into overlapping chunks.

    Args:
        pages: List of dicts with keys page (int), text (str)
        source_file: Name of the source file for citation
        chunk_size: Max characters per chunk
        chunk_overlap: Overlap between consecutive chunks

    Returns:
        List of Chunk objects with text, source_file, page, chunk_id
    """
    chunks: list[Chunk] = []
    chunk_id = 0

    for page_dict in pages:
        page_num = page_dict["page"]
        text = page_dict.get("text", "").strip()

        if not text:
            continue

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        source_file=source_file,
                        page=page_num,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

            start = end - chunk_overlap
            if start >= len(text):
                break

    return chunks
