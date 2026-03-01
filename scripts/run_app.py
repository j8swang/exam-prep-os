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
from core.config import EXAMS_CACHE_DIR, HANDOUTS_CACHE_DIR, INDEX_DIR
from core.exam_parse import parse_exam_pdf
from core.pdf_extract import extract_text_from_pdf
from core.pdf_render import render_pdf_page
from core.pipeline import build_exam_skills_map
from core.vectorstore import VectorStore

st.set_page_config(page_title="Exam Prep OS", page_icon="📚", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    :root {
        --sage: #0f766e;
        --sage-light: #14b8a6;
        --cream: #faf9f6;
        --warm-white: #fffefb;
        --ink: #1c1917;
        --slate: #475569;
        --border: #e7e5e4;
    }
    
    .stApp { font-family: 'DM Sans', system-ui, sans-serif; background: var(--cream) !important; }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #faf9f6 0%, #f5f4f0 100%) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.25rem !important;
        box-shadow: 0 2px 8px rgba(15, 118, 110, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.4) !important;
    }
    
    .stButton > button:not([kind="primary"]) {
        background: var(--warm-white) !important;
        color: var(--slate) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    
    h1 { color: var(--ink) !important; font-weight: 700 !important; }
    h2, h3 { color: #292524 !important; font-weight: 600 !important; }
    .stCaption, p { color: var(--slate) !important; }
    
    [data-testid="stFileUploader"] {
        background: var(--warm-white) !important;
        border: 1px dashed var(--border) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--sage-light) !important;
        background: #f0fdfa !important;
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "skills_map" not in st.session_state:
    st.session_state.skills_map = None
if "all_questions" not in st.session_state:
    st.session_state.all_questions = []
if "exam_display_names" not in st.session_state:
    st.session_state.exam_display_names = {}
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None

def _show_page_image(cache_dir: Path, source_file: str, page: int, caption: str = ""):
    path = cache_dir / source_file
    if path.exists():
        try:
            img_bytes = render_pdf_page(path, page, dpi=120)
            st.image(img_bytes, caption=caption, use_container_width=True)
        except Exception:
            st.caption(f"Could not render {source_file} p.{page}")
    else:
        st.caption(f"File not found: {source_file}. Re-upload and rebuild.")

# --- Home Page ---
if st.session_state.page == "home":
    st.markdown("# Exam Prep OS")
    st.markdown("Upload your class handouts and practice exams. We'll build a concept map that connects exam questions to your course materials.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📂 Class Handouts")
        st.caption("Lecture slides, notes, or textbook excerpts (in lecture order)")
        handout_files = st.file_uploader("Upload handouts", type=["pdf"], accept_multiple_files=True, key="handouts")

    with col2:
        st.markdown("### 📝 Practice Exams")
        st.caption("Teacher-provided practice tests")
        exam_files = st.file_uploader("Upload practice exams", type=["pdf"], accept_multiple_files=True, key="exams")

    st.markdown("---")
    st.markdown("### Next Step")
    if st.session_state.skills_map:
        if st.button("View Exam Concept Map", type="primary"):
            st.session_state.page = "concept_map"
            st.rerun()
        st.caption("Upload new files below to rebuild.")
    if st.button("Build Index and Generate Concept Map"):
        if not handout_files:
            st.error("Upload class handouts first.")
        elif not exam_files:
            st.error("Upload at least one practice exam.")
        else:
            with st.spinner("Building index and generating concept map..."):
                # Build handout index
                store = VectorStore()
                HANDOUTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                for f in handout_files:
                    content = f.read()
                    cache_path = HANDOUTS_CACHE_DIR / f.name
                    with open(cache_path, "wb") as out:
                        out.write(content)
                    with io.BytesIO(content) as bio:
                        pages = extract_text_from_pdf(bio)
                    chunks = chunk_pages(pages, source_file=f.name)
                    store.add_chunks(chunks)
                INDEX_DIR.mkdir(parents=True, exist_ok=True)
                store.save(INDEX_DIR)

                # Parse exams and build skills map
                all_questions = []
                exam_display_names = {}
                EXAMS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                for idx, f in enumerate(exam_files):
                    display_name = f"Practice Test {idx + 1}"
                    cache_filename = f"Practice Test {idx + 1}.pdf"
                    content = f.read()
                    cache_path = EXAMS_CACHE_DIR / cache_filename
                    with open(cache_path, "wb") as out:
                        out.write(content)
                    with io.BytesIO(content) as bio:
                        questions = parse_exam_pdf(bio, source_name=cache_filename)
                    for q in questions:
                        exam_display_names[q["question_id"]] = display_name
                    all_questions.extend(questions)

                if not all_questions:
                    st.warning("No questions extracted. Try different PDFs.")
                else:
                    store = VectorStore()
                    store.load(INDEX_DIR)
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
                        st.session_state.exam_display_names = exam_display_names
                        st.session_state.page = "concept_map"
                        st.rerun()

    st.divider()
    with st.expander("Search Handouts (after building index)"):
        query = st.text_input("Search", key="search")
        if query and (INDEX_DIR / "index.faiss").exists():
            store = VectorStore()
            store.load(INDEX_DIR)
            for r in store.search(query, k=5):
                st.markdown(f"**{r.source_file}** p.{r.page}")
                st.caption(r.text[:200] + "...")

# --- Exam Concept Map Page ---
elif st.session_state.page == "concept_map":
    skills_map = st.session_state.skills_map
    all_questions = st.session_state.all_questions
    q_by_id = {q["question_id"]: q for q in all_questions}
    display_names = st.session_state.exam_display_names

    # Filter: only concepts with practice problems
    skills_with_problems = [s for s in skills_map if s["question_count"] > 0]
    qid_to_concepts: dict[str, list[str]] = {}
    for skill in skills_map:
        for qid in skill["question_ids"]:
            qid_to_concepts.setdefault(qid, []).append(skill["concept"])
    concept_to_citations = {s["concept"]: s["citations"] for s in skills_map}

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.session_state.selected_item = None
        st.rerun()

    st.markdown("# Exam Concept Map")
    view_mode = st.radio(
        "View",
        ["By Problem (Chronological)", "By Concept (Lecture Order)"],
        key="view_mode",
        horizontal=True,
    )

    # Build list items for left menu
    if view_mode == "By Problem (Chronological)":
        list_items = []
        for q in all_questions:
            display = display_names.get(q["question_id"], q.get("source_file", "?"))
            qnum = q["question_id"].split("_q")[-1] if "_q" in q["question_id"] else "?"
            list_items.append((f"{display} — Q{qnum}", "problem", q))
    else:
        list_items = []
        for skill in skills_with_problems:
            list_items.append((f"{skill['concept']} ({skill['question_count']})", "concept", skill))

    if not list_items:
        st.info("No items to display.")
    else:
        list_labels = [x[0] for x in list_items]
        col_left, col_right = st.columns([1, 3])

        with col_left:
            st.markdown("**Select**")
            selected_label = st.radio(
                "Items",
                list_labels,
                key="concept_map_select",
                label_visibility="collapsed",
            )

        with col_right:
            if selected_label:
                idx = list_labels.index(selected_label)
                _, item_type, item_data = list_items[idx]

                if item_type == "problem":
                    q = item_data
                    qid = q["question_id"]
                    concepts = qid_to_concepts.get(qid, [])
                    page = q.get("page", 1)
                    st.markdown(f"**{selected_label}**")
                    st.markdown("**Concept(s):** " + (", ".join(concepts) if concepts else "—"))
                    st.markdown("---")
                    st.markdown("**Problem (from exam):**")
                    _show_page_image(EXAMS_CACHE_DIR, q["source_file"], page, f"p.{page}")
                    seen = set()
                    citation_list = []
                    for c in concepts:
                        for cit in concept_to_citations.get(c, []):
                            key = (cit["source_file"], cit["page"])
                            if key not in seen:
                                seen.add(key)
                                citation_list.append(cit)
                    if citation_list:
                        st.markdown("**Relevant handouts:**")
                        for cit in citation_list:
                            st.markdown(f"*{cit['source_file']}* — p.{cit['page']}")
                            _show_page_image(HANDOUTS_CACHE_DIR, cit["source_file"], cit["page"], "")

                else:
                    skill = item_data
                    st.markdown(f"**{skill['concept']}**")
                    st.markdown(f"*{skill['question_count']} practice problem(s)*")
                    st.markdown("---")
                    if skill["question_ids"]:
                        st.markdown("**Tested by:**")
                        for qid in skill["question_ids"]:
                            q = q_by_id.get(qid, {})
                            display = display_names.get(qid, qid)
                            page = q.get("page", 1)
                            st.markdown(f"**{display}**")
                            _show_page_image(EXAMS_CACHE_DIR, q["source_file"], page, f"p.{page}")
                    if skill["citations"]:
                        st.markdown("**Relevant handouts:**")
                        for c in skill["citations"]:
                            st.markdown(f"*{c['source_file']}* — p.{c['page']}")
                            _show_page_image(HANDOUTS_CACHE_DIR, c["source_file"], c["page"], "")
