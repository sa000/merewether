"""AI data chat -- Anthropic SDK wrapper for the Merewether pitch app.

Adapted from TREXQUANT's ``app/catalog_agent.py``. The differences:

- No Streamlit imports (this module is pure SDK glue).
- No SQLite cache (the Trex version persists answers; here we always
  re-call the API so the demo feels live).
- Inventory is a Python dict, not a metadata DataFrame -- callers pass
  a pre-rendered text block from ``data_sources.build_inventory_text``.
"""

from __future__ import annotations

import json
import logging

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2048

SYSTEM_PROMPT = """You are a data assistant for the Merewether Investment \
data science pitch app. You help the user discover what data is available \
in this app and how it can be used.

SCOPE: You answer questions about the data sources listed in the catalog \
below -- their providers, frequencies, units, asset classes, date coverage, \
and how they relate. Examples of in-scope questions: "what data is \
available?", "which sources cover macro data?", "what's the difference \
between CPI and unemployment in this app?", "what would I use to research \
inflation?".

If the user asks "What is the size of this data and the date range?", \
respond with a markdown table showing: Source | Frequency | First Date | \
Last Date | Rows. Format the table in standard markdown syntax. Return only \
the table, no other text.

If asked something out of scope (predictions, financial advice, anything \
not about the catalog), respond with:
{{"answer": "I can only help with questions about the data sources in this \
app. Try asking what's available or how a particular source can be used.", \
"sources": []}}

RULES:
- Only reference sources that exist in the catalog below.
- When listing sources, include the inventory key as well as the label so \
the user can find them in the dropdown.
- Keep answers concrete: at most ~120 words. Use plain text, no markdown \
headings (except for the metadata table which uses markdown).
- Each source entry must have EXACTLY ONE inventory key.

Respond with ONLY valid JSON (no markdown code fences):
{{"answer": "Brief natural-language answer or markdown table",
 "sources": [{{"key": "...", "label": "...", "asset_class": "..."}}]}}

{context}"""


def _build_metadata_table(inventory: dict) -> str:
    """Build a markdown table with data sizes and date ranges."""
    from app.data_sources import load_series

    rows = [
        "| Source | Frequency | First Date | Last Date | Rows |",
        "|--------|-----------|-----------|----------|------|",
    ]

    for key, entry in inventory.items():
        df, value_col = load_series(key)
        label = entry.get("label", key)
        frequency = entry.get("frequency", "unknown")

        if df.empty:
            rows.append(f"| {label} | {frequency} | — | — | 0 |")
        else:
            first_date = df.index[0].strftime("%Y-%m-%d") if hasattr(df.index[0], "strftime") else str(df.index[0])
            last_date = df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], "strftime") else str(df.index[-1])
            row_count = len(df)
            rows.append(f"| {label} | {frequency} | {first_date} | {last_date} | {row_count} |")

    return "\n".join(rows)


@st.cache_data(ttl=259_200, show_spinner=False)
def _ask_cached(question: str, inventory_text: str, api_key: str) -> dict:
    """Cached implementation of data chat (24h TTL)."""
    import anthropic
    from app.data_sources import INVENTORY

    # Detect metadata query about data size and date range
    if "size" in question.lower() and "date range" in question.lower():
        table = _build_metadata_table(INVENTORY)
        return {"answer": table, "sources": []}

    system = SYSTEM_PROMPT.format(context=inventory_text)
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL,
            system=system,
            messages=[{"role": "user", "content": question}],
            max_tokens=MAX_TOKENS,
        )
    except anthropic.APIError as e:
        logger.exception("AI Data Chat: Anthropic API error")
        return {
            "answer": (
                f"Could not reach the Anthropic API ({e.message if hasattr(e, 'message') else e}). "
                f"Please check the API key and try again."
            ),
            "sources": [],
        }
    except Exception as e:
        logger.exception("AI Data Chat: unexpected error")
        return {
            "answer": f"Unexpected error talking to the model: {e}",
            "sources": [],
        }

    text = response.content[0].text.strip() if response.content else ""

    # Strip markdown code fences if present (Claude sometimes adds them).
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines[1:] if l.strip() != "```"]
        text = "\n".join(lines).strip()

    try:
        result = json.loads(text)
        if "answer" not in result:
            result["answer"] = text
        if "sources" not in result:
            result["sources"] = []
        return result
    except (json.JSONDecodeError, TypeError):
        return {"answer": text or "(no response)", "sources": []}


def ask(question: str, inventory_text: str, api_key: str) -> dict:
    """Send a question to Claude Haiku with caching (72-hour TTL).

    Args:
        question: User's natural-language question.
        inventory_text: Pre-built inventory text from
            ``data_sources.build_inventory_text``.
        api_key: Anthropic API key.

    Returns:
        Dict with ``answer`` (str) and ``sources`` (list). On API failure,
        returns a friendly fallback message and empty sources list.
    """
    return _ask_cached(question=question, inventory_text=inventory_text, api_key=api_key)
