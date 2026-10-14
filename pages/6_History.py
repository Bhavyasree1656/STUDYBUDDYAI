
"""History page - combined document and visual analysis history."""

import sys
from pathlib import Path
from textwrap import dedent
from html import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from services.history import (
    get_history,
    load_document,
    remove_document,
    record_opened,
)

from database.database import (
    get_research_analysis,
    get_all_visual_analyses,
    delete_visual_analysis,
)

from utils.helpers import page_header, format_date, format_file_size


_EXT_ICONS = {
    "pdf": "📄",
    "docx": "📝",
    "txt": "📃",
    "pptx": "📊",
    "png": "🖼️",
    "jpg": "🖼️",
    "jpeg": "🖼️",
    "webp": "🖼️",
}


def _ext_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_ICONS.get(ext, "📄")


def _open_document(doc_id: str) -> None:
    record_opened(doc_id)
    doc = load_document(doc_id)

    if not doc:
        st.error("Could not load this document.")
        return

    st.session_state.current_doc_id = doc_id
    st.session_state.current_doc = doc
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_doc_id = None
    st.session_state.fc_doc_id = None
    st.session_state.card_index = 0
    st.session_state.card_flipped = False

    research_analysis = get_research_analysis(doc_id)

    if research_analysis:
        st.session_state["research_doc_id"] = doc_id
        st.session_state["research_opened_doc"] = doc
        st.session_state["research_filename"] = doc.get(
            "filename", "Research paper"
        )
        st.session_state["research_analysis"] = research_analysis
        st.switch_page("pages/7_Research_Paper.py")
    else:
        st.switch_page("pages/3_Summary.py")


def _confirm_delete(doc_id: str) -> None:
    key = f"confirm_delete_{doc_id}"

    if not st.session_state.get(key, False):
        if st.button(
            "🗑",
            key=f"del_{doc_id}",
            use_container_width=True,
        ):
            st.session_state[key] = True
            st.rerun()
        return

    st.markdown(
        '<div class="history-delete-confirm">Delete?</div>',
        unsafe_allow_html=True,
    )

    col_yes, col_no = st.columns(2)

    with col_yes:
        if st.button("Yes", key=f"yes_{doc_id}", use_container_width=True):
            if st.session_state.get("current_doc_id") == doc_id:
                st.session_state.current_doc_id = None
                st.session_state.current_doc = None

            if st.session_state.get("research_doc_id") == doc_id:
                for key_to_clear in (
                    "research_doc_id",
                    "research_opened_doc",
                    "research_analysis",
                    "research_filename",
                ):
                    st.session_state.pop(key_to_clear, None)

            remove_document(doc_id)
            st.session_state.pop(key, None)
            st.rerun()

    with col_no:
        if st.button("No", key=f"no_{doc_id}", use_container_width=True):
            st.session_state[key] = False
            st.rerun()


def _document_row_html(doc: dict, is_active: bool) -> str:
    active_class = "doc-row is-active" if is_active else "doc-row"

    active_badge = (
        '<span class="status-badge status-badge-active">Active</span>'
        if is_active
        else ""
    )

    filename = escape(str(doc.get("filename", "Untitled document")))
    opened = doc.get("opened_count", 0)
    opens_text = f"&nbsp;·&nbsp; 👁 Opened {opened}×" if opened else ""

    return dedent(
        f"""
        <div class="{active_class}">
            <span class="doc-row-icon">{_ext_icon(filename)}</span>
            <div class="doc-row-content">
                <div class="doc-row-title">
                    {filename}{active_badge}
                </div>
                <div class="doc-row-meta">
                    📅 {format_date(doc.get("created_at", ""))}
                    &nbsp;·&nbsp; 💾 {format_file_size(doc.get("file_size", 0))}
                    {opens_text}
                </div>
            </div>
        </div>
        """
    ).strip()


def _render_document_row(doc: dict) -> None:
    doc_id = doc["id"]

    is_active = (
        doc_id == st.session_state.get("current_doc_id")
        or doc_id == st.session_state.get("research_doc_id")
    )

    col_card, col_open, col_delete = st.columns([6, 1, 1], gap="small")

    with col_card:
        st.markdown(
            _document_row_html(doc, is_active),
            unsafe_allow_html=True,
        )

    with col_open:
        st.write("")
        if st.button(
            "Open",
            key=f"open_{doc_id}",
            use_container_width=True,
        ):
            _open_document(doc_id)

    with col_delete:
        st.write("")
        _confirm_delete(doc_id)

    st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)


