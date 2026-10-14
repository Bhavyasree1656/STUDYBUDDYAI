"""StudyBuddy AI — Research Paper Analysis."""

import sys
import json
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from services.extractor import extract_text
from services.research_analyzer import analyze_research_paper
from database.database import (
    save_document,
    save_research_analysis,
    get_research_analysis,
)
from utils.constants import MAX_TEXT_LENGTH
from utils.helpers import page_header, format_file_size


def display_value(value, fallback="Not identified"):
    if value is None or value == "":
        return fallback
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or fallback
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def render_text_section(title, icon, content):
    if content is None or content == "" or content == []:
        return
    st.markdown(f"### {icon} {title}")
    with st.container(border=True):
        st.write(content)


def render_list_section(title, icon, items):
    if not items:
        return
    if not isinstance(items, list):
        items = [items]
    st.markdown(f"### {icon} {title}")
    with st.container(border=True):
        for item in items:
            if isinstance(item, dict):
                item = json.dumps(item, ensure_ascii=False)
            st.markdown(f"- {item}")


def build_report(analysis, filename):
    lines = [
        "# Research Paper Analysis",
        "",
        f"**File:** {filename}",
        "",
    ]

    paper_info = analysis.get("paper_info", {})
    if isinstance(paper_info, dict):
        lines.extend(["## Paper Information", ""])
        for key, value in paper_info.items():
            lines.append(
                f"- **{key.replace('_', ' ').title()}:** "
                f"{display_value(value)}"
            )
        lines.append("")

    sections = [
        ("research_problem", "Research Problem"),
        ("objectives", "Objectives"),
        ("existing_approach", "Existing Approach"),
        ("proposed_methodology", "Proposed Methodology"),
        ("dataset", "Dataset"),
        ("technologies_and_algorithms", "Technologies and Algorithms"),
        ("evaluation_metrics", "Evaluation Metrics"),
        ("results", "Results and Findings"),
        ("advantages", "Advantages"),
        ("limitations", "Limitations"),
        ("research_gap", "Research Gap"),
        ("future_work", "Future Work"),
        ("key_contributions", "Key Contributions"),
    ]

    for key, title in sections:
        value = analysis.get(key)
        if value is None or value == "" or value == []:
            continue
        lines.extend([f"## {title}", "", display_value(value), ""])

    return "\n".join(lines)


# --------------------------------------------------
# LOAD SAVED RESEARCH ANALYSIS WHEN OPENED FROM HISTORY
# --------------------------------------------------

research_doc_id = st.session_state.get("research_doc_id")

if research_doc_id:
    saved_analysis = get_research_analysis(research_doc_id)

    if saved_analysis:
        st.session_state["research_analysis"] = saved_analysis

    saved_doc = st.session_state.get("research_opened_doc", {})
    if saved_doc:
        st.session_state["research_filename"] = saved_doc.get(
            "filename", "Research paper"
        )


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

page_header(
    "📑 Research Insight Hub",
    "Upload a research paper to extract its problem, methodology, "
    "dataset, results, limitations, research gap, and contributions.",
)

st.markdown("### 📤 Upload a Research Paper")

st.caption(
    "Supported formats: PDF, DOCX, TXT and PPTX. "
    "For best results, upload a paper with selectable text."
)

uploaded_file = st.file_uploader(
    "Choose your research paper",
    type=["pdf", "docx", "txt", "pptx"],
    key="research_paper_upload",
    help="Upload one research paper at a time.",
)

if uploaded_file is not None:
    file_name = uploaded_file.name

    with st.container(border=True):
        col_file, col_size = st.columns([3, 1])
        with col_file:
            st.markdown("**📄 Selected file**")
            st.write(file_name)
        with col_size:
            st.markdown("**File size**")
            st.write(format_file_size(uploaded_file.size))

    if st.button(
        "🔬 Analyze Research Paper",
        type="primary",
        use_container_width=True,
        key="analyze_research_paper",
    ):
        try:
            with st.spinner(
                "Extracting text and analyzing your research paper..."
            ):
                extracted_text = extract_text(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                )

                if not extracted_text or not extracted_text.strip():
                    st.error(
                        "Could not extract readable text from this file. "
                        "Please upload another paper."
                    )
                    st.stop()

                extracted_text = extracted_text[:MAX_TEXT_LENGTH]
                analysis = analyze_research_paper(extracted_text)

                if not isinstance(analysis, dict) or not analysis:
                    st.error(
                        "The research paper could not be analyzed. "
                        "Please try again."
                    )
                    st.stop()

                # Save a document record for the existing History page.
                doc_id = save_document(
                    filename=file_name,
                    file_size=uploaded_file.size,
                    extracted_text=extracted_text,
                    summary={
                        "short_summary": analysis.get(
                            "research_problem", ""
                        ),
                        "bullet_points": analysis.get("objectives", []),
                        "key_takeaways": analysis.get(
                            "key_contributions", []
                        ),
                    },
                    explanation={
                        "simple_explanation": analysis.get(
                            "proposed_methodology", ""
                        ),
                        "important_concepts": analysis.get(
                            "technologies_and_algorithms", []
                        ),
                        "real_life_examples": [],
                        "exam_tips": [],
                    },
                    quiz=[],
                    flashcards=[],
                )

                # Persist the full research analysis separately.
                save_research_analysis(doc_id, analysis)

                st.session_state["research_doc_id"] = doc_id
                st.session_state["research_analysis"] = analysis
                st.session_state["research_filename"] = file_name
                st.session_state["research_opened_doc"] = {
                    "id": doc_id,
                    "filename": file_name,
                }

            st.success("Research paper analyzed and saved to History!")

        except Exception as exc:
            st.error(f"Could not analyze the research paper: {exc}")
            with st.expander("Technical error details"):
                st.code(traceback.format_exc())


