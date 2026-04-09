"""Merewether Investment -- Streamlit pitch app entry point.

Single-page layout with a hero, table of contents, and seven collapsible
sections (three narrative, three interactive, one transcript demo, plus
a footer). Run with ``streamlit run app/main.py``.
"""

import base64
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.style import (  # noqa: E402
    inject_css,
    sidebar_logo,
    ACCENT,
    BG_CARD,
    BG_CARD_SOLID,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_DIM,
    TEXT_FAINT,
)
from app.sections import narrative  # noqa: E402
from app.sections import data_explorer as data_explorer_section  # noqa: E402
from app.sections import data_chat as data_chat_section  # noqa: E402
from app.sections import trend_research as trend_research_section  # noqa: E402
from app.sections import transcript as transcript_section  # noqa: E402


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
_LOGO_PATH = PROJECT_ROOT / "app" / "static" / "logo_m.png"

st.set_page_config(
    page_title="Merewether Investment | Data Science Proposal",
    page_icon=str(_LOGO_PATH) if _LOGO_PATH.exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
sidebar_logo(PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
def _render_hero() -> None:
    logo_html = ""
    if _LOGO_PATH.exists():
        b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode()
        logo_html = (
            f'<img src="data:image/png;base64,{b64}" width="110" '
            f'style="display: block; margin: 0 auto 1.25rem auto;" />'
        )

    st.markdown(
        f"""
        <div style="text-align: center; padding: 2.5rem 0 1rem 0;">
            {logo_html}
            <div style="color: {TEXT_DIM}; font-size: 0.85rem;
                        text-transform: uppercase; letter-spacing: 0.18em;
                        margin-bottom: 0.6rem;">
                Data Science Proposal
            </div>
            <h1 style="color: {TEXT_PRIMARY}; font-weight: 700;
                       font-size: 2.6rem; margin: 0; letter-spacing: -0.02em;">
                Sakibul Alam
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Table of contents
# ---------------------------------------------------------------------------
_TOC_ITEMS = [
    "1. Purpose",
    "2. Short-Term Goals",
    "3. Long-Term Goals",
    "4. Data Explorer",
    "5. AI Data Chat",
    "6. Trend Research",
    "7. Transcript Analysis",
]


def _render_toc() -> None:
    items_html = "".join(
        f'<span style="color: {TEXT_SECONDARY}; font-size: 0.9rem; '
        f'white-space: nowrap;">{item}</span>'
        for item in _TOC_ITEMS
    )
    st.markdown(
        f"""
        <div style="background: {BG_CARD_SOLID}; border: 1px solid {BORDER};
                    border-radius: 8px; padding: 1.1rem 1.4rem;
                    margin: 1.5rem 0 2rem 0;">
            <div style="color: {TEXT_DIM}; font-size: 0.78rem;
                        text-transform: uppercase; letter-spacing: 0.1em;
                        margin-bottom: 0.65rem;">
                Contents
            </div>
            <div style="display: flex; flex-wrap: wrap;
                        gap: 0.55rem 1.75rem;">
                {items_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _render_footer() -> None:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 3rem 0 1rem 0;
                    margin-top: 2rem; border-top: 1px solid {BORDER};">
            <p style="color: {TEXT_FAINT}; font-size: 0.82rem; margin: 0;">
                Built April 2026 &middot;
                <a href="https://github.com/sa000/merewether"
                   style="color: {TEXT_FAINT}; border-bottom: none;">
                    github.com/sa000/merewether
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------------
_render_hero()
_render_toc()


# Sections
with st.expander("1. Purpose", expanded=False):
    narrative.render_why()

with st.expander("2. Short-Term Goals", expanded=False):
    narrative.render_short_term()

with st.expander("3. Long-Term Goals", expanded=False):
    narrative.render_long_term()

with st.expander("4. Data Explorer", expanded=False):
    data_explorer_section.render()

with st.expander("5. AI Data Chat", expanded=False):
    data_chat_section.render()

with st.expander("6. Trend Research", expanded=False):
    trend_research_section.render()

with st.expander("7. Transcript Analysis", expanded=False):
    transcript_section.render()


_render_footer()
