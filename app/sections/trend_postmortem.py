"""AI Trend Post-Mortem section renderer.

The user picks an asset (Apple or corn futures), a date window, and
an optional question, and Claude Haiku with web search returns a
narrative explaining what drove the price move during that window.
Pre-filled buttons set the asset + window + question in one click.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from app import trend_analyst
from app.data_sources import INVENTORY
from app.sections import require_api_key
from app.style import (
    ACCENT,
    BG_CARD_SOLID,
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card,
)


# Only the yfinance-backed assets are eligible for trend post-mortem;
# macro series don't have web-searchable price stories.
_ELIGIBLE_KEYS = [k for k, v in INVENTORY.items() if v["source"] == "yahoo"]


_PRESETS = [
    {
        "label": "Why did Apple drop sharply in October 2023?",
        "asset": "AAPL",
        "start": date(2023, 9, 1),
        "end": date(2023, 11, 1),
        "question": (
            "Why did Apple stock drop sharply between September and "
            "early November 2023?"
        ),
    },
    {
        "label": "What drove corn higher in summer 2022?",
        "asset": "ZC=F",
        "start": date(2022, 4, 1),
        "end": date(2022, 7, 1),
        "question": (
            "What drove corn futures to a multi-year high in the spring "
            "and early summer of 2022?"
        ),
    },
    {
        "label": "Corn during the 2012 US drought",
        "asset": "ZC=F",
        "start": date(2012, 6, 1),
        "end": date(2012, 9, 1),
        "question": (
            "What happened to corn futures during the 2012 US drought, "
            "and how did the USDA describe the damage?"
        ),
    },
    {
        "label": "Why did Apple rally in early 2024?",
        "asset": "AAPL",
        "start": date(2024, 1, 1),
        "end": date(2024, 4, 1),
        "question": (
            "Why did Apple rally between January and early April 2024?"
        ),
    },
]


def _intro() -> None:
    st.markdown(
        f"""
        <p style="color: {TEXT_PRIMARY}; font-size: 16px; line-height: 1.7;
                  margin: 0 0 1rem 0;">
            Pick a name and a window. Claude searches the public web,
            collects the news and reports that explain the move, and
            returns a brief with inline citations. Same shape as a
            quick research note an analyst might pull together
            manually — except the model has already done the search,
            so the analyst gets to start from a draft.
        </p>
        """,
        unsafe_allow_html=True,
    )


def _apply_preset(idx: int) -> None:
    p = _PRESETS[idx]
    st.session_state["trend_asset"] = p["asset"]
    st.session_state["trend_start"] = p["start"]
    st.session_state["trend_end"] = p["end"]
    st.session_state["trend_question"] = p["question"]


def _render_presets() -> None:
    st.markdown(
        f'<div style="color: {TEXT_DIM}; font-size: 12px; '
        f'text-transform: uppercase; letter-spacing: 0.06em; '
        f'margin: 0 0 0.5rem 0;">Try one of these</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, preset in enumerate(_PRESETS):
        col = cols[i % 2]
        if col.button(
            preset["label"],
            key=f"trend_preset_{i}",
            use_container_width=True,
        ):
            _apply_preset(i)
            st.rerun()


def _render_form() -> tuple[str, date, date, str, bool]:
    asset_default = st.session_state.get("trend_asset", _ELIGIBLE_KEYS[0])
    if asset_default not in _ELIGIBLE_KEYS:
        asset_default = _ELIGIBLE_KEYS[0]

    start_default = st.session_state.get("trend_start", date(2023, 9, 1))
    end_default = st.session_state.get("trend_end", date(2023, 11, 1))
    question_default = st.session_state.get(
        "trend_question",
        "Why did this asset move during the selected window?",
    )

    asset_key = st.selectbox(
        "Asset",
        _ELIGIBLE_KEYS,
        index=_ELIGIBLE_KEYS.index(asset_default),
        format_func=lambda k: INVENTORY[k]["label"],
        key="trend_asset_select",
    )

    c1, c2 = st.columns(2)
    start = c1.date_input("Window start", value=start_default, key="trend_start_picker")
    end = c2.date_input("Window end", value=end_default, key="trend_end_picker")

    question = st.text_area(
        "Question (optional context for the model)",
        value=question_default,
        height=80,
        key="trend_question_textarea",
    )

    api_key = require_api_key()
    submit = st.button(
        "Run post-mortem",
        type="primary",
        disabled=(api_key is None or start >= end),
        key="trend_submit",
    )
    return asset_key, start, end, question, submit


def _render_result(result: dict) -> None:
    if result.get("error"):
        st.error(result["error"])
        return

    sections = result.get("sections") or {}
    section_citations = result.get("section_citations") or {}
    citations = result.get("citations") or []
    summary = result.get("price_summary") or {}

    if summary:
        cols = st.columns(5)
        labels = [
            ("Start", summary.get("start_price"), "n"),
            ("End", summary.get("end_price"), "n"),
            ("Change", summary.get("pct_change"), "p"),
            ("Peak", summary.get("peak"), "n"),
            ("Trough", summary.get("trough"), "n"),
        ]
        for col, (lbl, val, kind) in zip(cols, labels):
            if val is None:
                col.metric(lbl, "—")
            elif kind == "p":
                col.metric(lbl, f"{val:+.2f}%")
            else:
                col.metric(lbl, f"{val:,.2f}")

    if not sections:
        narrative = result.get("narrative") or "(no narrative returned)"
        st.markdown(
            card(
                f'<p style="color: {TEXT_PRIMARY}; font-size: 16px; '
                f'line-height: 1.7; margin: 0; white-space: pre-wrap;">'
                f'{narrative}</p>'
            ),
            unsafe_allow_html=True,
        )
        return

    # Render preamble first if present
    if "_preamble" in sections:
        st.markdown(sections["_preamble"])

    for key in [k for k in sections if k != "_preamble"]:
        st.markdown(f"### {key}")
        st.markdown(sections[key])
        sect_cites = section_citations.get(key) or []
        if sect_cites:
            cite_html_parts = []
            for c in sect_cites[:5]:
                cite_html_parts.append(
                    f'<a href="{c["url"]}" target="_blank" '
                    f'style="display: inline-block; color: {ACCENT}; '
                    f'font-size: 13px; padding: 3px 9px; margin: 0 6px 6px 0; '
                    f'border: 1px solid {BORDER}; border-radius: 12px; '
                    f'text-decoration: none;">{c["title"][:80]}</a>'
                )
            st.markdown(
                "".join(cite_html_parts),
                unsafe_allow_html=True,
            )

    if citations:
        with st.expander(f"All sources ({len(citations)})"):
            for c in citations:
                st.markdown(f"- [{c['title']}]({c['url']})")


def render() -> None:
    _intro()
    _render_presets()
    asset_key, start, end, question, submit = _render_form()

    if submit:
        api_key = require_api_key()
        if api_key is None:
            return
        if start >= end:
            st.error("Window start must be before window end.")
            return

        # Stash the question into the user message via the SDK wrapper.
        # The SDK function builds its own context from numeric anchors;
        # we append the user question for clarity.
        with st.spinner("Researching with Claude (this may take 20-40 seconds)…"):
            result = trend_analyst.analyze_trend(
                asset_key=asset_key,
                start=start,
                end=end,
                api_key=api_key,
            )
        _render_result(result)
