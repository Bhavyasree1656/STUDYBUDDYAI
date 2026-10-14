
"""Visual Analyzer page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from PIL import Image
from io import BytesIO

from models.gemini import get_model


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">
                🖼️ <span class="hero-accent">Visual</span> Analyzer
            </div>
            <p class="hero-description">
                Upload a diagram, chart, table, figure, or image and
                get an AI-powered explanation of what it represents.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _analyze_image(image_bytes: bytes, mime_type: str) -> str:
    """Send an image to Gemini and return its explanation."""
    model = get_model()

    prompt = """
    Analyze this educational image carefully.

    Provide the response using these headings:

    1. **What the image represents**
       Explain its overall purpose in simple language.

    2. **Main components**
       Describe the important labels, shapes, symbols, axes, or elements.

    3. **Step-by-step explanation**
       Explain the flow or sequence in order, if applicable.

    4. **Key observations**
       Highlight important relationships, patterns, or conclusions.

    5. **Short study notes**
       Give 3–5 concise points useful for revision.

    Be accurate. Do not invent labels or details that are not visible.
    If some text is unreadable, clearly mention that.
    """

    response = model.generate_content(
        [
            prompt,
            {
                "mime_type": mime_type,
                "data": image_bytes,
            },
        ]
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text


def _render_upload() -> None:
    st.markdown(
        '<div class="section-label">📤 &nbsp;Upload Visual</div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="visual_analyzer_upload",
    )

    if not uploaded:
        return

    image_bytes = uploaded.getvalue()

    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()
        image = Image.open(BytesIO(image_bytes))

    except Exception:
        st.error("This image could not be opened. Please upload another image.")
        return

    st.success(f"Ready: {uploaded.name}")

    st.image(
        image,
        caption="Uploaded Visual",
        use_container_width=True,
    )

    mime_type = uploaded.type or "image/png"

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "🔍 Analyze Visual",
        type="primary",
        use_container_width=True,
        key="analyze_visual_button",
    ):
        with st.spinner("Gemini is analyzing your visual..."):
            try:
                result = _analyze_image(image_bytes, mime_type)
                st.session_state["visual_analysis_result"] = result
                st.session_state["visual_analysis_filename"] = uploaded.name

            except Exception as exc:
                st.error(
                    "Visual analysis failed. Check your Gemini configuration "
                    "and try again."
                )
                with st.expander("Technical details"):
                    st.code(str(exc))

    result = st.session_state.get("visual_analysis_result")
    result_filename = st.session_state.get("visual_analysis_filename")

    if result and result_filename == uploaded.name:
        st.markdown(
            '<div class="section-label">📊 &nbsp;Analysis Results</div>',
            unsafe_allow_html=True,
        )
        st.markdown(result)

        st.download_button(
            "⬇️ Download Analysis",
            data=result,
            file_name="visual_analysis.md",
            mime="text/markdown",
            use_container_width=True,
        )


_render_header()
_render_upload()
