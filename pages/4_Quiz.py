"""Quiz page - one question at a time, reveal-then-navigate flow. Reads only from SQLite."""
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.helpers import page_header, no_document_warning


def _init_state(doc_id: str) -> None:
    """Reset all quiz state when the document changes."""
    if st.session_state.get("quiz_doc_id") != doc_id:
        st.session_state.quiz_doc_id = doc_id
        st.session_state.quiz_current_q = 0
        st.session_state.quiz_scores = {}
        st.session_state.quiz_answers = {}
        st.session_state.quiz_finished = False


def _reset_quiz(doc_id: str) -> None:
    st.session_state.quiz_doc_id = doc_id
    st.session_state.quiz_current_q = 0
    st.session_state.quiz_scores = {}
    st.session_state.quiz_answers = {}
    st.session_state.quiz_finished = False


def _score_tone(pct: int) -> tuple[str, str]:
    if pct >= 80:
        return "tone-high", "Excellent! 🎉"
    if pct >= 60:
        return "tone-mid", "Good job! 👍"
    return "tone-low", "Keep practising! 💪"


def _review_card(idx: int, question: dict, is_correct, user_ans: str, correct_ans: str) -> str:
    if is_correct is True:
        status_class = "review-card is-correct"
        status_text = f"✅ &nbsp;Q{idx + 1}"
        answer_line = f'Your answer: <span class="answer-correct">{user_ans}</span>'
    elif is_correct is False:
        status_class = "review-card is-incorrect"
        status_text = f"❌ &nbsp;Q{idx + 1}"
        answer_line = (
            f'Your answer: <span class="answer-incorrect">{user_ans}</span>'
            f" &nbsp;·&nbsp; Correct: <span class=\"answer-correct\">{correct_ans}</span>"
        )
    else:
        status_class = "review-card is-unanswered"
        status_text = f"⏭️ &nbsp;Q{idx + 1}"
        answer_line = f'Your answer: <span class="answer-incorrect">—</span>'

    return dedent(
        f"""
    <div class="{status_class}">
        <div class="review-status">{status_text}</div>
        <div class="review-question">{question["question"]}</div>
        <div class="review-answer">{answer_line}</div>
    </div>
    """
    ).strip()


def _render_score_screen(questions: list, doc_id: str) -> None:
    total = len(questions)
    score = sum(1 for value in st.session_state.quiz_scores.values() if value)
    pct = round(score / total * 100) if total else 0
    tone_class, grade = _score_tone(pct)

    st.markdown(
        dedent(
            f"""
        <div class="score-banner {tone_class}">
            <div class="score-value">
                {score}
                <span class="score-total">/{total}</span>
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
        if st.button("🔄  Restart Quiz", use_container_width=True):
            _reset_quiz(doc_id)
            st.rerun()
    with col_review:
        if st.button("📋  Review Answers", use_container_width=True):
            st.session_state.quiz_finished = False
            st.session_state.quiz_current_q = 0
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Question breakdown</div>', unsafe_allow_html=True)

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
    st.markdown(f'<div class="review-list">{cards_html}</div>', unsafe_allow_html=True)


def _render_question(questions: list) -> None:
    idx = st.session_state.quiz_current_q
    question = questions[idx]
    total = len(questions)
    options = question.get("options", [])
    correct = question.get("answer", "")

    revealed = idx in st.session_state.quiz_scores
    user_ans = st.session_state.quiz_answers.get(idx)
    is_correct = st.session_state.quiz_scores.get(idx, False)

    answered_count = len(st.session_state.quiz_scores)
    st.progress(answered_count / total if total else 0)
    st.markdown(
        (
            f'<div class="info-tip between">'
            f"<span>Question {idx + 1} of {total}</span>"
            f"<span>{answered_count} answered</span></div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    card_class = ""
    if revealed:
        card_class = "correct" if is_correct else "incorrect"

    st.markdown(
        dedent(
            f"""
        <div class="quiz-question-card {card_class}">
            <div class="question-number">Question {idx + 1}</div>
            <div class="question-text">{question["question"]}</div>
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )

    selected = st.radio(
        f"q{idx}",
        options=options,
        index=options.index(user_ans) if user_ans in options else None,
        disabled=revealed,
        label_visibility="collapsed",
        key=f"radio_{idx}",
    )
    if selected and not revealed:
        st.session_state.quiz_answers[idx] = selected

    st.markdown("<br>", unsafe_allow_html=True)

    if not revealed:
        col_reveal, _, col_prev = st.columns([1, 4, 1])
        with col_reveal:
            if st.button("🔍  Reveal Answer", use_container_width=True):
                ans = st.session_state.quiz_answers.get(idx)
                st.session_state.quiz_scores[idx] = bool(ans) and (ans == correct)
                st.rerun()
        with col_prev:
            if st.button("← Prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state.quiz_current_q = idx - 1
                st.rerun()

    else:
        ans = st.session_state.quiz_answers.get(idx, "")
        if is_correct:
            explanation_html = (
                f'<div class="quiz-explanation is-correct">✅ <strong>Correct!</strong> '
                f'{question.get("explanation", "")}</div>'
            )
        elif ans:
            explanation_html = (
                f'<div class="quiz-explanation is-incorrect">'
                f'❌ <strong>Correct answer:</strong> {correct}<br>'
                f'{question.get("explanation", "")}</div>'
            )
        else:
            explanation_html = (
                f'<div class="quiz-explanation is-skipped">'
                f'⏭️ <strong>Skipped.</strong> Correct answer: {correct}<br>'
                f'{question.get("explanation", "")}</div>'
            )
        st.markdown(explanation_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        is_last = idx == total - 1
        col_prev, _, col_next = st.columns([1, 4, 1])
        with col_prev:
            if st.button("← Prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state.quiz_current_q = idx - 1
                st.rerun()
        with col_next:
            label = "🏁  Finish" if is_last else "Next →"
            if st.button(label, use_container_width=True):
                if is_last:
                    st.session_state.quiz_finished = True
                else:
                    st.session_state.quiz_current_q = idx + 1
                st.rerun()


def _render_quiz(doc: dict) -> None:
    page_header("🧠  Quiz", f"One question at a time · {doc['filename']}")

    questions = doc.get("quiz", [])
    if not questions:
        st.warning("No quiz data found for this document.")
        return

    doc_id = doc["id"]
    _init_state(doc_id)

    if st.session_state.quiz_finished:
        _render_score_screen(questions, doc_id)
    else:
        _render_question(questions)


doc = st.session_state.get("current_doc")
if not doc:
    page_header("🧠  Quiz")
    no_document_warning()
else:
    _render_quiz(doc)