# --------------------------------------------------
# DISPLAY RESEARCH INSIGHTS
# --------------------------------------------------

analysis = st.session_state.get("research_analysis")
filename = st.session_state.get("research_filename", "Research paper")

if isinstance(analysis, dict) and analysis:
    st.divider()
    st.markdown("## 📊 Research Insights")
    st.caption(f"Analysis for: {filename}")

    paper_info = analysis.get("paper_info", {})
    if not isinstance(paper_info, dict):
        paper_info = {}

    st.markdown(
        f"### 📄 {display_value(paper_info.get('title'), filename)}"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Authors**")
        st.write(display_value(paper_info.get("authors")))
        st.markdown("**Publication Year**")
        st.write(display_value(paper_info.get("publication_year")))

    with col2:
        st.markdown("**Publication Venue**")
        st.write(display_value(paper_info.get("venue")))
        st.markdown("**Keywords**")
        st.write(display_value(paper_info.get("keywords")))

    render_text_section(
        "Research Problem", "🔍", analysis.get("research_problem")
    )
    render_list_section(
        "Objectives", "🎯", analysis.get("objectives", [])
    )
    render_text_section(
        "Existing Approach", "📚", analysis.get("existing_approach")
    )
    render_text_section(
        "Proposed Methodology", "🧠",
        analysis.get("proposed_methodology")
    )

    dataset = analysis.get("dataset", {})
    if dataset:
        st.markdown("### 📊 Dataset")
        if isinstance(dataset, dict):
            with st.container(border=True):
                st.markdown(
                    f"**Name:** {display_value(dataset.get('name'))}"
                )
                st.markdown(
                    f"**Description:** "
                    f"{display_value(dataset.get('description'))}"
                )
                st.markdown(
                    f"**Size:** {display_value(dataset.get('size'))}"
                )
                st.markdown(
                    f"**Source:** {display_value(dataset.get('source'))}"
                )
        else:
            render_text_section("Dataset", "📊", dataset)

    render_list_section(
        "Technologies & Algorithms", "⚙️",
        analysis.get("technologies_and_algorithms", [])
    )
    render_list_section(
        "Evaluation Metrics", "📏",
        analysis.get("evaluation_metrics", [])
    )
    render_list_section(
        "Results & Findings", "📈", analysis.get("results", [])
    )
    render_list_section(
        "Advantages", "✅", analysis.get("advantages", [])
    )
    render_list_section(
        "Limitations", "⚠️", analysis.get("limitations", [])
    )
    render_text_section(
        "Research Gap", "💡", analysis.get("research_gap")
    )
    render_list_section(
        "Future Work", "🚀", analysis.get("future_work", [])
    )
    render_list_section(
        "Key Contributions", "📝",
        analysis.get("key_contributions", [])
    )

    st.divider()
    st.markdown("### 📥 Export Your Analysis")

    report = build_report(analysis, filename)
    safe_name = Path(filename).stem.replace(" ", "_")

    st.download_button(
        "⬇️ Download Analysis Report",
        data=report,
        file_name=f"{safe_name}_research_analysis.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if st.button(
        "🔄 Analyze Another Paper",
        use_container_width=True,
        key="analyze_another_paper",
    ):
        st.session_state.pop("research_doc_id", None)
        st.session_state.pop("research_opened_doc", None)
        st.session_state.pop("research_analysis", None)
        st.session_state.pop("research_filename", None)
        st.rerun()

else:
    st.markdown("### 🔎 What you can analyze")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 🔍 Research Problem")
            st.caption("Problem statement and objectives.")
        with st.container(border=True):
            st.markdown("#### 📊 Dataset & Metrics")
            st.caption("Dataset details and evaluation metrics.")
        with st.container(border=True):
            st.markdown("#### ⚠️ Limitations")
            st.caption("Constraints reported in the paper.")

    with col2:
        with st.container(border=True):
            st.markdown("#### 🧠 Methodology")
            st.caption("Methods, models and algorithms.")
        with st.container(border=True):
            st.markdown("#### 📈 Results")
            st.caption("Key findings and reported outcomes.")
        with st.container(border=True):
            st.markdown("#### 💡 Research Gap")
            st.caption("Identified gaps and open problems.")