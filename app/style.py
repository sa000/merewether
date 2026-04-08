"""Custom CSS styling for the Merewether pitch app.

A light, conservative theme that mirrors merewetherinvestment.com:
white background, near-black text, thin gray borders, and a single
near-black-navy accent. Adapted from the dark TREXQUANT styling.
"""

import base64
from pathlib import Path

import streamlit as st


_DEFAULT_LOGO = Path(__file__).resolve().parent / "static" / "logo_m.png"

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
ACCENT = "#1a2332"            # near-black navy, the only accent
ACCENT_HOVER = "#2c3e50"
ACCENT_DIM = "rgba(26, 35, 50, 0.06)"

BG_PAGE = "#ffffff"
BG_CARD = "#fafafa"           # subtle hover/section background
BG_CARD_SOLID = "#ffffff"
BG_SIDEBAR = "#f5f5f5"

TEXT_PRIMARY = "#0a0a0a"
TEXT_SECONDARY = "#374151"
TEXT_DIM = "#6b7280"
TEXT_FAINT = "#9ca3af"

BORDER = "#e5e7eb"
BORDER_SUBTLE = "#f0f0f0"

GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#d97706"

LINK = ACCENT

# Reusable inline style strings
STYLE_BODY = f"color: {TEXT_PRIMARY}; font-size: 17px; line-height: 1.7;"
STYLE_LABEL = f"color: {TEXT_PRIMARY}; font-size: 1rem; font-weight: 600;"
STYLE_SUB = f"color: {TEXT_SECONDARY}; font-size: 1rem; line-height: 1.65;"
STYLE_DIM = f"color: {TEXT_DIM}; font-size: 0.95rem;"

CHART_COLORS = {
    "primary": ACCENT,
    "secondary": "#6b7280",
    "positive": GREEN,
    "negative": RED,
    "warning": AMBER,
    "grid": BORDER,
    "text": TEXT_PRIMARY,
    "text_dim": TEXT_DIM,
    "fill": "rgba(26, 35, 50, 0.08)",
}


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CUSTOM_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;500;600;700&display=swap"
      rel="stylesheet">
