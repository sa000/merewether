"""Section renderers and shared section helpers.

Each module in this package exposes a ``render()`` (or several
``render_*()``) function that draws one collapsible section of the
single-page Streamlit app. Shared helpers for API key handling and
local ``.env`` loading also live here so every section can use them
without repeating boilerplate.
"""

import os
from pathlib import Path

import streamlit as st


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DOTENV_LOADED = False


def _load_dotenv() -> None:
    """Load ``.env`` (if present) into ``os.environ`` once per process.

    Streamlit Cloud uses ``st.secrets`` (configured in the dashboard) so
    this function is only useful for local development. We do not depend
    on ``python-dotenv`` -- the parser is intentionally tiny.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True

    dotenv_path = _PROJECT_ROOT / ".env"
    if not dotenv_path.exists():
        return
    try:
        for raw_line in dotenv_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


def get_api_key() -> str | None:
    """Return the Anthropic API key from secrets or env, else ``None``.

    Order of precedence:

    1. ``st.secrets["ANTHROPIC_API_KEY"]`` -- Streamlit Cloud / .streamlit/secrets.toml
    2. ``os.environ["ANTHROPIC_API_KEY"]`` -- local .env or shell export

    The ``st.secrets`` access is wrapped in try/except because Streamlit
    raises (rather than returning ``None``) when no secrets file exists.
    """
    _load_dotenv()
    try:
        secret = st.secrets.get("ANTHROPIC_API_KEY")
        if secret:
            return secret
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY") or None


def require_api_key() -> str | None:
    """Get the API key, or render a warning and return ``None``.

    Section renderers call this at the top of their ``render()`` and
    bail out (still showing widgets, but with the submit button
    disabled) when no key is available.
    """
    key = get_api_key()
    if not key:
        st.warning(
            "This section calls the Anthropic API. Set "
            "``ANTHROPIC_API_KEY`` in ``.env`` (local) or in the "
            "Streamlit Cloud secrets dashboard to enable it."
        )
    return key
