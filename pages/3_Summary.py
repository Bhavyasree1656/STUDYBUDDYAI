"""Summary page - short summary, bullet points, key takeaways. Reads only from SQLite."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.helpers import page_header, no_document_warning, format_date


def _meta_pill(label: str, value: str) -> str:
    return dedent(
        f"""
    <div class="meta-pill">
        <div class="meta-pill-label">{label}</div>
        <div class="meta-pill-value">{value}</div>
    </div>
    """
    ).strip()


def _ensure_summary(raw) -> dict:
    """Normalise summary field - handles both new dict and legacy string."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        return {"short_summary": raw, "bullet_points": [], "key_takeaways": []}
    return {"short_summary": "", "bullet_points": [], "key_takeaways": []}


def _build_markdown(doc: dict, summary: dict) -> str:
    lines = [
        f"# Study Summary: {doc['filename']}",
        f"Generated: {format_date(doc.get('generated_time') or doc.get('created_at', ''))}",
        "",
        "---",
        "",
        "## Short Summary",
        "",
        summary.get("short_summary", ""),
        "",
        "## Key Points",
        "",
    ]
    for bp in summary.get("bullet_points", []):
        lines.append(f"- {bp}")
    lines += ["", "## Key Takeaways", ""]
    for kt in summary.get("key_takeaways", []):
        lines.append(f"✓ {kt}")
    return "\n".join(lines)


def _content_list(items: list[str], bullet: str) -> str:
    rows = "".join(
        dedent(
            f"""
        <div class="content-list-row">
            <span class="content-list-bullet">{bullet}</span>
            <span class="content-list-text">{item}</span>
        </div>
        """
        ).strip()
        for item in items
    )
    return f'<div class="content-block section-block"><div class="content-list">{rows}</div></div>'


def _render_summary(doc: dict) -> None:
    page_header("📝  Summary", f"Key concepts at a glance · {doc['filename']}")

    quiz_count = len(doc.get("quiz", []))
    fc_count = len(doc.get("flashcards", []))
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.markdown(_meta_pill("Document", doc["filename"]), unsafe_allow_html=True)
    with c2:
        st.markdown(_meta_pill("Processed", format_date(doc["created_at"])), unsafe_allow_html=True)
    with c3:
        st.markdown(
            _meta_pill("Study materials", f"{quiz_count} quiz Qs · {fc_count} flashcards"),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    summary = _ensure_summary(doc.get("summary"))
    if not summary.get("short_summary") and not summary.get("bullet_points") and not summary.get("key_takeaways"):
        st.warning("No summary found for this document.")
        return

    st.markdown('<div class="section-label">📄 &nbsp;Short Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="content-block section-block">{summary.get("short_summary", "")}</div>',
        unsafe_allow_html=True,
    )

    bullet_points = summary.get("bullet_points", [])
    if bullet_points:
        st.markdown('<div class="section-label">📌 &nbsp;Key Points</div>', unsafe_allow_html=True)
        st.markdown(_content_list(bullet_points, "▸"), unsafe_allow_html=True)

    takeaways = summary.get("key_takeaways", [])
    if takeaways:
        st.markdown('<div class="section-label">🎯 &nbsp;Key Takeaways</div>', unsafe_allow_html=True)
        rows_html = "".join(
            dedent(
                f"""
            <div class="takeaway-row">
                <span class="takeaway-check">✓</span>
                <span class="takeaway-text">{takeaway}</span>
            </div>
            """
            ).strip()
            for takeaway in takeaways
        )
        st.markdown(f'<div class="takeaway-list">{rows_html}</div>', unsafe_allow_html=True)

    md_content = _build_markdown(doc, summary)

    st.markdown("<hr>", unsafe_allow_html=True)
    col_dl, col_copy, col_spacer = st.columns([1, 1, 3])

    with col_dl:
        safe_name = doc["filename"].rsplit(".", 1)[0].replace(" ", "_")
        st.download_button(
            label="⬇  Download Markdown",
            data=md_content.encode("utf-8"),
            file_name=f"{safe_name}_summary.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_copy:
        if st.button("📋  Copy Text", use_container_width=True):
            st.session_state["_show_copy_area"] = True

    if st.session_state.get("_show_copy_area"):
        st.text_area(
            "Select all and copy (Ctrl+A -> Ctrl+C):",
            value=md_content,
            height=200,
            key="copy_text_area",
        )

    st.markdown(
        dedent(
            """
        <div class="continue-card">
            <div class="continue-title">Continue studying</div>
            <div class="continue-text">
                📖 <strong>Explanation</strong> - Detailed breakdown with concepts &amp; examples<br>
                🧠 <strong>Quiz</strong> - Test your knowledge question by question<br>
                🃏 <strong>Flashcards</strong> - Review key terms and definitions
            </div>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )



doc = st.session_state.get("current_doc")

if st.button("← Back to Learning Hub", key="summary_back"):
    st.switch_page("pages/1_Home.py")

if not doc:
    page_header("📝  Summary")
    no_document_warning()
else:
    _render_summary(doc)

