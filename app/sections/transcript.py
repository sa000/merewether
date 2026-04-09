"""Transcript Analysis section renderer.

A grounded Q&A demo over a small library of earnings-call transcripts
stored as plain-text files under ``app/content/transcripts/``. The user
picks a ticker/quarter from a dropdown, sees a scrollable preview of
the transcript, and can either click one of four preset questions
(auto-fire) or type their own. Claude Haiku answers *only* from the
selected transcript text, and short verbatim quotes are rendered as
chips below the answer.

Mirrors the flow and session-state pattern used in
``app/sections/data_chat.py``.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app import transcript_chat
from app.sections import require_api_key
from app.style import (
    ACCENT,
    ACCENT_DIM,
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    card,
)


_TRANSCRIPTS_DIR = Path(__file__).resolve().parents[2] / "transcripts"

_PRESET_QUESTIONS = [
    "Summarize this transcript",
    "What were the key financial highlights management called out?",
    "What guidance or outlook did they give for next quarter?",
    "What was the most interesting analyst Q&A exchange?",
]

_DEFAULT_QUESTION = "Summarize this transcript"

# Friendly labels for the dropdown. Anything not in this map falls back
# to the filename stem in upper case.
_LABELS = {
    "apple": "Apple Inc. (AAPL)",
    "aapl": "Apple Inc. (AAPL)",
    "tsla": "Tesla, Inc. (TSLA)",
    "tesla": "Tesla, Inc. (TSLA)",
}


def _list_transcripts() -> list[tuple[str, Path]]:
    """Return a sorted list of ``(label, path)`` for each transcript file.

    Reads from ``<repo>/transcripts/*.txt``. Filenames map to labels via
    ``_LABELS`` (e.g. ``apple.txt`` -> ``Apple Inc. (AAPL)``); anything
    not in the map falls back to the stem in upper case so dropping new
    files in the folder just works.
    """
    if not _TRANSCRIPTS_DIR.exists():
        return []

    items: list[tuple[str, Path]] = []
    for path in sorted(_TRANSCRIPTS_DIR.glob("*.txt")):
        stem = path.stem.lower()
        label = _LABELS.get(stem, path.stem.upper())
        items.append((label, path))
    return items


def _intro() -> None:
    st.markdown(
        f"""
        <p style="color: {TEXT_PRIMARY}; font-size: 16px; line-height: 1.7;
                  margin: 0 0 1rem 0;">
            Pick an earnings-call transcript and ask Claude about it.
            The model is grounded strictly on the transcript text shown
            below — it will not pull in outside knowledge about the
            company or the quarter. Transcripts in this demo are short
            sample excerpts, clearly labeled, and stand in for the kind
            of internal corpus I would wire up against a real transcript
            provider at Merewether.
        </p>
        """,
        unsafe_allow_html=True,
    )


def _render_preset_buttons() -> None:
    # Two rows of two buttons for a tidy 2x2 grid.
    rows = [_PRESET_QUESTIONS[:2], _PRESET_QUESTIONS[2:]]
    for row_idx, row in enumerate(rows):
        cols = st.columns(len(row))
        for col, q in zip(cols, row):
            key = f"transcript_preset_{row_idx}_{hash(q) & 0xffffffff}"
            if col.button(q, key=key, use_container_width=True):
                st.session_state["transcript_question"] = q
                st.session_state["transcript_auto_run"] = True
                st.rerun()


def _render_answer(result: dict) -> None:
    answer = (result.get("answer") or "").strip()
    quotes = result.get("quotes") or []

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

    if quotes:
        chips = []
        for q in quotes:
            text = (q or "").strip().strip('"')
            if not text:
                continue
            if len(text) > 140:
                text = text[:137] + "…"
            chips.append(
                f'<span style="display: inline-block; '
                f'background: {ACCENT_DIM}; color: {ACCENT}; '
                f'padding: 4px 10px; border-radius: 12px; '
                f'font-size: 13px; font-weight: 500; '
                f'margin: 0 6px 6px 0;">&ldquo;{text}&rdquo;</span>'
            )
        if chips:
            st.markdown(
                f'<div style="margin: 0.75rem 0 0 0;">'
                f'<div style="color: {TEXT_DIM}; font-size: 12px; '
                f'text-transform: uppercase; letter-spacing: 0.06em; '
                f'margin-bottom: 0.4rem;">Supporting quotes</div>'
                f'{"".join(chips)}</div>',
                unsafe_allow_html=True,
            )


def render() -> None:
    _intro()
    api_key = require_api_key()

    transcripts = _list_transcripts()
    if not transcripts:
        st.warning(
            "No transcripts found in ``app/content/transcripts/``. "
            "Drop one or more ``<ticker>_<quarter>.txt`` files into "
            "that folder to enable this section."
        )
        return

    labels = [label for label, _ in transcripts]
    paths = {label: path for label, path in transcripts}

    selected_label = st.selectbox(
        "Transcript",
        labels,
        index=0,
        key="transcript_ticker_select",
    )
    selected_path = paths[selected_label]

    try:
        transcript_text = selected_path.read_text(encoding="utf-8")
    except OSError as e:
        st.error(f"Could not read transcript: {e}")
        return

    st.text_area(
        "Transcript preview",
        value=transcript_text,
        height=240,
        key=f"transcript_preview_{selected_path.stem}",
        disabled=True,
    )

    # Pop the auto-run flag set by a preset button click on the previous run.
    auto_run = st.session_state.pop("transcript_auto_run", False)

    _render_preset_buttons()

    default = st.session_state.get("transcript_question", _DEFAULT_QUESTION)
    question = st.text_area(
        "Your question",
        value=default,
        height=100,
        key="transcript_textarea",
        label_visibility="collapsed",
    )

    submit = st.button(
        "Ask",
        type="primary",
        disabled=(api_key is None or not question.strip()),
        key="transcript_submit",
    )

    if (submit or auto_run) and api_key and question.strip():
        with st.spinner("Reading the transcript…"):
            result = transcript_chat.ask(
                question=question.strip(),
                transcript_text=transcript_text,
                label=selected_label,
                api_key=api_key,
            )
        _render_answer(result)
