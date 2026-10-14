
"""StudyBuddy AI — main entry point."""

import sys
import io
import os
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

from database.database import init_db, save_visual_analysis
from utils.helpers import load_css, init_session_state


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="StudyBuddy AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="locked",
)

init_db()
load_css()
init_session_state()


# --------------------------------------------------
# REGISTER APPLICATION PAGES
# --------------------------------------------------

studybuddy_page = st.Page(
    "pages/1_Home.py",
    title="Learning Hub",
    icon="🏠",
    default=True,
)

explanation_page = st.Page(
    "pages/2_Explanation.py",
    title="Explanation",
    icon="💡",
)

summary_page = st.Page(
    "pages/3_Summary.py",
    title="Summary",
    icon="📄",
)

quiz_page = st.Page(
    "pages/4_Quiz.py",
    title="Quiz",
    icon="📝",
)

flashcards_page = st.Page(
    "pages/5_Flashcards.py",
    title="Flashcards",
    icon="🃏",
)

history_page = st.Page(
    "pages/6_History.py",
    title="History",
    icon="📚",
)

research_page = st.Page(
    "pages/7_Research_Paper.py",
    title="Research Paper",
    icon="📑",
)


# --------------------------------------------------
# VISUAL ANALYZER
# --------------------------------------------------

