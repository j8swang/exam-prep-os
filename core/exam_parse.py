"""Parse practice exam PDFs into individual questions."""

import json
import re
from pathlib import Path
from typing import BinaryIO

from core.mistral_client import chat
from core.pdf_extract import extract_text_from_pdf


def _extract_questions_via_mistral(full_text: str, source_name: str) -> list[dict]:
    """Use Mistral to extract questions from exam text."""
    system = """You are an expert at parsing exam documents. Extract each distinct question or problem.
Return a JSON array of objects, each with: "text" (the question text, trimmed), "page" (approximate page if obvious, else 1).
Numbering like "1.", "Q1", "Problem 1" starts a new question. Combine multi-part sub-questions (a, b, c) into one question.
Keep question text concise but complete. If the document has no clear questions, return []."""

    # Truncate if very long to stay under token limits
    max_chars = 30000
    text = full_text[:max_chars] + ("..." if len(full_text) > max_chars else "")

    prompt = f"""Extract all exam questions from this document (source: {source_name}):

---
{text}
---

Return only valid JSON array, no markdown or explanation."""

    try:
        response = chat(prompt, system=system)
        # Strip markdown code block if present
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```\s*$", "", response)
        items = json.loads(response)
        if not isinstance(items, list):
            return []
        return [{"text": str(x.get("text", "")).strip(), "page": int(x.get("page", 1))} for x in items if x.get("text")]
    except (json.JSONDecodeError, ValueError):
        return _extract_questions_heuristic(full_text)


def _extract_questions_heuristic(text: str) -> list[dict]:
    """Fallback: split by common question patterns."""
    # Patterns: "1.", "Q1", "Question 1", "Problem 1"
    pattern = re.compile(r"(?:\n\s*|\A)(?:Question\s*)?(?:Q\.?\s*)?(\d+)[.)]\s*", re.IGNORECASE)
    parts = pattern.split(text)
    questions = []
    for i in range(1, len(parts)):
        if i % 2 == 1:
            # This is a number; next part is question text
            if i + 1 < len(parts):
                qtext = parts[i + 1].strip()
                # Stop at next major number or end
                next_num = re.search(r"\n\s*(?:\d+[.)]|Q\.?\s*\d+)", qtext)
                if next_num:
                    qtext = qtext[: next_num.start()].strip()
                if len(qtext) > 20:
                    questions.append({"text": qtext[:2000], "page": 1})
    if not questions:
        # Last resort: treat each paragraph as potential question
        blocks = re.split(r"\n\s*\n", text)
        for b in blocks:
            b = b.strip()
            if len(b) > 30 and len(b) < 1500:
                questions.append({"text": b, "page": 1})
    return questions


def parse_exam_pdf(
    path: str | Path | BinaryIO,
    source_name: str = "exam",
) -> list[dict]:
    """
    Parse a practice exam PDF into question candidates.

    Returns:
        List of dicts with keys: text, page, source_file
    """
    pages = extract_text_from_pdf(path)
    full_text = "\n\n".join(f"--- Page {p['page']} ---\n{p['text']}" for p in pages)

    if not full_text.strip():
        return []

    questions = _extract_questions_via_mistral(full_text, source_name)

    for i, q in enumerate(questions):
        q["source_file"] = source_name
        q["question_id"] = f"{source_name}_q{i+1}"

    return questions
