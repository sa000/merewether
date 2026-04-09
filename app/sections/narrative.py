"""Narrative section renderers.

Each function reads a markdown file from ``app/content/`` and renders
it inside the current Streamlit container. Files are watched automatically—
edits trigger instant reruns without requiring a restart.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.style import BORDER_SUBTLE, TEXT_FAINT


_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def _render_markdown(filename: str) -> None:
    """Read and render a markdown file from ``app/content/``.

    Files are watched automatically by Streamlit. Edits to .md files trigger
    an instant rerun and show updated content (no restart needed).
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        _placeholder_block(f"Missing content file: {filename}")
        return

    # Read file fresh each render (no caching) so Streamlit detects changes
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
def render_why() -> None:
    _render_markdown("why.md")


def render_short_term() -> None:
    _render_markdown("short_term.md")
    _render_correlation_widget()


def render_long_term() -> None:
    _render_markdown("long_term.md")


def _render_correlation_widget() -> None:
    """Render the corn vs weather chart."""
    import streamlit as st
    from app.data_sources import corn_weather_correlation
    from app.charts import dual_axis_line_chart
    from app.style import show_chart

    result = corn_weather_correlation()
    merged = result.get("merged_df")
    if merged is None or merged.empty:
        st.caption("Live data temporarily unavailable.")
        return

    fig = dual_axis_line_chart(
        df=merged,
        left_col="corn_close",
        right_col="precip_30d_in",
        left_title="Corn contract value ($)",
        right_title="Iowa rolling 30d precip (in)",
        title="Corn futures vs Iowa precipitation",
        height=340,
    )
    show_chart(fig, height=340)
