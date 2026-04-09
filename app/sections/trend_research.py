"""Trend Research section renderer.

Two hardcoded research examples with web search. Click an example to
automatically run the analysis and see what drove the price move during
that window. Each example demonstrates different data points and
narratives to show the range of what's possible.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from app import trend_analyst
from app.sections import require_api_key
from app.sections.narrative import render_content
from app.style import (
    ACCENT,
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    card,
)


_PRESETS = [
    {
        "label": "Why did Apple drop sharply in October 2023?",
        "asset": "AAPL",
        "start": date(2023, 9, 1),
        "end": date(2023, 11, 1),
    },
    {
        "label": "What drove corn futures higher in summer 2022?",
        "asset": "ZC=F",
        "start": date(2022, 4, 1),
        "end": date(2022, 7, 1),
    },
]


def _render_presets() -> None:
    cols = st.columns(2)
    for i, preset in enumerate(_PRESETS):
        col = cols[i % 2]
        if col.button(
            preset["label"],
            key=f"trend_preset_{i}",
            use_container_width=True,
        ):
            st.session_state["trend_pending_asset"] = preset["asset"]
            st.session_state["trend_pending_start"] = preset["start"]
            st.session_state["trend_pending_end"] = preset["end"]
            st.session_state["trend_auto_run"] = True
            st.rerun()


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
    render_content("trend_research.md")

    # Pop the auto-run flag set by a preset button click on the previous run.
    auto_run = st.session_state.pop("trend_auto_run", False)

    _render_presets()

    # Pop pending state values set by a preset click
    asset = st.session_state.pop("trend_pending_asset", None)
    start = st.session_state.pop("trend_pending_start", None)
    end = st.session_state.pop("trend_pending_end", None)

    if (auto_run or asset is not None) and asset and start and end:
        api_key = require_api_key()
        if api_key is None:
            return

        with st.spinner(
            "Researching with Claude (this may take 20-40 seconds)…"
        ):
            result = trend_analyst.analyze_trend(
                asset_key=asset,
                start=start,
                end=end,
                api_key=api_key,
            )
        _render_result(result)
