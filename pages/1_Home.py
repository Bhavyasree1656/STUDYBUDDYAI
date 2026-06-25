"""Home page - hero, upload, stats, recent history."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from services.extractor import extract_text
from services.history import load_document
from models.gemini import generate_study_pack
from database.database import save_document, get_stats
from utils.helpers import format_date, format_file_size
from utils.constants import SUPPORTED_FORMATS, MAX_TEXT_LENGTH

_EXT_ICONS = {"pdf": "📄", "docx": "📝", "txt": "📃", "pptx": "📊"}


def _ext_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_ICONS.get(ext, "📄")


def _render_hero() -> None:
    st.markdown(
        dedent(
            """
        <div class="hero-card">
            <div class="hero-title">
                AI Powered <span class="hero-accent">Study Buddy</span>
            </div>
            <p class="hero-description">
                Upload your notes once and let AI prepare everything for you -
                summaries, explanations, quizzes, and flashcards in one click.
            </p>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_upload_section() -> None:
    st.markdown(
        '<div class="section-label">📤 &nbsp;Upload Document</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Drag & drop or click to browse - PDF, DOCX, TXT, PPTX",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    if uploaded:
        file_bytes = uploaded.read()
        icon = _ext_icon(uploaded.name)

        st.markdown(
            dedent(
                f"""
            <div class="file-preview">
                <span class="file-preview-icon">{icon}</span>
                <div class="file-preview-content">
                    <div class="file-preview-name">{uploaded.name}</div>
                    <div class="file-preview-meta">{format_file_size(uploaded.size)}</div>
                </div>
                <span class="file-preview-status">Ready</span>
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )

        if st.session_state.upload_filename != uploaded.name:
            st.session_state.upload_text = None

        if st.session_state.upload_text is None:
            with st.spinner("Extracting text from document..."):
                try:
                    text = extract_text(file_bytes, uploaded.name)
                    st.session_state.upload_text = text
                    st.session_state.upload_filename = uploaded.name
                    st.session_state.upload_size = uploaded.size
                    st.session_state.generation_done = False
                except Exception as err:
                    st.error(f"Could not extract text: {err}")
                    return

        if not st.session_state.upload_text:
            st.warning("No readable text found in this file.")
            return

        _render_generate_button()

    else:
        st.session_state.upload_text = None
        st.session_state.upload_filename = None
        st.session_state.generation_done = False


def _render_generate_button() -> None:
    if st.session_state.generation_done:
        st.markdown(
            dedent(
                """
            <div class="status-banner success">
                <div class="status-icon">✅</div>
                <div class="status-title">Study Pack Generated</div>
                <div class="status-text">
                    Use the sidebar to explore Summary, Explanation, Quiz, and Flashcards.
                </div>
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )
        return

    st.markdown("<br>", unsafe_allow_html=True)
    col, _ = st.columns([2, 3])
    with col:
        if st.button("⚡ Generate AI Study Pack", use_container_width=True):
            _run_generation()


def _run_generation() -> None:
    text = st.session_state.upload_text
    filename = st.session_state.upload_filename
    size = st.session_state.upload_size

    with st.spinner("Calling Gemini AI - this takes 15-30 seconds..."):
        try:
            result = generate_study_pack(text[:MAX_TEXT_LENGTH])
        except ValueError as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(f"Gemini API error: {e}")
            return

    doc_id = save_document(
        filename=filename,
        file_size=size,
        extracted_text=text,
        summary=result.get("summary", ""),
        explanation=result.get("explanation", ""),
        quiz=result.get("quiz", []),
        flashcards=result.get("flashcards", []),
    )

    st.session_state.current_doc_id = doc_id
    st.session_state.current_doc = load_document(doc_id)
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.card_index = 0
    st.session_state.card_flipped = False
    st.session_state.generation_done = True
    st.rerun()


def _render_stats() -> None:
    stats = get_stats()
    items = [
        ("📄", stats["documents"], "Documents\nProcessed"),
        ("🧠", stats["quizzes"], "Quizzes\nGenerated"),
        ("🃏", stats["flashcards"], "Flashcards\nCreated"),
        ("📝", stats["summaries"], "Summaries\nGenerated"),
    ]

    st.markdown('<div class="section-label">📊 &nbsp;Statistics</div>', unsafe_allow_html=True)
    cols = st.columns(4, gap="small")

    for col, (icon, value, label) in zip(cols, items):
        label_html = label.replace("\n", "<br>")
        with col:
            st.markdown(
                dedent(
                    f"""
                <div class="stat-card">
                    <div class="stat-icon">{icon}</div>
                    <div class="stat-value">{value}</div>
                    <div class="stat-label">{label_html}</div>
                </div>
                """
                ).strip(),
                unsafe_allow_html=True,
            )


_render_hero()
_render_upload_section()
st.markdown("<hr>", unsafe_allow_html=True)
_render_stats()
