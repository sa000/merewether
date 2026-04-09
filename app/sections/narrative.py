"""Narrative section renderers.

Each function reads a markdown file from ``app/content/`` and renders
it inside the current Streamlit container. Files are watched for changes
so edits auto-refresh without restarting the app.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.style import BORDER_SUBTLE, TEXT_FAINT


_CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


@st.cache_data(show_spinner=False)
def _read_cached_markdown(filename: str, file_mtime: float) -> str:
    """Read markdown file with mtime-based cache invalidation.

    When the file's modification time changes, the cache key changes and
    the cached result is invalidated, triggering an app rerun.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        return f"**Missing content file: {filename}**"
    return path.read_text(encoding="utf-8")


def _render_markdown(filename: str) -> None:
    """Read and render a markdown file from ``app/content/``.

    Files are automatically watched. When you edit and save a .md file,
    the app detects the change and reruns to display the updated content.
    No restart needed.
    """
    path = _CONTENT_DIR / filename
    if not path.exists():
        _placeholder_block(f"Missing content file: {filename}")
        return

    # Get file modification time; when this changes, cache is invalidated
    try:
        file_mtime = path.stat().st_mtime
    except OSError:
        file_mtime = 0

    # Cache key includes mtime, so file edits auto-invalidate the cache
    text = _read_cached_markdown(filename, file_mtime)
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
    """A small live demo of the kind of project mentioned above."""
    import streamlit as st
    from app.data_sources import corn_weather_correlation
    from app.charts import dual_axis_line_chart
    from app.style import show_chart, ACCENT, TEXT_DIM

    st.markdown(
        f'<h4 style="color: {ACCENT}; font-weight: 700; margin: 1.5rem 0 0.5rem 0;">'
        f'A small concrete example</h4>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color: {TEXT_DIM}; font-size: 14px; margin: 0 0 1rem 0;">'
        f'Live: corn front-month futures (ZC=F) versus rolling 30-day '
        f'Iowa precipitation. Updates whenever this page is opened.</p>',
        unsafe_allow_html=True,
    )

    result = corn_weather_correlation()
    merged = result.get("merged_df")
    if merged is None or merged.empty:
        st.caption("Live data temporarily unavailable. The correlation chart "
                   "will return on the next refresh.")
        return

    fig = dual_axis_line_chart(
        df=merged,
        left_col="corn_close",
        right_col="precip_30d_in",
        left_title="Corn close (USc/bu)",
        right_title="Iowa 30d precip (in)",
        title="Corn futures vs Iowa precipitation",
        height=340,
    )
    show_chart(fig, height=340)

    corr = result.get("correlation")
    c1, c2 = st.columns([1, 3])
    if corr is not None and corr == corr:  # NaN check
        c1.metric("Trailing 1y Pearson r", f"{corr:+.2f}")
    else:
        c1.metric("Trailing 1y Pearson r", "—")
    c2.markdown(
        f'<p style="color: {TEXT_DIM}; font-size: 13px; margin-top: 0.5rem;">'
        f'A single state and a single window — not predictive on its own. '
        f'The point is to show the kind of small, concrete project I would '
        f'start with: pull two free public sources, line them up on a date '
        f'index, and compute one honest number.</p>',
        unsafe_allow_html=True,
    )
