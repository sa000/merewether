"""Data source fetchers and inventory for the Merewether pitch app.

Two providers:

- **Yahoo Finance** for daily OHLCV (Apple stock, corn futures).
- **FRED public CSV** for macro series (GDP, CPI, unemployment).
  Uses ``https://fred.stlouisfed.org/graph/fredgraph.csv`` which does
  NOT require an API key.

The ``INVENTORY`` dict is the single source of truth for what's
available -- both ``sections/data_explorer.py`` (the UI dropdown) and
``data_chat.py`` (the LLM context) read from it.
"""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
INVENTORY: dict[str, dict] = {
    "AAPL": {
        "label": "Apple Inc. (AAPL)",
        "source": "yahoo",
        "ticker": "AAPL",
        "asset_class": "equity",
        "frequency": "daily",
        "units": "USD per share",
        "description": "Daily OHLCV for Apple Inc. common stock.",
    },
    "ZC=F": {
        "label": "Corn Futures (ZC=F)",
        "source": "yahoo",
        "ticker": "ZC=F",
        "asset_class": "futures",
        "frequency": "daily",
        "units": "USD per bushel (front-month)",
        "description": (
            "Daily OHLCV for CBOT corn futures, front-month continuous "
            "contract via Yahoo Finance."
        ),
    },
    "GDP": {
        "label": "US Real GDP",
        "source": "fred",
        "series_id": "GDP",
        "asset_class": "macro",
        "frequency": "quarterly",
        "units": "USD billions",
        "description": (
            "Quarterly US gross domestic product, billions of dollars, "
            "from the St. Louis Fed FRED database."
        ),
    },
    "CPIAUCSL": {
        "label": "US CPI (All Urban Consumers)",
        "source": "fred",
        "series_id": "CPIAUCSL",
        "asset_class": "macro",
        "frequency": "monthly",
        "units": "Index, 1982-1984=100",
        "description": (
            "Monthly headline Consumer Price Index for all urban "
            "consumers, from FRED."
        ),
    },
    "UNRATE": {
        "label": "US Unemployment Rate",
        "source": "fred",
        "series_id": "UNRATE",
        "asset_class": "macro",
        "frequency": "monthly",
        "units": "Percent",
        "description": (
            "Monthly civilian unemployment rate (seasonally adjusted), "
            "from FRED."
        ),
    },
}


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_yahoo(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Download OHLCV history from Yahoo Finance.

    Returns an empty DataFrame on any failure -- the caller is
    responsible for showing a friendly message rather than crashing
    the app. ``yfinance`` is wrapped because the underlying scraping
    target changes occasionally.
    """
    try:
        import yfinance as yf

        df = yf.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if df is None or df.empty:
            return pd.DataFrame()

        # yfinance >= 0.2.x returns a MultiIndex column for single-ticker
        # downloads in some versions; flatten it.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                c[0] if isinstance(c, tuple) else c for c in df.columns
            ]
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_open_meteo(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch daily temperature and precipitation from Open-Meteo's free archive API.

    Returns a DataFrame indexed by date with columns:
        - precip_in (precipitation in inches)
        - temp_max_f (max temperature in Fahrenheit)
        - temp_min_f (min temperature in Fahrenheit)

    Returns empty DataFrame on any failure (no API key required for the
    archive endpoint).
    """
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "America/Chicago",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily") or {}
        if not daily.get("time"):
            return pd.DataFrame()
        df = pd.DataFrame({
            "date": pd.to_datetime(daily["time"]),
            "temp_max_f": [t * 9 / 5 + 32 if t is not None else None for t in daily.get("temperature_2m_max", [])],
            "temp_min_f": [t * 9 / 5 + 32 if t is not None else None for t in daily.get("temperature_2m_min", [])],
            "precip_in": [p / 25.4 if p is not None else None for p in daily.get("precipitation_sum", [])],
        })
        df = df.set_index("date")
        return df
    except Exception:
        return pd.DataFrame()


def corn_weather_correlation() -> dict:
    """Compute the trailing-1y correlation between corn futures and Iowa
    rolling-30d precipitation.

    Returns:
        Dict with:
        - correlation: float (Pearson) over the trailing ~252 trading days,
          NaN if insufficient data
        - merged_df: DataFrame indexed by date with columns
          ['corn_close', 'precip_30d_in']
        - rolling_corr_df: DataFrame indexed by date with column
          'rolling_corr_60d' (60-trading-day rolling correlation)
        - start_date: ISO date string of the merged window start
        - end_date: ISO date string of the merged window end
        Empty values on failure.
    """
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=2 * 365)

    corn = fetch_yahoo("ZC=F", period="2y")
    if corn.empty:
        return {"correlation": float("nan"), "merged_df": pd.DataFrame(),
                "rolling_corr_df": pd.DataFrame(),
                "start_date": "", "end_date": ""}

    weather = fetch_open_meteo(41.59, -93.62, start.isoformat(), end.isoformat())
    if weather.empty:
        return {"correlation": float("nan"), "merged_df": pd.DataFrame(),
                "rolling_corr_df": pd.DataFrame(),
                "start_date": "", "end_date": ""}

    # Pick a sensible close column
    close_col = "Close" if "Close" in corn.columns else corn.select_dtypes("number").columns[0]
    corn_series = corn[close_col].rename("corn_close")

    precip_30d = weather["precip_in"].rolling(window=30, min_periods=15).sum().rename("precip_30d_in")

    merged = pd.concat([corn_series, precip_30d], axis=1, join="inner").dropna()
    if merged.empty or len(merged) < 30:
        return {"correlation": float("nan"), "merged_df": merged,
                "rolling_corr_df": pd.DataFrame(),
                "start_date": "", "end_date": ""}

    trailing = merged.tail(252)
    correlation = float(trailing["corn_close"].corr(trailing["precip_30d_in"]))

    rolling_corr = merged["corn_close"].rolling(60, min_periods=30).corr(merged["precip_30d_in"])
    rolling_corr_df = rolling_corr.dropna().to_frame("rolling_corr_60d")

    return {
        "correlation": correlation,
        "merged_df": merged,
        "rolling_corr_df": rolling_corr_df,
        "start_date": merged.index[0].strftime("%Y-%m-%d"),
        "end_date": merged.index[-1].strftime("%Y-%m-%d"),
    }


