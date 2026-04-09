"""AI Data Chat section renderer.

A natural-language Q&A box over the inventory. The user types a
question, Claude Haiku answers in JSON with a short text answer plus
a list of relevant inventory keys. The text answer is rendered in a
card; the keys become small chips below.
"""

from __future__ import annotations

import streamlit as st

from app import data_chat
from app.data_sources import INVENTORY, build_inventory_text
from app.sections import require_api_key
from app.style import (
    ACCENT,
    ACCENT_DIM,
    BG_CARD_SOLID,
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card,
)


_DEFAULT_QUESTION = "What data is available in this app, and what kind of questions can I answer with it?"
_PRESET_QUESTIONS = [
    "Which sources cover macro economic data?",
    "What's the difference between the equity and futures data here?",
    "If I wanted to research US inflation, what would I use?",
]


def _intro() -> None:
    st.markdown(
        f"""
        <p style="color: {TEXT_PRIMARY}; font-size: 16px; line-height: 1.7;
                  margin: 0 0 1rem 0;">
            Ask Claude what data is available in this app. The model is
            grounded only on the inventory below — it cannot make up
            sources that don't exist. This is a stand-in for the kind
            of internal Q&A I would build over Merewether's actual data
            catalog: an analyst should never have to remember where a
            field lives.
        </p>
        """,
        unsafe_allow_html=True,
    )


def _render_preset_buttons() -> None:
    cols = st.columns(len(_PRESET_QUESTIONS))
    for col, q in zip(cols, _PRESET_QUESTIONS):
        if col.button(q, key=f"preset_{hash(q) & 0xffffffff}", use_container_width=True):
            st.session_state["data_chat_question"] = q
            st.session_state["data_chat_auto_run"] = True
            st.rerun()


def _render_answer(result: dict) -> None:
    answer = (result.get("answer") or "").strip()
    sources = result.get("sources") or []

    if not answer:
        st.info("No answer was returned.")
        return

    st.markdown(
        card(
            f'<p style="color: {TEXT_PRIMARY}; font-size: 16px; '
            f'line-height: 1.7; margin: 0;">{answer}</p>'
        ),
        unsafe_allow_html=True,
    )

    if sources:
        chips = []
        for s in sources:
            label = s.get("label") or s.get("key") or "source"
            chips.append(
                f'<span style="display: inline-block; '
                f'background: {ACCENT_DIM}; color: {ACCENT}; '
                f'padding: 4px 10px; border-radius: 12px; '
                f'font-size: 13px; font-weight: 500; '
                f'margin: 0 6px 6px 0;">{label}</span>'
            )
        st.markdown(
            f'<div style="margin: 0.75rem 0 0 0;">'
            f'<div style="color: {TEXT_DIM}; font-size: 12px; '
            f'text-transform: uppercase; letter-spacing: 0.06em; '
            f'margin-bottom: 0.4rem;">Relevant sources</div>'
            f'{"".join(chips)}</div>',
            unsafe_allow_html=True,
        )


def render() -> None:
    _intro()
    api_key = require_api_key()

    # Pop the auto-run flag set by a preset button click on the previous run.
    auto_run = st.session_state.pop("data_chat_auto_run", False)

    _render_preset_buttons()

    default = st.session_state.get("data_chat_question", _DEFAULT_QUESTION)
    question = st.text_area(
        "Your question",
        value=default,
        height=100,
        key="data_chat_textarea",
        label_visibility="collapsed",
    )

    submit = st.button(
        "Ask",
        type="primary",
        disabled=(api_key is None or not question.strip()),
        key="data_chat_submit",
    )

    if (submit or auto_run) and api_key and question.strip():
        with st.spinner("Thinking…"):
            result = data_chat.ask(
                question=question.strip(),
                inventory_text=build_inventory_text(INVENTORY),
                api_key=api_key,
            )
        _render_answer(result)
