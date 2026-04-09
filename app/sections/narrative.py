"""Narrative section renderers.

Each function reads a markdown file from ``app/content/`` and renders
it inside the current Streamlit container. Files are watched for changes
using modification time as the cache key.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.style import BORDER_SUBTLE, TEXT_FAINT


_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


def render_content(filename: str) -> None:
    """Read and render a markdown file from app/content/ with auto-refresh.

    Public function for any section to use. When the file is edited and saved,
    the app automatically updates on next page interaction.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        _placeholder_block(f"Missing content file: {filename}")
        return

    # Include file mtime in cache key; when file changes, cache is invalidated
    try:
        file_mtime = path.stat().st_mtime
    except OSError:
        file_mtime = 0

    text = _read_markdown_cached(filename, file_mtime)
    st.markdown(text)


@st.cache_data(show_spinner=False)
def _read_markdown_cached(filename: str, file_mtime: float) -> str:
    """Read markdown file. Cache key includes mtime for auto-refresh on edits.

    When file modification time changes, cache is invalidated and file is re-read.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        return f"**Missing content file: {filename}**"
    return path.read_text(encoding="utf-8")


def _render_markdown(filename: str) -> None:
    """Read and render a markdown file from ``app/content/``.

    Edits to .md files automatically update the page when you save.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        _placeholder_block(f"Missing content file: {filename}")
        return

    # Include file mtime in cache key; when file changes, cache is invalidated
    try:
        file_mtime = path.stat().st_mtime
    except OSError:
        file_mtime = 0

    text = _read_markdown_cached(filename, file_mtime)
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
    _render_data_explorer()


def _render_data_explorer() -> None:
    """Render the data explorer."""
    from app.sections import data_explorer as data_explorer_section
    data_explorer_section.render()


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
