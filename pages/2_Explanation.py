
"""Explanation page - four sections from SQLite. Never calls Gemini."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.helpers import page_header, no_document_warning


def _ensure_explanation(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        return {
            "simple_explanation": raw,
            "important_concepts": [],
            "real_life_examples": [],
            "exam_tips": [],
        }
    return {
        "simple_explanation": "",
        "important_concepts": [],
        "real_life_examples": [],
        "exam_tips": [],
    }


def _render_explanation(doc: dict) -> None:
    page_header("📖  Explanation", f"Detailed breakdown · {doc['filename']}")

    exp = _ensure_explanation(doc.get("explanation"))
    has_content = any([
        exp.get("simple_explanation"),
        exp.get("important_concepts"),
        exp.get("real_life_examples"),
        exp.get("exam_tips"),
    ])

    if not has_content:
        st.warning("No explanation found for this document.")
        return

    simple = exp.get("simple_explanation", "").strip()

    if simple:
        st.markdown(
            '<div class="section-label">💡 &nbsp;Simple Explanation</div>',
            unsafe_allow_html=True,
        )
        paragraphs = [
            p.strip() for p in simple.split("\n\n") if p.strip()
        ]
        paras_html = "".join(
            f"<p class='content-paragraph'>{p}</p>"
            for p in paragraphs
        )
        st.markdown(
            f'<div class="content-block section-block">{paras_html}</div>',
            unsafe_allow_html=True,
        )

    concepts = exp.get("important_concepts", [])

    if concepts:
        st.markdown(
            '<div class="section-label">📚 &nbsp;Important Concepts</div>',
            unsafe_allow_html=True,
        )
        cards_html = "".join(
            dedent(
                f"""
                <div class="concept-card">
                    <div class="concept-title">{c.get("concept", "")}</div>
                    <div class="concept-body">{c.get("definition", "")}</div>
                </div>
                """
            ).strip()
            for c in concepts
            if isinstance(c, dict)
        )
        st.markdown(
            f'<div class="card-list">{cards_html}</div>',
            unsafe_allow_html=True,
        )

    examples = exp.get("real_life_examples", [])

    if examples:
        st.markdown(
            '<div class="section-label">🌍 &nbsp;Real-life Examples</div>',
            unsafe_allow_html=True,
        )
        ex_html = "".join(
            dedent(
                f"""
                <div class="example-card">
                    <span class="example-index">{i + 1}</span>
                    <span class="example-text">{example}</span>
                </div>
                """
            ).strip()
            for i, example in enumerate(examples)
        )
        st.markdown(
            f'<div class="card-list">{ex_html}</div>',
            unsafe_allow_html=True,
        )

    tips = exp.get("exam_tips", [])

    if tips:
        st.markdown(
            '<div class="section-label">🎓 &nbsp;Exam Tips</div>',
            unsafe_allow_html=True,
        )
        tips_html = "".join(
            dedent(
                f"""
                <div class="tip-row">
                    <span class="tip-row-icon">💡</span>
                    <span class="tip-row-text">{tip}</span>
                </div>
                """
            ).strip()
            for tip in tips
        )
        st.markdown(
            f'<div class="content-block">{tips_html}</div>',
            unsafe_allow_html=True,
        )


st.button(
    "← Back to Learning Hub",
    key="explanation_back",
    on_click=lambda: st.switch_page("pages/1_Home.py"),
)

doc = st.session_state.get("current_doc")

if not doc:
    page_header("📖  Explanation")
    no_document_warning()
else:
    _render_explanation(doc)
