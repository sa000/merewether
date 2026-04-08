"""Data Explorer section renderer.

A dropdown over the inventory, a Plotly time-series chart, and six
summary-stat metrics. Validates the data layer end-to-end without any
AI dependency.
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from app.charts import price_line_chart, summary_stats
from app.data_sources import INVENTORY, load_series
from app.style import (
    BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    show_chart,
)


def _intro() -> None:
    st.markdown(
        f"""
        <p style="color: {TEXT_PRIMARY}; font-size: 16px; line-height: 1.7;
                  margin: 0 0 1rem 0;">
            A small interactive demo of how I think about data plumbing.
            Pick any series below: prices come from Yahoo Finance, macro
            series come from the St. Louis Fed FRED database. No API key
            is required for either.
        </p>
        """,
        unsafe_allow_html=True,
    )


def _format_metric(value: float, kind: str = "number") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if kind == "pct":
        return f"{value:+.2f}%"
    return f"{value:,.2f}"


def render() -> None:
    _intro()

    keys = list(INVENTORY.keys())
    choice = st.selectbox(
        "Choose a data source",
        keys,
        format_func=lambda k: INVENTORY[k]["label"],
        key="data_explorer_choice",
    )
    entry = INVENTORY[choice]

    df, value_col = load_series(choice)
    if df.empty or not value_col:
        st.warning(
            f"Could not load **{entry['label']}** right now. The "
            "underlying provider may be temporarily unavailable. Try "
            "another source from the dropdown."
        )
        return

    st.markdown(
        f"""
        <div style="color: {TEXT_DIM}; font-size: 14px; margin: 0.25rem 0 1rem 0;">
            {entry['description']} &middot; {entry['frequency']} &middot;
            {entry['units']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = price_line_chart(
        df=df,
        value_col=value_col,
        title=entry["label"],
        yaxis_title=entry["units"],
        height=420,
    )
    show_chart(fig, height=420)

    stats = summary_stats(df, value_col)

    cols = st.columns(6)
    cols[0].metric("Last", _format_metric(stats["last"]))
    cols[1].metric("Year-over-Year", _format_metric(stats["yoy_pct"], "pct"))
    cols[2].metric("Mean", _format_metric(stats["mean"]))
    cols[3].metric("Std Dev", _format_metric(stats["std"]))
    cols[4].metric("Min", _format_metric(stats["min"]))
    cols[5].metric("Max", _format_metric(stats["max"]))

    if stats["observations"]:
        first_date = pd.Timestamp(df.index[0]).strftime("%Y-%m-%d")
        last_date = pd.Timestamp(df.index[-1]).strftime("%Y-%m-%d")
        st.markdown(
            f"""
            <div style="color: {TEXT_DIM}; font-size: 13px; margin-top: 0.6rem;">
                {stats["observations"]:,} observations &middot;
                {first_date} to {last_date}
            </div>
            """,
            unsafe_allow_html=True,
        )
