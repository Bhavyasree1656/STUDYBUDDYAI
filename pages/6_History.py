"""History page - search, sort, open, delete. Reads only from SQLite."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from services.history import get_history, load_document, remove_document, record_opened
from utils.helpers import page_header, format_date, format_file_size

_EXT_ICONS = {"pdf": "📄", "docx": "📝", "txt": "📃", "pptx": "📊"}


def _ext_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_ICONS.get(ext, "📄")


def _open_document(doc_id: str) -> None:
    record_opened(doc_id)
    doc = load_document(doc_id)
    if doc:
        st.session_state.current_doc_id = doc_id
        st.session_state.current_doc = doc
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.quiz_doc_id = None
        st.session_state.fc_doc_id = None
        st.session_state.card_index = 0
        st.session_state.card_flipped = False
        st.switch_page("pages/3_Summary.py")


def _confirm_delete(doc_id: str, filename: str) -> None:
    key = f"confirm_delete_{doc_id}"
    if key not in st.session_state:
        st.session_state[key] = False

    if not st.session_state[key]:
        if st.button("🗑", key=f"del_{doc_id}", use_container_width=True):
            st.session_state[key] = True
            st.rerun()
    else:
        st.markdown('<div class="history-delete-confirm">Delete?</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", key=f"yes_{doc_id}", use_container_width=True):
                if st.session_state.get("current_doc_id") == doc_id:
                    st.session_state.current_doc_id = None
                    st.session_state.current_doc = None
                remove_document(doc_id)
                del st.session_state[key]
                st.rerun()
        with c2:
            if st.button("No", key=f"no_{doc_id}", use_container_width=True):
                st.session_state[key] = False
                st.rerun()


def _document_row_html(doc: dict, is_active: bool) -> str:
    active_class = "doc-row is-active" if is_active else "doc-row"
    active_badge = '<span class="status-badge status-badge-active">Active</span>' if is_active else ""
    opened = doc.get("opened_count", 0)
    opens_text = f"&nbsp;·&nbsp; 👁 Opened {opened}×" if opened else ""

    return dedent(
        f"""
    <div class="{active_class}">
        <span class="doc-row-icon">{_ext_icon(doc["filename"])}</span>
        <div class="doc-row-content">
            <div class="doc-row-title">{doc["filename"]}{active_badge}</div>
            <div class="doc-row-meta">
                📅 {format_date(doc["created_at"])}
                &nbsp;·&nbsp; 💾 {format_file_size(doc["file_size"])}
                {opens_text}
            </div>
        </div>
    </div>
    """
    ).strip()


def _render_document_row(doc: dict) -> None:
    doc_id = doc["id"]
    is_active = doc_id == st.session_state.get("current_doc_id")

    c_card, c_open, c_del = st.columns([6, 1, 1], gap="small")
    with c_card:
        st.markdown(_document_row_html(doc, is_active), unsafe_allow_html=True)
    with c_open:
        st.write("")
        if st.button("Open", key=f"open_{doc_id}", use_container_width=True):
            _open_document(doc_id)
    with c_del:
        st.write("")
        _confirm_delete(doc_id, doc["filename"])


def _render_history() -> None:
    page_header("📚  History", "All documents you have processed")

    all_docs = get_history()
    if not all_docs:
        st.markdown(
            dedent(
                """
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No documents yet</h3>
                <p>Go to <strong>Home</strong>, upload a file, and generate your first study pack.</p>
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )
        return

    col_search, col_sort = st.columns([3, 1], gap="small")
    with col_search:
        search = st.text_input(
            "search",
            placeholder="🔍  Search by filename...",
            label_visibility="collapsed",
        )
    with col_sort:
        sort_by = st.selectbox(
            "sort",
            ["Newest first", "Oldest first", "Name A → Z", "Name Z → A", "Most opened"],
            label_visibility="collapsed",
        )

    filtered = [d for d in all_docs if search.lower() in d["filename"].lower()] if search else list(all_docs)

    if sort_by == "Oldest first":
        filtered = sorted(filtered, key=lambda d: d.get("upload_time", ""))
    elif sort_by == "Name A → Z":
        filtered = sorted(filtered, key=lambda d: d["filename"].lower())
    elif sort_by == "Name Z → A":
        filtered = sorted(filtered, key=lambda d: d["filename"].lower(), reverse=True)
    elif sort_by == "Most opened":
        filtered = sorted(filtered, key=lambda d: d.get("opened_count", 0), reverse=True)

    total_str = f"{len(filtered)} of {len(all_docs)}" if search else str(len(all_docs))
    st.markdown(
        f'<div class="recent-header">{total_str} document{"s" if len(filtered) != 1 else ""}</div>',
        unsafe_allow_html=True,
    )

    if not filtered:
        st.markdown(
            '<div class="info-tip padded">No documents match your search.</div>',
            unsafe_allow_html=True,
        )
        return

    for doc in filtered:
        _render_document_row(doc)
        st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)


_render_history()
