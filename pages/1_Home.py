
"""Learning Hub - upload documents and access study features."""

import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from services.extractor import extract_text
from services.history import load_document
from models.gemini import generate_study_pack
from database.database import save_document
from utils.helpers import format_file_size
from utils.constants import SUPPORTED_FORMATS, MAX_TEXT_LENGTH


EXT_ICONS = {
    "pdf": "📄",
    "docx": "📝",
    "txt": "📃",
    "pptx": "📊",
}


def ext_icon(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return EXT_ICONS.get(ext, "📄")


def render_header():
    st.markdown(
        dedent("""
            <div class="hero-card">
                <div class="hero-title">
                    📚 <span class="hero-accent">Learning Hub</span>
                </div>
                <p class="hero-description">
                    Upload your study material once and generate
                    summaries, explanations, quizzes, and flashcards.
                </p>
            </div>
        """).strip(),
        unsafe_allow_html=True,
    )


def render_upload_section():
    st.markdown(
        '<div class="section-label">📤 &nbsp;Upload Document</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload PDF, DOCX, TXT or PPTX",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="study_document_upload",
    )

    # A newly selected file replaces the previous active upload.
    if uploaded is not None:
        filename = uploaded.name

        if st.session_state.get("upload_filename") != filename:
            st.session_state.upload_text = None
            st.session_state.generation_done = False

        if st.session_state.get("upload_text") is None:
            with st.spinner("Extracting text from document..."):
                try:
                    text = extract_text(uploaded.getvalue(), filename)
                    st.session_state.upload_text = text
                    st.session_state.upload_filename = filename
                    st.session_state.upload_size = uploaded.size
                except Exception as err:
                    st.error(f"Could not extract text: {err}")
                    return

    # Restore the previous document display after returning to this page.
    filename = st.session_state.get("upload_filename")
    text = st.session_state.get("upload_text")

    if filename and text:
        size = st.session_state.get("upload_size", 0)

        st.markdown(
            dedent(f"""
                <div class="file-preview">
                    <span class="file-preview-icon">{ext_icon(filename)}</span>
                    <div class="file-preview-content">
                        <div class="file-preview-name">{filename}</div>
                        <div class="file-preview-meta">
                            {format_file_size(size)}
                        </div>
                    </div>
                    <span class="file-preview-status">Ready</span>
                </div>
            """).strip(),
            unsafe_allow_html=True,
        )

        if st.session_state.get("generation_done"):
            st.success("Your study pack is ready to use.")
        else:
            st.button(
                "⚡ Generate AI Study Pack",
                width="stretch",
                type="primary",
                on_click=run_generation,
            )

    elif uploaded is None:
        st.caption("Upload a document to get started.")


def run_generation():
    text = st.session_state.get("upload_text", "")
    filename = st.session_state.get("upload_filename", "")
    size = st.session_state.get("upload_size", 0)

    if not text or not filename:
        st.error("Please upload a document first.")
        return

    try:
        with st.spinner("Generating your AI study pack..."):
            result = generate_study_pack(text[:MAX_TEXT_LENGTH])

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
        st.session_state.generation_done = True

        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.card_index = 0
        st.session_state.card_flipped = False

    except Exception as err:
        st.error(f"Could not generate the study pack: {err}")


def render_study_navigation():
    if not st.session_state.get("generation_done"):
        return

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">📚 &nbsp;Your Study Pack</div>',
        unsafe_allow_html=True,
    )

    pages = [
        ("📄 Summary", "pages/3_Summary.py"),
        ("💡 Explanation", "pages/2_Explanation.py"),
        ("📝 Quiz", "pages/4_Quiz.py"),
        ("🃏 Flashcards", "pages/5_Flashcards.py"),
    ]

    columns = st.columns(4, gap="small")

    for column, (label, target) in zip(columns, pages):
        with column:
            if st.button(label, key=f"nav_{target}", width="stretch"):
                st.switch_page(target)


render_header()
render_upload_section()
render_study_navigation()
