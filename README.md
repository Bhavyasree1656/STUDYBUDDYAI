# StudyBuddy AI

AI-powered study tool that turns your notes into summaries, explanations, quizzes, and flashcards — in a single Gemini API call.

## Features

- **Upload** PDF, DOCX, TXT, or PPTX files
- **One-click generation** — Summary · Explanation · Quiz · Flashcards
- **Interactive Quiz** with scoring and per-question explanations
- **Flashcard deck** with flip animation and progress tracking
- **History** — all documents stored in SQLite, reopened without re-calling the API
- **Dark dashboard UI** — Notion + GitHub aesthetic

## Setup

### 1. Get a free Gemini API key
Visit [Google AI Studio](https://aistudio.google.com/apikey) and create a free key.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the API key
Edit `.env`:
```
GEMINI_API_KEY=your_key_here
```

### 4. Run
```bash
streamlit run app.py
```

## Project structure

```
StudyBuddyAI/
├── app.py                  # Entry point & sidebar
├── database/
│   └── database.py         # SQLite CRUD
├── models/
│   └── gemini.py           # Single Gemini API call
├── services/
│   ├── extractor.py        # PDF/DOCX/TXT/PPTX text extraction
│   └── history.py          # History service layer
├── pages/
│   ├── 1_Home.py           # Upload & stats
│   ├── 2_Explanation.py    # AI explanation
│   ├── 3_Summary.py        # Document summary
│   ├── 4_Quiz.py           # Interactive quiz
│   ├── 5_Flashcards.py     # Flashcard deck
│   └── 6_History.py        # Document history
├── utils/
│   ├── helpers.py          # Shared UI utilities
│   └── constants.py        # App-wide constants
└── assets/
    └── style.css           # Dark theme stylesheet
```

## Deploy to Streamlit Cloud

1. Push to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set `GEMINI_API_KEY` in **Secrets** (Settings → Secrets)
4. Deploy — that's it

## Tech stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| AI | Google Gemini 2.5 Flash (`google-genai`) |
| PDF | PyMuPDF |
| DOCX | python-docx |
| PPTX | python-pptx |
| Database | SQLite (built-in) |
| Config | python-dotenv |
