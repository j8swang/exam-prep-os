"""Concept extraction and question-to-concept mapping via Mistral."""

import json
import re

from core.mistral_client import chat


def extract_concepts_from_handouts(chunk_texts: list[str]) -> list[str]:
    """
    Extract an ordered list of concepts taught in the handouts.

    Args:
        chunk_texts: Representative text chunks from handouts (e.g. first N chars of each chunk, or sampled)

    Returns:
        Ordered list of concept names (as taught in lecture order)
    """
    # Concatenate with separators, truncate if needed
    combined = "\n\n---\n\n".join(chunk_texts)
    max_chars = 25000
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[content truncated]"

    system = """You are an expert educator. Given course material, extract the main concepts/skills taught, in the order they appear (lecture order).
Return a JSON array of strings, e.g. ["Concept 1", "Concept 2"]. Use clear, concise names (3-8 words each).
Include only concepts that are explicitly taught. Return [] if no clear concepts."""

    prompt = f"""Extract the ordered list of concepts from this course material:

---
{combined}
---

Return only a valid JSON array of strings, no other text."""

    try:
        response = chat(prompt, system=system)
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```\s*$", "", response)
        concepts = json.loads(response)
        if isinstance(concepts, list):
            return [str(c).strip() for c in concepts if c]
        return []
    except (json.JSONDecodeError, ValueError):
        return []


def map_question_to_concepts(
    question_text: str,
    concept_list: list[str],
    max_concepts: int = 3,
) -> list[str]:
    """
    Map an exam question to 1-3 relevant concepts from the list.

    Args:
        question_text: The exam question
        concept_list: Ordered list of concept names
        max_concepts: Max concepts to return per question

    Returns:
        List of concept names (subset of concept_list) that this question tests
    """
    if not concept_list:
        return []

    concepts_str = "\n".join(f"{i+1}. {c}" for i, c in enumerate(concept_list))

    system = """You are an expert at mapping exam questions to course concepts.
Given a question and a list of concepts, identify which concept(s) the question is testing.
Return a JSON array of the exact concept names from the list (1-3 concepts). Use only names that appear in the list."""

    prompt = f"""Question:
{question_text[:1500]}

Concepts (choose from these exactly):
{concepts_str}

Which concepts does this question test? Return only a JSON array of concept names, e.g. ["Concept A", "Concept B"]."""

    try:
        response = chat(prompt, system=system)
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```\s*$", "", response)
        mapped = json.loads(response)
        if isinstance(mapped, list):
            # Filter to only concepts that exist in concept_list
            valid = {c.strip() for c in concept_list}
            return [m for m in mapped if str(m).strip() in valid][:max_concepts]
        return []
    except (json.JSONDecodeError, ValueError):
        return []
