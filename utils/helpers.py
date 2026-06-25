import streamlit as st
from pathlib import Path
from datetime import datetime
from textwrap import dedent


def load_css() -> None:
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def init_session_state() -> None:
    defaults = {
        # Document state
        "current_doc_id":  None,
        "current_doc":     None,
        # Upload state
        "upload_text":     None,
        "upload_filename": None,
        "upload_size":     0,
        "processing":      False,
        "generation_done": False,
        # Quiz — all-at-once (legacy, kept for compat)
        "quiz_answers":    {},
        "quiz_submitted":  False,
        "quiz_score":      0,
        # Quiz — one at a time
        "quiz_doc_id":     None,
        "quiz_current_q":  0,
        "quiz_revealed":   False,   # unused in new flow (per-Q via quiz_scores)
        "quiz_scores":     {},      # {question_index: bool}
        "quiz_finished":   False,
        # Flashcards
        "card_index":      0,
        "card_flipped":    False,
        "fc_doc_id":       None,
        "fc_order":        None,    # list[int] — shuffled indices
        "fc_shuffled":     False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        return iso_str or "—"


def format_file_size(size_bytes: int) -> str:
    if not size_bytes:
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 ** 2):.1f} MB"


def no_document_warning() -> None:
    st.markdown(
        dedent(
            """
        <div class="empty-state">
            <div class="empty-icon">📂</div>
            <h3>No document selected</h3>
            <p>Go to <strong>Home</strong> to upload a file and generate your study pack,
            or open a document from <strong>History</strong>.</p>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    sub_html = f"<p class='page-subtitle'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        dedent(
            f"""
        <div class="page-header">
            <h1 class="page-title">{title}</h1>
            {sub_html}
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "accent") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'
