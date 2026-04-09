"""Transcript chat -- Anthropic SDK wrapper for question-answering over an
earnings call transcript. No web search, no JSON output. Free-form text.

Mirrors the structure of ``app.data_chat`` but is intentionally simpler:
the caller passes the full transcript text plus the user's question, and
the model answers in plain prose. A single source (the transcript) means
there is no JSON envelope, no ``sources`` list, and no chunking -- the
whole transcript is dropped into the system prompt as grounding context.
"""

from __future__ import annotations

import hashlib
import logging

import streamlit as st

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2048

SYSTEM_PROMPT = """You are an analyst answering a question about an earnings \
call transcript. Answer ONLY using information from the transcript text \
provided below. If the transcript does not contain the answer, say so \
directly -- do not invent facts.

Style:
- Be concise: 2-5 short paragraphs at most.
- Quote short excerpts (under 25 words) when they directly support a claim.
- Do NOT use markdown headings; plain paragraphs are fine.

TRANSCRIPT:
{transcript}"""


@st.cache_data(ttl=259_200, show_spinner=False)
def _ask_cached(transcript_hash: str, question: str, api_key: str, transcript_text: str) -> dict:
    """Cached implementation of transcript Q&A (24h TTL)."""
    import anthropic

    system = SYSTEM_PROMPT.format(transcript=transcript_text)
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL,
            system=system,
            messages=[{"role": "user", "content": question}],
            max_tokens=MAX_TOKENS,
        )
    except anthropic.APIError as e:
        logger.exception("Transcript chat: API error")
        return {
            "answer": (
                f"Could not reach the Anthropic API ({e}). "
                f"Please check the API key and try again."
            )
        }
    except Exception as e:
        logger.exception("Transcript chat: unexpected error")
        return {"answer": f"Unexpected error: {e}"}

    text = response.content[0].text.strip() if response.content else "(no response)"
    return {"answer": text}


def ask(transcript_text: str, question: str, api_key: str) -> dict:
    """Send a question grounded on a transcript (cached 72-hour).

    Args:
        transcript_text: Full text of the earnings call transcript.
        question: The analyst's natural-language question.
        api_key: Anthropic API key.

    Returns:
        Dict with a single ``answer`` key (str). On API or unexpected
        failure, returns a friendly fallback message.
    """
    # Hash the transcript so we can cache by content + question
    transcript_hash = hashlib.sha256(transcript_text.encode()).hexdigest()[:16]

    return _ask_cached(
        transcript_hash=transcript_hash,
        question=question,
        api_key=api_key,
        transcript_text=transcript_text,
    )