<style>
    /* --- Global --- */
    .stApp {{
        background-color: {BG_PAGE};
        font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
        font-size: 17px;
        line-height: 1.7;
        color: {TEXT_PRIMARY};
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }}

    /* Apply font to text elements */
    .stMarkdown, .stMetric, .stDataFrame,
    .stSelectbox, .stTextInput, .stTextArea, .stSlider,
    .stButton > button, .stTabs,
    .block-container,
    .block-container p, .block-container li,
    .block-container h1, .block-container h2,
    .block-container h3, .block-container h4,
    .block-container label,
    .block-container td, .block-container th,
    .block-container a, .block-container input,
    .block-container textarea, .block-container select,
    .block-container span:not([data-testid="stIconMaterial"]) {{
        font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    }}

    /* --- Body text: 17px, near-black, comfortable line-height --- */
    .block-container .stMarkdown p,
    .block-container .stMarkdown li {{
        color: {TEXT_PRIMARY};
        font-size: 17px;
        line-height: 1.7;
        font-weight: 400;
    }}
    .block-container .stMarkdown strong,
    .block-container .stMarkdown b {{
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    .block-container .stMarkdown h2,
    .block-container .stMarkdown h3,
    .block-container .stMarkdown h4 {{
        color: {ACCENT};
    }}
    .block-container .stMarkdown pre,
    .block-container .stMarkdown code,
    .block-container .stCode {{
        font-size: 14px !important;
        line-height: 1.5 !important;
        background: {BG_CARD};
        color: {TEXT_PRIMARY};
        border-radius: 4px;
    }}
    [data-testid="stWidgetLabel"][aria-hidden="true"],
    .stSelectbox [data-testid="stWidgetLabel"]:empty {{
        display: none !important;
    }}
    .block-container .stElementContainer {{
        margin-bottom: 0;
    }}

    /* --- Headings --- */
    .block-container h1 {{
        color: {TEXT_PRIMARY};
        font-size: 1.9rem;
        font-weight: 600;
        line-height: 1.2;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }}
    .block-container h2 {{
        color: {TEXT_PRIMARY};
        font-size: 1.6rem;
        font-weight: 600;
        line-height: 1.25;
        letter-spacing: -0.01em;
        margin-top: 2rem;
    }}
    .block-container h3 {{
        color: {TEXT_PRIMARY};
        font-size: 1.25rem;
        font-weight: 600;
        line-height: 1.3;
        border-bottom: 1px solid {BORDER};
        padding-bottom: 8px;
        margin-top: 1.5rem;
    }}
    .block-container h4 {{
        color: {TEXT_PRIMARY};
        font-size: 1.05rem;
        font-weight: 600;
        line-height: 1.35;
    }}

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {{
        background-color: {BG_SIDEBAR};
        border-right: 1px solid {BORDER};
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {{
        color: {TEXT_PRIMARY} !important;
        font-size: 15px;
    }}

    /* --- Metric cards --- */
    div[data-testid="stMetric"] {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 12px 16px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: {ACCENT};
        box-shadow: 0 2px 8px rgba(26, 35, 50, 0.06);
    }}
    div[data-testid="stMetric"] label {{
        color: {TEXT_DIM} !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-size: 1.4rem !important;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}

    /* --- Captions and helper text --- */
    .stCaption, [data-testid="stCaption"] {{
        color: {TEXT_DIM} !important;
        font-size: 14px !important;
    }}

    /* --- Notification (info / warning / error) --- */
    [data-testid="stNotification"] {{
        background: {BG_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px;
    }}
    [data-testid="stNotification"] p {{
        color: {TEXT_PRIMARY} !important;
        font-size: 15px !important;
    }}

    /* --- DataFrames --- */
    .stDataFrame {{
        border: 1px solid {BORDER};
        border-radius: 8px;
    }}

    /* --- Expander --- */
    [data-testid="stExpander"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        background: {BG_CARD_SOLID} !important;
        margin-bottom: 8px !important;
    }}
    [data-testid="stExpander"] details summary {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: {TEXT_PRIMARY} !important;
        padding: 14px 18px !important;
    }}
    [data-testid="stExpander"] details summary:hover {{
        color: {ACCENT} !important;
        background: {BG_CARD};
    }}
    [data-testid="stExpander"] svg {{
        color: {TEXT_DIM} !important;
    }}
    [data-testid="stExpander"] .stMarkdown p,
    [data-testid="stExpander"] .stMarkdown li {{
        color: {TEXT_PRIMARY} !important;
        font-size: 16px;
        line-height: 1.7;
    }}

    /* --- Buttons --- */
    .stButton > button {{
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid {BORDER};
        background: {BG_CARD_SOLID};
        color: {TEXT_PRIMARY};
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
    }}
    .stButton > button[kind="primary"] {{
        background: {ACCENT};
        color: #ffffff;
        border-color: {ACCENT};
    }}
    .stButton > button[kind="primary"]:hover {{
        background: {ACCENT_HOVER};
        border-color: {ACCENT_HOVER};
        color: #ffffff;
    }}
    .stButton > button:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
    }}

    /* --- Tabs --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        border-bottom: 1px solid {BORDER};
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {TEXT_DIM};
        font-size: 15px;
        font-weight: 500;
        background: transparent;
        border-radius: 6px 6px 0 0;
        padding: 8px 18px;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {ACCENT};
        background: {BG_CARD};
    }}
    .stTabs [aria-selected="true"] {{
        color: {ACCENT} !important;
        font-weight: 600;
        border-bottom: 2px solid {ACCENT} !important;
    }}

    /* --- Selectbox / inputs / date pickers --- */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input {{
        background: {BG_CARD_SOLID};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
    }}
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div:focus-within,
    .stTextArea > div > div:focus-within,
    .stDateInput > div > div:focus-within {{
        border-color: {ACCENT};
    }}
    /* BaseWeb popover (selectbox dropdown menu) */
    [data-baseweb="popover"] {{
        background: {BG_CARD_SOLID} !important;
    }}
    [data-baseweb="menu"] li {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* --- Links --- */
    a {{
        color: {LINK};
        text-decoration: none;
        border-bottom: 1px solid {BORDER};
        transition: border-color 0.15s ease;
    }}
    a:hover {{
        border-bottom-color: {ACCENT};
    }}

    /* --- Layout --- */
    .block-container {{
        padding-top: 2rem;
        max-width: 1100px;
        margin-left: auto;
        margin-right: auto;
    }}

    /* --- Charts --- */
    iframe {{
        border-radius: 8px;
    }}

    /* --- Hide "main" label in sidebar nav (single page app) --- */
    [data-testid="stSidebarNav"] {{
        display: none;
    }}

    /* --- Focus ring --- */
    .stButton > button:focus-visible,
    .stSelectbox > div > div:focus-visible,
    .stTextInput > div > div > input:focus-visible {{
        outline: 2px solid {ACCENT};
        outline-offset: 2px;
    }}
</style>
"""


def inject_css() -> None:
    """Inject the custom CSS into the current Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent page header with optional subtitle."""
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(
            f'<div style="color: {TEXT_SECONDARY}; font-size: 17px; '
            f'margin-bottom: 1.25rem;">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def show_chart(fig, height: int = 450) -> None:
    """Render a Plotly figure inside an HTML iframe.

    Streamlit's native ``st.plotly_chart`` can render with width=0 when
    placed inside a collapsed expander -- the chart appears as a sliver
    on first open. Routing through ``components.html`` avoids that.
    """
    import streamlit.components.v1 as components

    html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    wrapper = (
        f'<div style="background: {BG_CARD_SOLID}; border: 1px solid {BORDER}; '
        f'border-radius: 8px; padding: 8px;">{html}</div>'
    )
    components.html(wrapper, height=height + 20, scrolling=False)


def card(content_html: str, border_color: str = BORDER) -> str:
    """Wrap HTML content in a thin-border card and return the markup."""
    return (
        f'<div style="background: {BG_CARD_SOLID}; border: 1px solid {border_color}; '
        f'border-radius: 8px; padding: 1.1rem 1.4rem; margin-bottom: 0.75rem;">'
        f'{content_html}</div>'
    )


def sidebar_logo(project_root: Path | None = None) -> None:
    """Render the Merewether logo at the top of the sidebar."""
    logo_path = (
        project_root / "app" / "static" / "logo_m.png"
        if project_root
        else _DEFAULT_LOGO
    )
    if logo_path.exists():
        b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.sidebar.markdown(
            f"""
            <div style="text-align: center; padding: 1rem 0 1.25rem 0;">
                <img src="data:image/png;base64,{b64}" width="160"
                     style="border-radius: 4px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.title("Merewether")
