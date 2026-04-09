"""AI trend post-mortem -- Anthropic SDK wrapper with web search.

Adapted from TREXQUANT's ``app/trade_analyst.py``. The Trex version
selects the best and worst trades from a backtest log and asks Claude
to research what drove each one. This version is simpler: the user
picks ONE asset and ONE date window, and Claude does a single
post-mortem on that trend with web search citations.

The ``parse_response`` function is lifted nearly verbatim from Trex
because the web_search_tool_result handling, citation deduplication,
and section splitting are load-bearing.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import pandas as pd
import streamlit as st

from app.data_sources import INVENTORY, load_series

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """You are a markets analyst writing a brief post-mortem on \
{asset_label} between {start} and {end}. The reader is a portfolio manager \
who already sees the price chart -- do not restate the dates or prices. \
Jump straight into the analysis.

CITATIONS ARE MANDATORY. Every single factual claim must be supported by a \
source citation. If you cannot find evidence for a claim in the search results, \
do not make it. Omit the claim entirely rather than speculate.

FORMAT RULES (follow exactly):
- Begin with a short ### Overview section -- 2-3 sentences naming the \
single most important driver of the move.
- Follow with a ### Drivers section listing 3-5 short paragraphs, each \
explaining a distinct catalyst (earnings, weather, policy, macro, \
positioning, etc.).
- End with a ### Caveats section noting anything the search results were \
unclear about, or alternative narratives.
- CRITICAL CITATION RULE: Every factual claim (any statement about prices, \
earnings, events, conditions, announcements) MUST include a citation showing \
WHERE the claim came from. Use inline markdown links: \
"iPhone sales rose 15% ([source title](url))" or \
"As reported by Financial Times, [reported that earnings fell](url)." \
Citations must be in the SAME SENTENCE as the claim. Do NOT list all sources \
at the end -- embed them in the narrative right where they support the claim. \
Every number, date, company announcement, earnings result, policy change must \
have a source. Prioritize official sources (earnings calls, press releases, \
SEC filings, established financial media) over speculation.
- Be specific. Use exact numbers, dates, and source names wherever possible. \
Avoid generalities like "market conditions deteriorated" without evidence."""


def build_window_context(
    asset_label: str,
    asset_key: str,
    start: date,
    end: date,
    price_summary: dict,
) -> str:
    """Format the user-facing prompt for the API call.

    Includes the asset, the window, and a handful of numeric anchors
    so Claude has factual hooks to tie the narrative to.
    """
    parts = [
        f"Analyze {asset_label} (inventory key: {asset_key}) between "
        f"{start.isoformat()} and {end.isoformat()}.",
        "",
        "Numeric anchors from the price series:",
    ]
    if price_summary:
        for k in ("start_price", "end_price", "pct_change", "peak", "trough"):
            if k in price_summary and price_summary[k] is not None:
                v = price_summary[k]
                if k == "pct_change":
                    parts.append(f"- {k}: {v:+.2f}%")
                else:
                    parts.append(f"- {k}: {v:,.2f}")
    parts.append("")
    parts.append(
        "Use web search to find the news, reports, and events that "
        "explain the move. Cite every claim inline."
    )
    return "\n".join(parts)


def _summarize_window(
    df: pd.DataFrame, value_col: str, start: date, end: date
) -> dict:
    """Compute a small set of numeric anchors for the AI prompt."""
    if df.empty or value_col not in df.columns:
        return {}
    sub = df.loc[
        (df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end)),
        value_col,
    ].dropna()
    if sub.empty:
        return {}
    start_price = float(sub.iloc[0])
    end_price = float(sub.iloc[-1])
    pct = (end_price - start_price) / start_price * 100.0 if start_price else None
    return {
        "start_price": start_price,
        "end_price": end_price,
        "pct_change": pct,
        "peak": float(sub.max()),
        "trough": float(sub.min()),
    }


# ---------------------------------------------------------------------------
# Response parsing (lifted from Trex with minor cleanup)
# ---------------------------------------------------------------------------
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "were", "are", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "this", "that",
    "these", "those", "it", "its", "not", "no", "than", "more", "also",
    "which", "what", "when", "where", "how", "all", "each", "every",
    "both", "few", "some", "any", "most", "per", "up", "down", "out",
    "into", "over", "after", "before",
}


def parse_response(response) -> dict:
    """Extract narrative text + section citations from a web-search response."""
    narrative_parts: list[str] = []
    all_search_results: list[dict] = []

    for block in response.content:
        btype = getattr(block, "type", None)

        if btype == "web_search_tool_result":
            content_blocks = getattr(block, "content", None) or []
            for item in content_blocks:
                url = getattr(item, "url", None)
                title = getattr(item, "title", "") or ""
                if url:
                    all_search_results.append({"title": title, "url": url})

        elif btype == "text":
            narrative_parts.append(getattr(block, "text", "") or "")

    full_narrative = "\n".join(narrative_parts).strip()

    # Deduplicate search results
    seen_urls: set[str] = set()
    unique_results: list[dict] = []
    for r in all_search_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)

    # Split on h2 or h3 headings into sections. Claude sometimes uses
    # ## and sometimes ### regardless of the system prompt; accept both.
    sections: dict[str, str] = {}
    parts = re.split(r"(?=^#{2,3}\s+)", full_narrative, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^#{2,3}\s+(.+?)(?:\n|$)", part)
        if m:
            key = m.group(1).strip()
            body = part[m.end():].strip()
            sections[key] = body
        else:
            sections.setdefault("_preamble", part)

    # Match citations to sections by simple keyword overlap
    section_citations: dict[str, list[dict]] = {}
    for key, body in sections.items():
        if key == "_preamble":
            section_citations[key] = []
            continue
        words = set(
            w.lower() for w in re.findall(r"[A-Za-z]{3,}", body)
        ) - _STOP_WORDS
        scored: list[tuple[int, dict]] = []
        for r in unique_results:
            tw = set(
                w.lower() for w in re.findall(r"[A-Za-z]{3,}", r["title"])
            )
            overlap = len(words & tw)
            if overlap > 0:
                scored.append((overlap, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        section_citations[key] = [r for _, r in scored[:5]]

    # Also harvest inline markdown links from each section
    for key, body in sections.items():
        seen = {c["url"] for c in section_citations.get(key, [])}
        for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\)]+)\)", body):
            title, url = m.group(1), m.group(2)
            if url not in seen:
                section_citations.setdefault(key, []).append(
                    {"title": title, "url": url}
                )
                seen.add(url)

    return {
        "narrative": full_narrative,
        "sections": sections,
        "section_citations": section_citations,
        "citations": unique_results,
    }


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------
@st.cache_data(ttl=259_200, show_spinner=False)
def _analyze_trend_cached(
    asset_key: str,
    start_iso: str,
    end_iso: str,
    api_key: str,
) -> dict:
    """Cached implementation of trend analysis (72-hour TTL)."""
    import anthropic

    start = date.fromisoformat(start_iso)
    end = date.fromisoformat(end_iso)

    if asset_key not in INVENTORY:
        return _error(f"Unknown asset: {asset_key}")

    entry = INVENTORY[asset_key]
    asset_label = entry["label"]

    # Pull a few numeric anchors so Claude has facts to tie the
    # narrative to. Failure to fetch is OK -- we still call the model
    # with an empty summary.
    df, value_col = load_series(asset_key)
    summary = _summarize_window(df, value_col, start, end) if value_col else {}

    context = build_window_context(asset_label, asset_key, start, end, summary)
    system = SYSTEM_PROMPT.format(
        asset_label=asset_label,
        start=start.isoformat(),
        end=end.isoformat(),
    )

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            system=system,
            messages=[{"role": "user", "content": context}],
            max_tokens=MAX_TOKENS,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
        )
    except anthropic.APIError as e:
        logger.exception("Trend analyst: Anthropic API error")
        return _error(f"API error: {getattr(e, 'message', str(e))}")
    except Exception as e:
        logger.exception("Trend analyst: unexpected error")
        return _error(f"Unexpected error: {e}")

    parsed = parse_response(response)
    parsed["error"] = None
    parsed["price_summary"] = summary
    return parsed


def analyze_trend(
    asset_key: str,
    start: date,
    end: date,
    api_key: str,
) -> dict:
    """Public entry point for trend analysis with caching.

    Args:
        asset_key: Inventory key from ``data_sources.INVENTORY``
            (only ``yahoo``-source assets are supported).
        start: Window start date.
        end: Window end date.
        api_key: Anthropic API key.

    Returns:
        Dict with ``narrative``, ``sections``, ``section_citations``,
        ``citations``, ``price_summary``, and ``error``.
    """
    return _analyze_trend_cached(
        asset_key=asset_key,
        start_iso=start.isoformat(),
        end_iso=end.isoformat(),
        api_key=api_key,
    )


def _error(msg: str) -> dict:
    return {
        "narrative": "",
        "sections": {},
        "section_citations": {},
        "citations": [],
        "price_summary": {},
        "error": msg,
    }
