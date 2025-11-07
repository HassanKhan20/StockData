<<<<<<< HEAD
# AlphaVantage ETL Project

This project demonstrates a small-but-complete data engineering workflow in Python:

- Fetches daily price and volume data for 10 large-cap tickers through the AlphaVantage API.
- Enriches tickers with company metadata and calculates RSI, SMA, and EMA indicators.
- Persists everything into five normalized tables using SQLAlchemy ORM on any SQL database (defaults to SQLite).
- Logs every run to provide basic observability over API success and latency.

## Features

- Modular folder layout (`config/`, `db/`, `src/`, `scripts/`).
- ORM models for `src_tickers`, `company_info`, `price_data`, `technical_indicators`, and `api_logs`.
- Centralized configuration via `.env`.
- Resilient AlphaVantage client with retry/backoff and request timing.
- Indicator math implemented with pandas to avoid extra API calls.
- Idempotent inserts (per-date dedupe) plus full refresh for technical indicators.

## Requirements

- Python 3.10+
- AlphaVantage API key (free tier works, but respect their rate limits).
- Internet access to call AlphaVantage.

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
=======
