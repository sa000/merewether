# Merewether Investment — Data Science Proposal

A small Streamlit app written as a working proposal for the data
scientist role at [Merewether Investment Management](https://merewetherinvestment.com).
Rather than a slide deck, the app demonstrates concretely how the
candidate thinks about data plumbing, AI, and prioritization at a
firm taking its first thoughtful step into data science.

Everything in the app runs from public data sources and a single
Anthropic API key.

## What's in it

A single page with a hero, a table of contents, and eight collapsible
sections. Four are narrative; three are interactive demos; one is a
placeholder for the next iteration.

| # | Section                       | Type        |
|---|-------------------------------|-------------|
| 1 | About Me                      | Narrative   |
| 2 | Why I'm Building This         | Narrative   |
| 3 | Short-Term Goals (90 days)    | Narrative   |
| 4 | Long-Term Goals               | Narrative   |
| 5 | **Data Explorer**             | Interactive |
| 6 | **AI Data Chat**              | Interactive |
| 7 | **AI Trend Post-Mortem**      | Interactive |
| 8 | Transcript Call Analysis      | Placeholder |

**Data Explorer.** A dropdown over five series — Apple stock and
corn futures (Yahoo Finance), and US GDP, CPI, and unemployment
(FRED). Each shows a Plotly time-series chart and six summary stats.

**AI Data Chat.** Natural-language Q&A over the inventory, grounded
on the catalog so the model cannot invent sources. Powered by Claude
Haiku 4.5.

**AI Trend Post-Mortem.** Pick an asset and a date window. Claude
Haiku 4.5 with web search returns a brief explaining what drove the
move, with inline citations. Four pre-filled examples are included.

**Transcript Call Analysis** is a placeholder describing the next
natural extension — the section explains the design without being
implemented yet.

## Tech stack

- Python 3.11+
- [Streamlit](https://streamlit.io) for the UI
- [Plotly](https://plotly.com/python/) for charts
- [yfinance](https://github.com/ranaroussi/yfinance) for equity and
  futures prices
- The public [FRED chart-export endpoint](https://fred.stlouisfed.org/)
  for macro series (no API key required)
- The [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
  for AI features

## Run it locally

```bash
git clone https://github.com/sa000/merewether.git
cd merewether
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set the API key (only needed for the two AI sections)
echo 'ANTHROPIC_API_KEY="sk-ant-..."' > .env

streamlit run app/main.py
```

The Data Explorer and the four narrative sections work without an
API key. The AI sections render their UI but disable the submit
button until a key is set.

## Deploy to Streamlit Community Cloud

1. Push this repository to a public GitHub repo.
2. Visit [share.streamlit.io](https://share.streamlit.io), connect
   the repo, and point it at `app/main.py`.
3. In the Streamlit Cloud dashboard, open **Settings → Secrets** and
   add:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

4. The committed `.streamlit/config.toml` carries the light theme
   over to the deployed site automatically.

## Project layout

```
merewether/
  README.md
  requirements.txt
  .streamlit/
    config.toml                 # light theme (committed)
    secrets.toml.example        # template
  app/
    main.py                     # hero + TOC + 8 expander sections
    style.py                    # design tokens, CSS, helpers
    charts.py                   # Plotly chart builders
    data_sources.py             # fetch_yahoo, fetch_fred, INVENTORY
    data_chat.py                # AI data chat SDK wrapper
    trend_analyst.py            # AI trend post-mortem SDK wrapper
    sections/
      __init__.py               # require_api_key + .env loader
      narrative.py              # markdown-backed narrative renderers
      data_explorer.py          # interactive Data Explorer
      data_chat.py              # interactive AI Data Chat
      trend_postmortem.py       # interactive Trend Post-Mortem
    static/
      logo_m.png
    content/
      about.md
      why.md
      short_term.md
      long_term.md
      transcript_placeholder.md
```
