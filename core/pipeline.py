"""Pipeline: handouts + practice exams → Exam Skills Map."""

from core.concepts import extract_concepts_from_handouts, map_question_to_concepts
from core.models import ConceptSkill, SearchResult
from core.vectorstore import VectorStore


def build_exam_skills_map(
    vectorstore: VectorStore,
    exam_questions: list[dict],
    citations_per_concept: int = 3,
) -> list[ConceptSkill]:
    """
    Build the Exam Skills Map: concepts in lecture order, with question counts and citations.

    Args:
        vectorstore: FAISS index over handouts (must be loaded with handout chunks)
        exam_questions: Parsed questions from practice exams (each with text, source_file, page, question_id)
        citations_per_concept: How many RAG citations to include per concept

    Returns:
        List of ConceptSkill in concept order
    """
    handout_chunks = vectorstore.chunks
    # Sample chunks for concept extraction (avoid token overflow)
    sample_size = min(50, len(handout_chunks))
    step = max(1, len(handout_chunks) // sample_size) if handout_chunks else 1
    sample_texts = [c.text for c in handout_chunks[::step][:sample_size]]

    concepts = extract_concepts_from_handouts(sample_texts)
    if not concepts:
        return []

    # Map each question to concepts
    concept_to_questions: dict[str, list[str]] = {c: [] for c in concepts}
    for i, q in enumerate(exam_questions):
        qid = q.get("question_id", f"q{i+1}")
        mapped = map_question_to_concepts(q["text"], concepts, max_concepts=3)
        for c in mapped:
            if c in concept_to_questions:
                concept_to_questions[c].append(qid)

    # For each concept: get RAG citations from handouts
    skills: list[ConceptSkill] = []
    for concept in concepts:
        citations: list[SearchResult] = []
        if vectorstore.index is not None and vectorstore.chunks:
            results = vectorstore.search(concept, k=citations_per_concept)
            citations = results

        skills.append(
            ConceptSkill(
                concept=concept,
                question_count=len(concept_to_questions[concept]),
                question_ids=concept_to_questions[concept],
                citations=citations,
            )
        )

    return skills