@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_fred(series_id: str) -> pd.DataFrame:
    """Download a FRED series as a DataFrame.

    Uses the public chart-export endpoint (no API key required). FRED
    encodes missing values as a literal ``"."`` so VALUE is coerced
    via ``pd.to_numeric(..., errors="coerce")``.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        if df.empty:
            return pd.DataFrame()

        # Older FRED responses use "DATE", newer ones may use "observation_date".
        date_col = None
        for cand in ("DATE", "observation_date", "date"):
            if cand in df.columns:
                date_col = cand
                break
        if date_col is None:
            date_col = df.columns[0]

        # The value column is whichever non-date column is present.
        value_cols = [c for c in df.columns if c != date_col]
        if not value_cols:
            return pd.DataFrame()
        value_col = value_cols[0]

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df = df.dropna(subset=[date_col]).set_index(date_col)
        df.index.name = "date"
        df = df.rename(columns={value_col: series_id})
        return df[[series_id]]
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def load_series(key: str) -> tuple[pd.DataFrame, str]:
    """Fetch a series by inventory key.

    Returns a ``(df, value_column_name)`` tuple. The DataFrame is
    indexed by date with at least one numeric column; the second
    element is the column name to plot. Empty DataFrame on failure.
    """
    if key not in INVENTORY:
        return pd.DataFrame(), ""

    entry = INVENTORY[key]
    source = entry["source"]

    if source == "yahoo":
        df = fetch_yahoo(entry["ticker"])
        if df.empty:
            return df, ""
        # Prefer adjusted close; fall back to whatever is closest.
        for cand in ("Close", "Adj Close", "close"):
            if cand in df.columns:
                return df, cand
        # Last resort: first numeric column.
        numeric = df.select_dtypes(include="number").columns.tolist()
        return (df, numeric[0]) if numeric else (df, "")

    if source == "fred":
        df = fetch_fred(entry["series_id"])
        if df.empty:
            return df, ""
        return df, entry["series_id"]

    return pd.DataFrame(), ""


# ---------------------------------------------------------------------------
# Inventory text for the AI Data Chat system prompt
# ---------------------------------------------------------------------------
def build_inventory_text(inventory: dict | None = None) -> str:
    """Render the inventory as a structured text block.

    The output is injected into the AI Data Chat system prompt so
    Claude can answer questions about *what's available* without
    hallucinating sources we don't actually have.
    """
    inv = inventory if inventory is not None else INVENTORY
    if not inv:
        return "(no data sources configured)"

    lines = ["AVAILABLE DATA SOURCES:", ""]
    for key, entry in inv.items():
        lines.append(f"## {entry['label']}")
        lines.append(f"- key: {key}")
        lines.append(f"- provider: {entry['source']}")
        lines.append(f"- asset class: {entry['asset_class']}")
        lines.append(f"- frequency: {entry['frequency']}")
        lines.append(f"- units: {entry['units']}")
        lines.append(f"- description: {entry['description']}")
        lines.append("")
    return "\n".join(lines)
