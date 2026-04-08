The first 90 days are about earning trust by removing friction in workflows you already have. Before proposing anything new, I would spend time understanding how research, trading, and operations actually move data around today, and look for the small interventions that pay back quickly without asking anyone to change how they work.

## First 90 days

- **Inventory existing data sources.** Document where each feed lives, who owns it, how often it updates, and what depends on it. One source of truth, kept in version control, that everyone can read.
- **A small data-quality dashboard.** A single internal page where analysts can see, at a glance, whether the inputs they rely on are fresh, complete, and consistent with yesterday.
- **Python helpers around existing market data feeds.** Thin wrappers so a research question that currently takes an afternoon takes a few minutes — same data, less friction.
- **Internal LLM-powered Q&A over research notes and meeting transcripts.** Read-only, scoped to the firm's own materials, so analysts can find what was said about a name six months ago without grepping through a shared drive.
- **A lightweight feature store.** Parquet files in S3 or a small SQLite database — whichever fits the firm's infrastructure — so any future model shares the same inputs as the last one.
- **Basic monitoring and alerting on existing pipelines.** Quiet on the good days, loud on the bad ones.
- **A weekly five-minute data demo.** A short walkthrough — Loom or live — so the rest of the firm sees what is possible without needing a long meeting to find out.

The goal of the first 90 days is *evidence*, not architecture. Small wins the rest of the firm can see and use.
