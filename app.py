"""StudyBuddy AI — main entry point."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from database.database import init_db
from utils.helpers import load_css, init_session_state

st.set_page_config(
    page_title="StudyBuddy AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
load_css()
init_session_state()

# ── Register pages before sidebar so page objects exist ───────────────────
home_page        = st.Page("pages/1_Home.py",        title="Home",        icon="🏠", default=True)
explanation_page = st.Page("pages/2_Explanation.py", title="Explanation",  icon="📖")
summary_page     = st.Page("pages/3_Summary.py",     title="Summary",      icon="📝")
quiz_page        = st.Page("pages/4_Quiz.py",        title="Quiz",         icon="🧠")
flashcards_page  = st.Page("pages/5_Flashcards.py",  title="Flashcards",   icon="🃏")
history_page     = st.Page("pages/6_History.py",     title="History",      icon="📚")

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Logo ──
    st.markdown(
        dedent(
            """
        <div class="sidebar-logo">
            <span class="logo-emoji">📚</span>
            <span class="logo-title">StudyBuddy AI</span>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )

    # ── Navigation ──
    st.markdown('<p class="nav-section-title">Navigation</p>', unsafe_allow_html=True)
    st.page_link(home_page,        label="Home",        icon="🏠")
    st.page_link(explanation_page, label="Explanation",  icon="📖")
    st.page_link(summary_page,     label="Summary",      icon="📝")
    st.page_link(quiz_page,        label="Quiz",         icon="🧠")
    st.page_link(flashcards_page,  label="Flashcards",   icon="🃏")

    st.markdown('<p class="nav-section-title with-gap">Records</p>', unsafe_allow_html=True)
    st.page_link(history_page, label="History", icon="📚")

    # ── Active document pill ──
    if st.session_state.get("current_doc"):
        doc = st.session_state.current_doc
        st.markdown(
            dedent(
                f"""
            <div class="active-doc-pill">
                <div class="active-doc-label">Active document</div>
                <div class="active-doc-name">{doc["filename"]}</div>
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )

    # ── Footer ──
    st.markdown(
        dedent(
            """
        <div class="sidebar-footer">
            <p class="sidebar-about">StudyBuddy AI &nbsp;·&nbsp; Powered by Gemini 2.5 Flash</p>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )

# ── Navigation (position hidden — links drawn manually above) ─────────────
pg = st.navigation(
    [home_page, explanation_page, summary_page, quiz_page, flashcards_page, history_page],
    position="hidden",
)
pg.run()
