"""Exam Prep OS – Course-grounded exam preparation helper."""

import io
import sys
from pathlib import Path

# Add project root so "core" can be imported
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv
load_dotenv(_project_root / ".env")

import streamlit as st

from core.chunking import chunk_pages
from core.config import EXAMS_CACHE_DIR, INDEX_DIR
from core.exam_parse import parse_exam_pdf
from core.pdf_extract import extract_text_from_pdf
from core.pdf_render import render_pdf_page
from core.pipeline import build_exam_skills_map
from core.vectorstore import VectorStore

st.set_page_config(page_title="Exam Prep OS", page_icon="📚", layout="wide")
st.title("Exam Prep OS")
st.markdown("Upload class handouts and practice exams. We infer what each question tests and match it to your materials.")

# Initialize session state
if "skills_map" not in st.session_state:
    st.session_state.skills_map = None
if "all_questions" not in st.session_state:
    st.session_state.all_questions = []
if "screenshot_for" not in st.session_state:
    st.session_state.screenshot_for = None

# --- Handouts ---
with st.container():
    st.subheader("1. Class Handouts")
    st.caption("Upload lecture slides, notes, or textbook excerpts (in lecture order).")
    handout_files = st.file_uploader(
        "Upload handouts",
        type=["pdf"],
        accept_multiple_files=True,
        key="handouts",
    )

    if handout_files and st.button("Build Handout Index"):
        store = VectorStore()
        with st.spinner("Indexing handouts..."):
            for f in handout_files:
                content = f.read()
                with io.BytesIO(content) as bio:
                    pages = extract_text_from_pdf(bio)
                chunks = chunk_pages(pages, source_file=f.name)
                store.add_chunks(chunks)
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            store.save(INDEX_DIR)
        st.success("Handout index built.")

# --- Practice Exams ---
st.divider()
with st.container():
    st.subheader("2. Practice Exams")
    st.caption("Upload practice exams from your teacher.")
    exam_files = st.file_uploader(
        "Upload practice exams",
        type=["pdf"],
        accept_multiple_files=True,
        key="exams",
    )

# --- Generate Exam Skills Map ---
st.divider()
st.subheader("3. Exam Skills Map")

if st.button("Generate Exam Skills Map"):
    if not (INDEX_DIR / "index.faiss").exists():
        st.error("Build the handout index first (step 1).")
    elif not exam_files:
        st.error("Upload at least one practice exam (step 2).")
    else:
        with st.spinner("Parsing exams and building skills map..."):
            store = VectorStore()
            store.load(INDEX_DIR)

            all_questions = []
            EXAMS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            for f in exam_files:
                content = f.read()
                # Save PDF for later screenshot viewing
                cache_path = EXAMS_CACHE_DIR / f.name
                with open(cache_path, "wb") as out:
                    out.write(content)
                with io.BytesIO(content) as bio:
                    questions = parse_exam_pdf(bio, source_name=f.name)
                all_questions.extend(questions)

            if not all_questions:
                st.warning("No questions could be extracted from the exams. Try different PDFs.")
            else:
                skills_map = build_exam_skills_map(store, all_questions, citations_per_concept=3)

                if not skills_map:
                    st.warning("Could not extract concepts from handouts.")
                else:
                    st.session_state.skills_map = [
                        {
                            "concept": s.concept,
                            "question_count": s.question_count,
                            "question_ids": s.question_ids,
                            "citations": [
                                {"text": c.text, "source_file": c.source_file, "page": c.page}
                                for c in s.citations
                            ],
                        }
                        for s in skills_map
                    ]
                    st.session_state.all_questions = all_questions
                    st.success(f"Mapped {len(all_questions)} questions to {len(skills_map)} concepts.")
                    st.rerun()

# --- Screenshot viewer (dismiss) ---
if st.session_state.screenshot_for:
    source_file, page = st.session_state.screenshot_for
    st.divider()
    with st.container():
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Close preview"):
                st.session_state.screenshot_for = None
                st.rerun()
        with col2:
            st.caption(f"**{source_file}** — Page {page}")

    cache_path = EXAMS_CACHE_DIR / source_file
    if cache_path.exists():
        try:
            img_bytes = render_pdf_page(cache_path, page, dpi=120)
            st.image(img_bytes, use_container_width=False)
        except Exception as e:
            st.error(f"Could not render page: {e}")
    else:
        st.warning("Original exam file no longer available. Re-upload and regenerate.")
    st.divider()

# --- Display Skills Map ---
if st.session_state.skills_map:
    q_by_id = {q["question_id"]: q for q in st.session_state.all_questions}

    for skill_idx, skill in enumerate(st.session_state.skills_map):
        with st.expander(
            f"**{skill['concept']}** — {skill['question_count']} exam question(s)",
            expanded=skill["question_count"] > 0,
        ):
            if skill["question_ids"]:
                st.markdown("**Tested by:**")
                for q_idx, qid in enumerate(skill["question_ids"]):
                    q = q_by_id.get(qid, {})
                    text = q.get("text", "")[:250] + ("..." if len(q.get("text", "")) > 250 else "")
                    source = q.get("source_file", "")
                    page = q.get("page", 1)
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**{qid}** — *{source}* p.{page}")
                        st.caption(text)
                    with col_b:
                        if st.button("📄 View page", key=f"view_{skill_idx}_{q_idx}_{qid}", type="primary"):
                            st.session_state.screenshot_for = (source, page)
                            st.rerun()
            if skill["citations"]:
                st.markdown("**Relevant handouts:**")
                for c in skill["citations"]:
                    st.markdown(f"- *{c['source_file']}* p.{c['page']}")
                    st.text(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""))
                st.markdown("")

# --- Search ---
st.divider()
with st.expander("Search Handouts", expanded=False):
    query = st.text_input("Search your handouts", key="search")
    if query and (INDEX_DIR / "index.faiss").exists():
        store = VectorStore()
        store.load(INDEX_DIR)
        results = store.search(query, k=5)
        for r in results:
            st.markdown(f"**{r.source_file}** (p. {r.page})")
            st.text(r.text[:400] + ("..." if len(r.text) > 400 else ""))
            st.markdown("---")