def _render_visual_row(item: dict) -> None:
    """Render a visual analysis like a normal History row."""

    visual_id = item.get("id", "")
    filename = str(item.get("filename", "Uploaded image"))
    analysis_type = str(item.get("analysis_type", "Visual"))
    created_at = str(item.get("created_at", ""))

    safe_filename = escape(filename)
    safe_type = escape(analysis_type)
    safe_date = escape(created_at[:10])

    col_card, col_open, col_delete = st.columns(
        [6, 1, 1], gap="small"
    )

    with col_card:
        st.markdown(
            dedent(
                f"""
                <div class="doc-row">
                    <span class="doc-row-icon">🖼️</span>
                    <div class="doc-row-content">
                        <div class="doc-row-title">{safe_filename}</div>
                        <div class="doc-row-meta">
                            🔎 {safe_type}
                            &nbsp;·&nbsp; 📅 {safe_date}
                        </div>
                    </div>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    with col_open:
        st.write("")
        if st.button(
            "Open",
            key=f"open_visual_{visual_id}",
            use_container_width=True,
        ):
            # app.py handles this flag and switches to visual_page.
            st.session_state["visual_history_open_id"] = visual_id
            st.session_state["go_to_visual_analyzer"] = True
            st.rerun()

    with col_delete:
        st.write("")
        if st.button(
            "🗑",
            key=f"delete_visual_{visual_id}",
            use_container_width=True,
        ):
            delete_visual_analysis(visual_id)
            st.rerun()

    st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)


def _render_history() -> None:
    page_header("📚 History", "All your documents and visual analyses")

    try:
        all_docs = get_history()
        visual_analyses = get_all_visual_analyses()
    except Exception as exc:
        st.error("Could not load history.")
        with st.expander("Technical details"):
            st.code(str(exc))
        return

    # Combine documents, research papers, and visual analyses.
    entries = []

    for doc in all_docs:
        entries.append({
            "kind": "document",
            "date": str(doc.get("upload_time", doc.get("created_at", ""))),
            "filename": str(doc.get("filename", "")),
            "data": doc,
        })

    for visual in visual_analyses:
        entries.append({
            "kind": "visual",
            "date": str(visual.get("created_at", "")),
            "filename": str(visual.get("filename", "")),
            "data": visual,
        })

    entries.sort(key=lambda entry: entry["date"], reverse=True)

    if not entries:
        st.info(
            "No history yet. Upload a document or analyze an image "
            "to see it here."
        )
        return

    col_search, col_sort = st.columns([3, 1], gap="small")

    with col_search:
        search = st.text_input(
            "search",
            placeholder="🔍 Search by filename...",
            label_visibility="collapsed",
        )

    with col_sort:
        sort_by = st.selectbox(
            "sort",
            [
                "Newest first",
                "Oldest first",
                "Name A → Z",
                "Name Z → A",
                "Most opened",
            ],
            label_visibility="collapsed",
        )

    if search:
        entries = [
            entry for entry in entries
            if search.lower() in entry["filename"].lower()
        ]

    if sort_by == "Oldest first":
        entries.sort(key=lambda entry: entry["date"])
    elif sort_by == "Name A → Z":
        entries.sort(key=lambda entry: entry["filename"].lower())
    elif sort_by == "Name Z → A":
        entries.sort(
            key=lambda entry: entry["filename"].lower(),
            reverse=True,
        )
    elif sort_by == "Most opened":
        entries.sort(
            key=lambda entry: (
                entry["data"].get("opened_count", 0)
                if entry["kind"] == "document"
                else 0
            ),
            reverse=True,
        )
    else:
        entries.sort(key=lambda entry: entry["date"], reverse=True)

    st.markdown(f"**{len(entries)} history entries**")

    for entry in entries:
        if entry["kind"] == "document":
            _render_document_row(entry["data"])
        else:
            _render_visual_row(entry["data"])


_render_history()
