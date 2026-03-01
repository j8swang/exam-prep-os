"""FAISS vector store with metadata persistence."""

import json
from pathlib import Path

import faiss
import numpy as np

from core.embedder import Embedder
from core.models import Chunk, SearchResult


class VectorStore:
    """FAISS index with chunk metadata for search and citation."""

    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or Embedder()
        self.index: faiss.IndexFlatL2 | None = None
        self.chunks: list[Chunk] = []

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Embed chunks and add to the FAISS index."""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        vectors = self.embedder.embed(texts).astype(np.float32)

        if self.index is None:
            dim = vectors.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        """Search for similar chunks. Returns top-k results with scores."""
        if self.index is None or not self.chunks:
            return []

        query_vec = self.embedder.embed([query]).astype(np.float32)
        scores, indices = self.index.search(query_vec, min(k, len(self.chunks)))

        results: list[SearchResult] = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            # L2 distance: lower = more similar; negate for "score" (higher = better)
            score = float(-scores[0][i])
            results.append(
                SearchResult(
                    text=chunk.text,
                    source_file=chunk.source_file,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    score=score,
                )
            )
        return results

    def save(self, path: str | Path) -> None:
        """Persist index and metadata to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if self.index is not None:
            faiss.write_index(self.index, str(path / "index.faiss"))

        meta = [c.model_dump() for c in self.chunks]
        with open(path / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, path: str | Path) -> None:
        """Load index and metadata from disk."""
        path = Path(path)
        index_file = path / "index.faiss"
        meta_file = path / "metadata.json"

        if index_file.exists():
            self.index = faiss.read_index(str(index_file))

        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            self.chunks = [Chunk(**m) for m in meta]
        else:
            self.chunks = []
