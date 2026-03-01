"""Pydantic models for Exam Prep OS."""

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A text chunk with source metadata."""

    text: str
    source_file: str
    page: int
    chunk_id: int = Field(description="Chunk index within the page/source")


class SearchResult(BaseModel):
    """A search result with relevance score and citation."""

    text: str
    source_file: str
    page: int
    chunk_id: int
    score: float = Field(description="Similarity score (higher = more relevant)")


class ExamQuestion(BaseModel):
    """A question parsed from a practice exam."""

    text: str
    source_file: str
    page: int
    question_id: str = Field(description="Unique ID, e.g. exam_name_q1")


class ConceptSkill(BaseModel):
    """A concept with its exam coverage and handout citations."""

    concept: str
    question_count: int
    question_ids: list[str] = Field(default_factory=list)
    citations: list[SearchResult] = Field(default_factory=list)