def visual_analyzer():
    """Analyze images and display analyses opened from History."""

    def get_api_key():
        api_key = ""

        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass

        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "")

        return api_key.strip()

    # Restore the selected saved analysis before rendering the page.
    history_visual_id = st.session_state.get("visual_history_open_id")
    opened_from_history = bool(history_visual_id)

    if history_visual_id:
        from database.database import get_all_visual_analyses

        try:
            saved_visuals = get_all_visual_analyses()

            history_visual = next(
                (
                    item
                    for item in saved_visuals
                    if str(item.get("id")) == str(history_visual_id)
                ),
                None,
            )

            if history_visual:
                st.session_state["visual_analysis_result"] = (
                    history_visual.get("analysis", "")
                )
                st.session_state["visual_analysis_filename"] = (
                    history_visual.get("filename", "")
                )
                st.session_state["visual_analysis_type_result"] = (
                    history_visual.get(
                        "analysis_type", "Figure or Image"
                    )
                )

                saved_type = history_visual.get(
                    "analysis_type", "Figure or Image"
                )

                valid_types = [
                    "Figure or Image",
                    "Diagram or Flowchart",
                    "Chart or Graph",
                    "Table",
                ]

                if saved_type in valid_types:
                    st.session_state["visual_analysis_type"] = saved_type

            else:
                st.warning(
                    "This saved visual analysis could not be found."
                )

        except Exception as exc:
            st.error("Could not load the saved visual analysis.")

            with st.expander("Technical details"):
                st.code(str(exc))

        finally:
            st.session_state.pop("visual_history_open_id", None)

    # Show the existing Visual Analyzer interface.
    st.markdown(
        dedent(
            """
            <div class="hero-card">
                <div class="hero-title">
                    🖼️ <span class="hero-accent">Visual Analyzer</span>
                </div>
                <p class="hero-description">
                    Upload and explore figures, diagrams, tables, charts,
                    and graphs from your study material.
                </p>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    st.markdown("### 📤 Upload a visual")

    uploaded_image = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "webp"],
        key="visual_image_upload",
        help="Supported formats: PNG, JPG, JPEG and WEBP",
    )

    st.markdown("### 🔎 What would you like to analyze?")

    analysis_type = st.selectbox(
        "Select visual type",
        [
            "Figure or Image",
            "Diagram or Flowchart",
            "Chart or Graph",
            "Table",
        ],
        key="visual_analysis_type",
    )

    result = st.session_state.get("visual_analysis_result", "")
    result_filename = st.session_state.get(
        "visual_analysis_filename", ""
    )

    # When opened from History, display the saved result immediately.
    # Do not require the user to upload the image again.
    if opened_from_history:
        st.markdown("### 🖼️ Saved Visual")

        with st.container(border=True):
            st.markdown(
                f"**Filename:** {result_filename or 'Saved visual'}"
            )
            st.markdown(
                f"**Analysis type:** "
                f"{st.session_state.get('visual_analysis_type_result', 'Visual')}"
            )

        st.markdown("### 📊 Saved Analysis")

        with st.container(border=True):
            if result:
                st.markdown(
                    f"#### 🧠 AI Explanation — "
                    f"{result_filename or 'Saved visual'}"
                )
                st.markdown(result)

                st.download_button(
                    "⬇️ Download Analysis",
                    data=result,
                    file_name=(
                        f"{Path(result_filename).stem}_analysis.md"
                        if result_filename
                        else "visual_analysis.md"
                    ),
                    mime="text/markdown",
                    use_container_width=True,
                    key="download_visual_history",
                )
            else:
                st.warning(
                    "The saved record exists, but its analysis text is empty."
                )

        # Don't accidentally display or analyze a previously uploaded image
        # while opening a saved record from History.
        return

    # No new upload: show the last saved/generated explanation, if available.
    if uploaded_image is None:
        st.markdown("### 🖼️ Image Preview")

        with st.container(border=True):
            st.caption(
                "Upload an image to preview and analyze it. "
                "Previously generated explanations can appear below."
            )

        st.markdown("### 📊 Analysis Results")

        with st.container(border=True):
            if result:
                st.markdown(
                    f"#### 🧠 AI Explanation — "
                    f"{result_filename or 'Saved visual'}"
                )
                st.markdown(result)

                st.download_button(
                    "⬇️ Download Analysis",
                    data=result,
                    file_name="visual_analysis.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="download_visual_no_upload",
                )
            else:
                st.caption(
                    "The visual explanation and key insights will appear here."
                )

        return

    # Validate and preview the uploaded image.
    image_bytes = uploaded_image.getvalue()

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()

        image = Image.open(io.BytesIO(image_bytes))
        image.load()

    except Exception:
        st.error("This image is invalid or cannot be opened.")
        return

    st.markdown("### 🖼️ Image Preview")

    with st.container(border=True):
        st.image(
            image,
            caption=uploaded_image.name,
            width=700,
        )

    st.markdown("### 📊 Analysis Results")

    if st.button(
        "🔍 Analyze Visual",
        type="primary",
        use_container_width=True,
        key="run_visual_analysis",
    ):
        api_key = get_api_key()

        if not api_key:
            st.error(
                "Gemini API key not found. Configure GEMINI_API_KEY in "
                ".streamlit/secrets.toml or your .env file."
            )

        else:
            mime_type = uploaded_image.type or "image/png"

            prompts = {
                "Figure or Image": (
                    "Explain what this educational image represents, "
                    "its important elements, observations, and study notes."
                ),
                "Diagram or Flowchart": (
                    "Explain this diagram or flowchart step by step. "
                    "Describe components, arrows, connections, and the process."
                ),
                "Chart or Graph": (
                    "Explain the chart title, axes, labels, trends, "
                    "comparisons, and conclusions. Do not invent values."
                ),
                "Table": (
                    "Explain the table headings, rows, columns, important "
                    "values, comparisons, and findings. Do not guess values."
                ),
            }

            prompt = f"""
You are StudyBuddy AI, an educational visual-analysis assistant.

Analyze this uploaded {analysis_type.lower()}.

{prompts[analysis_type]}

Use these headings:

1. What It Represents
2. Main Components
3. Step-by-Step Explanation
4. Key Observations
5. Important Study Notes

Use simple, student-friendly language.
Describe only details supported by the image.
Mention any unreadable text or values clearly.
If a section is not applicable, say so briefly.
"""

            with st.spinner("Gemini is analyzing your visual..."):
                try:
                    client = genai.Client(api_key=api_key)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            prompt,
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=mime_type,
                            ),
                        ],
                    )

                    result = (response.text or "").strip()

                    if not result:
                        st.error(
                            "Gemini returned an empty response. "
                            "Please try another image."
                        )

                    else:
                        st.session_state["visual_analysis_result"] = result
                        st.session_state["visual_analysis_filename"] = (
                            uploaded_image.name
                        )
                        st.session_state["visual_analysis_type_result"] = (
                            analysis_type
                        )

                        try:
                            save_visual_analysis(
                                filename=uploaded_image.name,
                                analysis_type=analysis_type,
                                analysis=result,
                            )

                            st.success(
                                "Visual analysis saved to your history!"
                            )

                        except Exception as exc:
                            st.error(
                                "Analysis completed, but saving to "
                                "history failed."
                            )

                            with st.expander("Technical details"):
                                st.code(str(exc))

                except Exception as exc:
                    st.error("Visual analysis failed.")

                    with st.expander("Technical details"):
                        st.code(str(exc))

    # Display the result for the currently uploaded image.
    result = st.session_state.get("visual_analysis_result", "")
    result_filename = st.session_state.get(
        "visual_analysis_filename", ""
    )

    if result and result_filename == uploaded_image.name:
        st.markdown("---")
        st.markdown(f"#### 🧠 AI Explanation — {result_filename}")
        st.markdown(result)

        st.download_button(
            "⬇️ Download Analysis",
            data=result,
            file_name="visual_analysis.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_visual_current",
        )


# --------------------------------------------------
# REGISTER VISUAL ANALYZER PAGE
# --------------------------------------------------

visual_page = st.Page(
    visual_analyzer,
    title="Visual Analyzer",
    icon="🖼️",
)


# --------------------------------------------------
# PAGE NAVIGATION
# --------------------------------------------------

pg = st.navigation(
    [
        studybuddy_page,
        explanation_page,
        summary_page,
        quiz_page,
        flashcards_page,
        research_page,
        visual_page,
        history_page,
    ],
    position="hidden",
)


# --------------------------------------------------
# HORIZONTAL STUDY NAVIGATION
# --------------------------------------------------

study_pages = {
    "Summary": "pages/3_Summary.py",
    "Explanation": "pages/2_Explanation.py",
    "Quiz": "pages/4_Quiz.py",
    "Flashcards": "pages/5_Flashcards.py",
}


def navigate_study_tab():
    selected = st.session_state.get("study_tab")
    target = study_pages.get(selected)

    if target:
        st.switch_page(target)


if pg.title in study_pages:
    st.session_state["study_tab"] = pg.title

    st.markdown(
        """
        <style>
        div[data-testid="stRadio"] > label {
            display: none !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 10px !important;
        }

        div[data-testid="stRadio"] label {
            background-color: #FFFFFF !important;
            border: 1px solid #E5D4AD !important;
            border-radius: 10px !important;
            padding: 10px 18px !important;
            margin: 0 !important;
            cursor: pointer !important;
            transition: background-color 0.2s ease,
                        border-color 0.2s ease !important;
        }

        div[data-testid="stRadio"] label > div:first-child {
            display: none !important;
        }

        div[data-testid="stRadio"] label p,
        div[data-testid="stRadio"] label span,
        div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
            color: #0F2D52 !important;
            -webkit-text-fill-color: #0F2D52 !important;
            opacity: 1 !important;
            font-weight: 600 !important;
        }

        div[data-testid="stRadio"] label:has(input:checked) {
            background-color: #0F2D52 !important;
            border-color: #0F2D52 !important;
        }

        div[data-testid="stRadio"] label:has(input:checked) p,
        div[data-testid="stRadio"] label:has(input:checked) span,
        div[data-testid="stRadio"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        div[data-testid="stRadio"] label:hover {
            border-color: #0F2D52 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.radio(
        "Study sections",
        options=["Summary", "Explanation", "Quiz", "Flashcards"],
        horizontal=True,
        key="study_tab",
        label_visibility="collapsed",
        on_change=navigate_study_tab,
    )

    st.markdown(
        '<div style="border-bottom:1px solid #E2DCCF;'
        'margin-bottom:1.5rem;"></div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# CUSTOM SIDEBAR
# --------------------------------------------------

with st.sidebar:
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

    st.markdown(
        '<p class="nav-section-title">Main</p>',
        unsafe_allow_html=True,
    )

    st.page_link(
        studybuddy_page,
        label="Learning Hub",
        icon="🏠",
    )

    st.page_link(
        research_page,
        label="Research Paper",
        icon="📑",
    )

    st.page_link(
        visual_page,
        label="Visual Analyzer",
        icon="🖼️",
    )

    st.markdown(
        '<p class="nav-section-title with-gap">Records</p>',
        unsafe_allow_html=True,
    )

    st.page_link(
        history_page,
        label="History",
        icon="📚",
    )

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

    st.markdown(
        dedent(
            """
            <div class="sidebar-footer">
                <p class="sidebar-about">
                    StudyBuddy AI&nbsp;·&nbsp; Powered by Gemini 2.5 Flash
                </p>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# RUN CURRENT PAGE
# --------------------------------------------------

# History sets this flag when the user clicks Open on a visual entry.
# Switch to the registered page object, not a filename.
if st.session_state.pop("go_to_visual_analyzer", False):
    st.switch_page(visual_page)

pg.run()
