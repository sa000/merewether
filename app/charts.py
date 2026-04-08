"""Plotly chart builders for the Merewether pitch app.

Pure functions: take data in, return a Plotly Figure out. No
Streamlit imports. The light theme defaults match ``app/style.py``
so charts blend with the rest of the page.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app.style import (
    ACCENT,
    BORDER,
    CHART_COLORS,
    TEXT_DIM,
    TEXT_PRIMARY,
)


LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    margin=dict(l=60, r=30, t=50, b=50),
    hovermode="x unified",
    font=dict(size=12, color=TEXT_PRIMARY, family="Source Sans 3, sans-serif"),
    xaxis=dict(
        gridcolor=BORDER,
        zeroline=False,
        showline=True,
        linecolor=BORDER,
        ticks="outside",
        tickcolor=BORDER,
    ),
    yaxis=dict(
        gridcolor=BORDER,
        zeroline=False,
        showline=True,
        linecolor=BORDER,
        ticks="outside",
        tickcolor=BORDER,
    ),
)


def _dates(index: pd.Index) -> list[str]:
    """Convert a datetime index to a list of YYYY-MM-DD strings."""
    return [pd.Timestamp(d).strftime("%Y-%m-%d") for d in index]


def _apply_layout(
    fig: go.Figure,
    title: str,
    yaxis_title: str,
    height: int = 420,
) -> go.Figure:
    """Apply consistent layout defaults to a figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color=TEXT_PRIMARY),
            x=0.0,
            xanchor="left",
        ),
        yaxis_title=yaxis_title,
        height=height,
        **LAYOUT_DEFAULTS,
    )
    fig.update_xaxes(nticks=10, tickformat="%b %Y")
    return fig


def price_line_chart(
    df: pd.DataFrame,
    value_col: str,
    title: str,
    yaxis_title: str,
    height: int = 420,
) -> go.Figure:
    """Single-series line chart for any time-indexed numeric column.

    Args:
        df: DataFrame indexed by date (or with a date column already
            set as the index) with at least one numeric column.
        value_col: The column to plot.
        title: Chart title.
        yaxis_title: Y axis label (e.g. ``"USD"``, ``"Index"``).
        height: Chart height in pixels.

    Returns:
        Plotly Figure.
    """
    if df.empty or value_col not in df.columns:
        fig = go.Figure()
        return _apply_layout(fig, title, yaxis_title, height)

    series = df[value_col].dropna()
    dates = _dates(series.index)
    values = series.tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name=value_col,
            line=dict(color=ACCENT, width=2),
            fill="tozeroy" if False else None,  # leave room for fill if desired
            hovertemplate="%{x}<br><b>%{y:,.2f}</b><extra></extra>",
        )
    )
    return _apply_layout(fig, title, yaxis_title, height)


def summary_stats(df: pd.DataFrame, value_col: str) -> dict:
    """Return summary statistics for a numeric series.

    Args:
        df: DataFrame indexed by date with the value column present.
        value_col: Column name to summarize.

    Returns:
        Dict with keys ``mean``, ``std``, ``min``, ``max``, ``last``,
        ``yoy_pct``, ``observations``. ``yoy_pct`` is the percent change
        of ``last`` versus the value approximately one year earlier
        (uses the closest prior date). All values are floats; missing
        data yields ``float('nan')``.
    """
    if df.empty or value_col not in df.columns:
        nan = float("nan")
        return dict(
            mean=nan, std=nan, min=nan, max=nan,
            last=nan, yoy_pct=nan, observations=0,
        )

    series = df[value_col].dropna()
    if series.empty:
        nan = float("nan")
        return dict(
            mean=nan, std=nan, min=nan, max=nan,
            last=nan, yoy_pct=nan, observations=0,
        )

    last_val = float(series.iloc[-1])
    last_date = pd.Timestamp(series.index[-1])

    # Find the closest observation at least ~365 days earlier.
    one_year_ago = last_date - pd.Timedelta(days=365)
    earlier = series[series.index <= one_year_ago]
    if earlier.empty:
        yoy_pct = float("nan")
    else:
        prev_val = float(earlier.iloc[-1])
        if prev_val == 0:
            yoy_pct = float("nan")
        else:
            yoy_pct = (last_val - prev_val) / prev_val * 100.0

    return dict(
        mean=float(series.mean()),
        std=float(series.std()),
        min=float(series.min()),
        max=float(series.max()),
        last=last_val,
        yoy_pct=yoy_pct,
        observations=int(series.shape[0]),
    )
