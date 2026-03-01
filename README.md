# Exam Prep OS

Course-grounded exam prep helper. Upload class handouts and practice exams; we infer what each question tests and match it to concepts in your materials.

## Features

- **Handouts**: Upload lecture slides, notes, textbook excerpts. Builds a searchable index (local embeddings + FAISS).
- **Practice Exams**: Upload teacher-provided practice exams.
- **Exam Skills Map**: For each concept taught in the handouts, see which exam questions test it and which handout pages cover it.

## Setup

```bash
pip install -r requirements.txt
```

Set `MISTRAL_API_KEY` in `.env` for concept extraction and question mapping.

## Run

```bash
streamlit run scripts/run_app.py
```

1. Upload handouts → Build Index
2. Upload practice exams
3. Generate Exam Skills Map
