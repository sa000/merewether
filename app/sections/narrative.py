"""Narrative section renderers.

Each function reads a markdown file from ``app/content/`` and renders
it inside the current Streamlit container. The transcript section
also drops a dashed placeholder block underneath the explanatory text.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.style import BORDER_SUBTLE, TEXT_FAINT


_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def _render_markdown(filename: str) -> None:
    """Read and render a markdown file from ``app/content/``.

    Falls back to a dashed placeholder if the file is missing so the
    section never crashes during early development.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        _placeholder_block(f"Missing content file: {filename}")
        return
    text = path.read_text(encoding="utf-8")
    st.markdown(text)


def _placeholder_block(label: str) -> None:
    """Render a dashed placeholder card."""
    st.markdown(
        f"""
        <div style="border: 2px dashed {BORDER_SUBTLE}; border-radius: 8px;
                    padding: 2rem; text-align: center; margin: 1rem 0;
                    background: #fafafa;">
            <p style="color: {TEXT_FAINT}; font-size: 0.9rem; margin: 0;">
                {label}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Public renderers
# ---------------------------------------------------------------------------
def render_about() -> None:
    _render_markdown("about.md")


def render_why() -> None:
    _render_markdown("why.md")


def render_short_term() -> None:
    _render_markdown("short_term.md")


def render_long_term() -> None:
    _render_markdown("long_term.md")


def render_transcript_placeholder() -> None:
    _render_markdown("transcript_placeholder.md")
    _placeholder_block("Transcript analyzer — coming soon")
