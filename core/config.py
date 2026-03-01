"""Configuration for Exam Prep OS."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = PROJECT_ROOT / "data" / "indexes"
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
EXAMS_CACHE_DIR = UPLOADS_DIR / "exams"

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# Embeddings (local model, no API calls)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
