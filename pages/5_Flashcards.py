"""Flashcards page - flip, shuffle, navigate. Reads only from SQLite."""
import sys
import random
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.helpers import page_header, no_document_warning


def _init_order(doc_id: str, n: int) -> list:
    """Return current card order; reset when document changes."""
    if st.session_state.get("fc_doc_id") != doc_id:
        st.session_state.fc_doc_id = doc_id
        st.session_state.fc_order = list(range(n))
        st.session_state.fc_shuffled = False
        st.session_state.card_index = 0
        st.session_state.card_flipped = False
    return st.session_state.fc_order


def _shuffle(n: int) -> None:
    order = list(range(n))
    random.shuffle(order)
    st.session_state.fc_order = order
    st.session_state.fc_shuffled = True
    st.session_state.card_index = 0
    st.session_state.card_flipped = False


def _reset_order(n: int) -> None:
    st.session_state.fc_order = list(range(n))
    st.session_state.fc_shuffled = False
    st.session_state.card_index = 0
    st.session_state.card_flipped = False


def _card_html(card: dict, flipped: bool, pos: int, total: int) -> str:
    if flipped:
        card_class = "flashcard is-back"
        side_tag = "Back · Definition"
        content = card.get("back", "")
    else:
        card_class = "flashcard is-front"
        side_tag = "Front · Term"
        content = card.get("front", "")

    return dedent(
        f"""
    <div class="flashcard-container">
        <div class="{card_class}">
            <div class="flashcard-side-tag">{side_tag}</div>
            <div class="flashcard-text">{content}</div>
        </div>
        <div class="flashcard-progress">Card {pos + 1} of {total}</div>
    </div>
    """
    ).strip()


def _render_controls(total: int, shuffled: bool) -> None:
    idx = st.session_state.card_index

    c_prev, c_flip, c_next = st.columns([1, 2, 1])
    with c_prev:
        if st.button("← Prev", use_container_width=True, disabled=(idx == 0)):
            st.session_state.card_index = idx - 1
            st.session_state.card_flipped = False
            st.rerun()
    with c_flip:
        label = "👁  Show Term" if st.session_state.card_flipped else "🔄  Flip to Definition"
        if st.button(label, use_container_width=True):
            st.session_state.card_flipped = not st.session_state.card_flipped
            st.rerun()
    with c_next:
        if st.button("Next →", use_container_width=True, disabled=(idx >= total - 1)):
            st.session_state.card_index = idx + 1
            st.session_state.card_flipped = False
            st.rerun()

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    c_shuffle, c_reset, _ = st.columns([1, 1, 3])
    with c_shuffle:
        if st.button("🔀  Shuffle", use_container_width=True, disabled=shuffled):
            _shuffle(total)
            st.rerun()
    with c_reset:
        if st.button("↺  Reset Order", use_container_width=True, disabled=not shuffled):
            _reset_order(total)
            st.rerun()


def _render_flashcards(doc: dict) -> None:
    page_header("🃏  Flashcards", f"Review key terms · {doc['filename']}")

    cards = doc.get("flashcards", [])
    if not cards:
        st.warning("No flashcards found for this document.")
        return

    total = len(cards)
    order = _init_order(doc["id"], total)
    idx = min(st.session_state.card_index, total - 1)
    st.session_state.card_index = idx

    real_idx = order[idx]
    shuffled = st.session_state.fc_shuffled

    st.markdown(
        _card_html(cards[real_idx], st.session_state.card_flipped, idx, total),
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    _render_controls(total, shuffled)

    st.markdown("<br>", unsafe_allow_html=True)
    st.progress((idx + 1) / total)

    shuffle_label = "· Shuffled" if shuffled else ""
    st.markdown(
        (
            f'<div class="info-tip centered">'
            f"{idx + 1}/{total} cards &nbsp;{shuffle_label}</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔢  Jump to card"):
        target = st.number_input("Card number", min_value=1, max_value=total, value=idx + 1, step=1)
        if st.button("Go", key="fc_go"):
            st.session_state.card_index = int(target) - 1
            st.session_state.card_flipped = False
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(f"📋  All {total} flashcards"):
        cards_html = "".join(
            dedent(
                f"""
            <div class="flashcard-list-row">
                <div class="card-index">#{pos}</div>
                <div class="flashcard-front">{cards[real_i].get("front", "")}</div>
                <div class="flashcard-back">{cards[real_i].get("back", "")}</div>
            </div>
            """
            ).strip()
            for pos, real_i in enumerate(order, 1)
        )
        st.markdown(f'<div class="flashcard-list">{cards_html}</div>', unsafe_allow_html=True)


doc = st.session_state.get("current_doc")
if not doc:
    page_header("🃏  Flashcards")
    no_document_warning()
else:
    _render_flashcards(doc)
