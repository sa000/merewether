"""Transcript Analysis section renderer.

A grounded Q&A demo over a small library of earnings-call transcripts
stored as plain-text files under ``app/content/transcripts/``. The user
picks a transcript from a dropdown, sees a scrollable read-only preview,
and either clicks one of four preset questions (auto-fire) or types
their own. Claude Haiku answers *only* from the selected transcript
text.

Mirrors the flow and session-state pattern used in
``app/sections/data_chat.py`` (including the preset-button rerun-and-
auto-run fix).
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from app import transcript_chat
from app.sections import require_api_key
from app.sections.narrative import render_content
from app.style import (
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    card,
)


_TRANSCRIPTS_DIR = (
    Path(__file__).resolve().parents[1] / "content" / "transcripts"
)

_PRESET_QUESTIONS = [
    "Summarize the call in 5 bullets",
    "Was the tone bullish or bearish?",
    "What are the key risks management discussed?",
    "What forward guidance did management give?",
]

_DEFAULT_QUESTION = _PRESET_QUESTIONS[0]

_PREVIEW_CHARS = 3000

# Mapping of ticker symbol -> friendly company name for the dropdown
# label. Anything not in this map falls back to the bare ticker.
_COMPANY_NAMES = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "META": "Meta",
    "AMZN": "Amazon",
    "NVDA": "Nvidia",
}


# ---------------------------------------------------------------------------
# Filename + header parsing
# ---------------------------------------------------------------------------
def _parse_filename(path: Path) -> tuple[str, str]:
    """Parse ``aapl_2023q4.txt`` -> ``("AAPL", "Apple Q4 2023 earnings call")``.

    Unrecognized patterns fall back to the filename stem in upper case
    so dropping any ``*.txt`` file into the folder still yields a usable
    dropdown entry.
    """
    stem = path.stem
    m = re.match(r"^([a-zA-Z]+)[_\-](\d{4})[qQ]([1-4])$", stem)
    if not m:
        return stem.upper(), stem.upper()

    ticker = m.group(1).upper()
    year = m.group(2)
    quarter = m.group(3)
    company = _COMPANY_NAMES.get(ticker, ticker)
    label = f"{company} Q{quarter} {year} earnings call"
    return ticker, label


def _parse_header(text: str) -> dict:
    """Extract ``Source``, ``Company``, ``Quarter`` from a 5-line header.

    Each header line looks like ``# Key: value`` (the leading ``#`` and
    optional whitespace are tolerated). Only the first ~10 lines are
    scanned so header parsing stays cheap even if somebody drops a very
    large file in. Missing keys simply come back as empty strings.
    """
    out = {"source": "", "company": "", "quarter": "", "disclaimer": ""}
    for raw_line in text.splitlines()[:10]:
        line = raw_line.lstrip("#").strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key in out and value:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def _list_transcripts() -> list[tuple[str, str, Path]]:
    """Return a sorted list of ``(ticker, label, path)`` per transcript.

    Reads from ``app/content/transcripts/*.txt``. The sort key is the
    filename stem so the order is stable across reloads.
    """
    if not _TRANSCRIPTS_DIR.exists():
        return []

    items: list[tuple[str, str, Path]] = []
    for path in sorted(_TRANSCRIPTS_DIR.glob("*.txt")):
        ticker, label = _parse_filename(path)
        items.append((ticker, label, path))
    return items


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def _render_metadata(header: dict) -> None:
    company = header.get("company") or ""
    quarter = header.get("quarter") or ""
    source = header.get("source") or ""

    parts = []
    if company:
        parts.append(company)
    if quarter:
        parts.append(quarter)
    if source:
        parts.append(f'<a href="{source}" target="_blank">source</a>')

    if not parts:
        return

    st.markdown(
        f'<div style="color: {TEXT_DIM}; font-size: 13px; '
        f'margin: 0 0 0.5rem 0;">{" &middot; ".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_preset_buttons() -> None:
    cols = st.columns(len(_PRESET_QUESTIONS))
    for col, q in zip(cols, _PRESET_QUESTIONS):
        key = f"transcript_preset_{hash(q) & 0xffffffff}"
        if col.button(q, key=key, use_container_width=True):
            st.session_state["transcript_question"] = q
            st.session_state["transcript_auto_run"] = True
            st.rerun()


def _render_answer(result: dict) -> None:
    answer = (result.get("answer") or "").strip()
    if not answer:
        st.info("No answer was returned.")
        return

    # The transcript text may contain newlines the model echoes back. We
    # convert them to <br> so paragraphs render readably inside the card.
    safe = answer.replace("\n\n", "<br><br>").replace("\n", "<br>")

    st.markdown(
        card(
            f'<p style="color: {TEXT_PRIMARY}; font-size: 16px; '
            f'line-height: 1.7; margin: 0;">{safe}</p>'
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render() -> None:
    render_content("transcript_analysis.md")

    # Pop the auto-run flag FIRST, at the very top of the render, so a
    # preset button click on the previous run becomes a synthetic submit
    # on this run. This mirrors the data_chat auto-fire fix.
    auto_run = st.session_state.pop("transcript_auto_run", False)

    api_key = require_api_key()

    transcripts = _list_transcripts()
    if not transcripts:
        st.warning(
            "No transcripts found in ``app/content/transcripts/``. "
            "Drop one or more ``<ticker>_<year>q<quarter>.txt`` files "
            "into that folder to enable this section."
        )
        return

    # Dropdown of labels; keep a lookup back to (ticker, path).
    labels = [label for _ticker, label, _path in transcripts]
    by_label = {
        label: (ticker, path) for ticker, label, path in transcripts
    }

    selected_label = st.selectbox(
        "Transcript",
        labels,
        index=0,
        key="transcript_select",
    )
    _ticker, selected_path = by_label[selected_label]

    try:
        transcript_text = selected_path.read_text(encoding="utf-8")
    except OSError as e:
        st.error(f"Could not read transcript: {e}")
        return

    header = _parse_header(transcript_text)
    _render_metadata(header)

    # Read-only scrollable preview; cap at _PREVIEW_CHARS so a 50 kb
    # transcript does not dominate the page layout.
    preview = transcript_text[:_PREVIEW_CHARS]
    if len(transcript_text) > _PREVIEW_CHARS:
        preview = preview.rstrip() + "\n\n[…truncated preview — full transcript is still used for Q&A…]"

    st.text_area(
        "Transcript preview",
        value=preview,
        height=240,
        disabled=True,
        label_visibility="collapsed",
        key=f"transcript_preview_{selected_path.stem}",
    )

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
                transcript_text=transcript_text,
                question=question.strip(),
                api_key=api_key,
            )
        _render_answer(result)
