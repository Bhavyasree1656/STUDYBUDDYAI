
"""Quiz page - one question at a time with immediate feedback."""

import sys
from pathlib import Path
from textwrap import dedent
from html import escape

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.helpers import page_header, no_document_warning


def _init_state(doc_id: str) -> None:
    """Reset quiz state when the document changes."""
    if st.session_state.get("quiz_doc_id") != doc_id:
        st.session_state.quiz_doc_id = doc_id
        st.session_state.quiz_current_q = 0
        st.session_state.quiz_scores = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_finished = False
        st.session_state.quiz_revealed = set()


def _reset_quiz(doc_id: str) -> None:
    st.session_state.quiz_doc_id = doc_id
    st.session_state.quiz_current_q = 0
    st.session_state.quiz_scores = {}
    st.session_state.quiz_answers = {}
    st.session_state.quiz_finished = False
    st.session_state.quiz_revealed = set()


def _score_tone(pct: int) -> tuple[str, str]:
    if pct >= 80:
        return "tone-high", "Excellent! 🎉"
    if pct >= 60:
        return "tone-mid", "Good job! 👍"
    return "tone-low", "Keep practising! 💪"


def _answer_feedback(question: dict, selected: str | None) -> None:
    """Show feedback immediately after an option is selected."""
    if selected is None:
        return

    correct = question.get("answer", "")
    explanation = question.get("explanation", "")

    if selected == correct:
        st.success("✅ Correct answer! Well done.")
    else:
        st.error("❌ Incorrect answer.")

    with st.container(border=True):
        st.markdown(f"**Correct answer:** {correct}")

        if explanation:
            st.markdown(f"**Explanation:** {explanation}")


def _review_card(
    idx: int,
    question: dict,
    is_correct,
    user_ans: str,
    correct_ans: str,
) -> str:
    if is_correct is True:
        status_class = "review-card is-correct"
        status_text = f"✅ &nbsp;Q{idx + 1}"
        answer_line = (
            f'Your answer: <span class="answer-correct">'
            f'{escape(str(user_ans))}</span>'
        )
    elif is_correct is False:
        status_class = "review-card is-incorrect"
        status_text = f"❌ &nbsp;Q{idx + 1}"
        answer_line = (
            f'Your answer: <span class="answer-incorrect">'
            f'{escape(str(user_ans or "—"))}</span>'
            f' &nbsp;·&nbsp; Correct: '
            f'<span class="answer-correct">'
            f'{escape(str(correct_ans))}</span>'
        )
    else:
        status_class = "review-card is-unanswered"
        status_text = f"⏭️ &nbsp;Q{idx + 1}"
        answer_line = (
            'Your answer: <span class="answer-incorrect">—</span>'
            f' &nbsp;·&nbsp; Correct: '
            f'<span class="answer-correct">'
            f'{escape(str(correct_ans))}</span>'
        )

    return dedent(
        f"""
        <div class="{status_class}">
            <div class="review-status">{status_text}</div>
            <div class="review-question">
                {escape(str(question.get("question", "")))}
            </div>
            <div class="review-answer">{answer_line}</div>
        </div>
        """
    ).strip()


