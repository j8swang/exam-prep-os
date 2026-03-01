"""Local embedding model (sentence-transformers)."""

import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import EMBEDDING_MODEL


class Embedder:
    """Local embedder using sentence-transformers. No API calls."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts into vectors."""
        if not texts:
            return np.array([]).reshape(0, self.model.get_sentence_embedding_dimension())
        return self.model.encode(texts, convert_to_numpy=True)