def _render_score_screen(questions: list, doc_id: str) -> None:
    total = len(questions)
    score = sum(
        1 for value in st.session_state.quiz_scores.values() if value
    )
    pct = round(score / total * 100) if total else 0
    tone_class, grade = _score_tone(pct)

    st.markdown(
        dedent(
            f"""
            <div class="score-banner {tone_class}">
                <div class="score-value">
                    {score}<span class="score-total">/{total}</span>
                </div>
                <div class="score-grade">{grade}</div>
                <div class="score-label">{pct}% correct</div>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    col_restart, col_review, _ = st.columns([1, 1, 3])

    with col_restart:
        if st.button("🔄 Restart Quiz", use_container_width=True):
            _reset_quiz(doc_id)
            st.rerun()

    with col_review:
        if st.button("📋 Review Answers", use_container_width=True):
            st.session_state.quiz_finished = False
            st.session_state.quiz_current_q = 0
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">Question breakdown</div>',
        unsafe_allow_html=True,
    )

    cards_html = "".join(
        _review_card(
            idx,
            question,
            st.session_state.quiz_scores.get(idx),
            st.session_state.quiz_answers.get(idx, "—"),
            question.get("answer", ""),
        )
        for idx, question in enumerate(questions)
    )

    st.markdown(
        f'<div class="review-list">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def _render_question(questions: list) -> None:
    idx = st.session_state.quiz_current_q
    question = questions[idx]
    total = len(questions)

    options = question.get("options", [])
    correct = question.get("answer", "")

    if not isinstance(options, list) or not options:
        st.warning("No answer options are available for this question.")
        return

    # A question becomes locked after clicking Next.
    revealed_questions = st.session_state.quiz_revealed
    revealed = idx in revealed_questions
    user_ans = st.session_state.quiz_answers.get(idx)

    answered_count = len(st.session_state.quiz_scores)

    st.progress(answered_count / total if total else 0)

    st.markdown(
        (
            '<div class="info-tip between">'
            f'<span>Question {idx + 1} of {total}</span>'
            f'<span>{answered_count} answered</span>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    card_class = ""
    if revealed:
        card_class = (
            "correct"
            if st.session_state.quiz_scores.get(idx, False)
            else "incorrect"
        )

    st.markdown(
        dedent(
            f"""
            <div class="quiz-question-card {card_class}">
                <div class="question-number">Question {idx + 1}</div>
                <div class="question-text">
                    {escape(str(question.get("question", "")))}
                </div>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    # Keep the answer selection separate for every question.
    radio_key = f"radio_{st.session_state.quiz_doc_id}_{idx}"

    if radio_key not in st.session_state:
        st.session_state[radio_key] = user_ans

    selected = st.radio(
        "Choose your answer",
        options=options,
        index=None,
        key=radio_key,
        disabled=revealed,
        label_visibility="collapsed",
    )

    if selected is not None and not revealed:
        st.session_state.quiz_answers[idx] = selected
        user_ans = selected

        # Immediate feedback on selection.
        _answer_feedback(question, selected)

    elif revealed:
        # Keep feedback visible when returning to an answered question.
        _answer_feedback(question, user_ans)

    st.markdown("<br>", unsafe_allow_html=True)

    # Only Prev and Next buttons; no Reveal Answer button.
    col_prev, _, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.button(
            "← Prev",
            key=f"prev_{idx}",
            use_container_width=True,
            disabled=(idx == 0),
        ):
            st.session_state.quiz_current_q = idx - 1
            st.rerun()

    with col_next:
        is_last = idx == total - 1
        label = "🏁 Finish" if is_last else "Next →"

        if st.button(
            label,
            key=f"next_{idx}",
            use_container_width=True,
            disabled=(not user_ans),
        ):
            # Save the result when moving forward.
            st.session_state.quiz_scores[idx] = user_ans == correct
            st.session_state.quiz_revealed.add(idx)

            if is_last:
                st.session_state.quiz_finished = True
            else:
                st.session_state.quiz_current_q = idx + 1

            st.rerun()


def _render_quiz(doc: dict) -> None:
    page_header("🧠 Quiz", f"One question at a time · {doc['filename']}")

    questions = doc.get("quiz", [])

    if not questions:
        st.warning("No quiz data found for this document.")
        return

    _init_state(str(doc["id"]))

    if st.session_state.quiz_finished:
        _render_score_screen(questions, str(doc["id"]))
    else:
        _render_question(questions)


doc = st.session_state.get("current_doc")

if st.button("← Back to Learning Hub", key="quiz_back"):
    st.switch_page("pages/1_Home.py")

if not doc:
    page_header("🧠 Quiz")
    no_document_warning()
else:
    _render_quiz(doc)
