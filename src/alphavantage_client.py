from __future__ import annotations

import time
from typing import Any, Dict, Tuple

import requests

from config.settings import settings


class AlphaVantageClient:
    base_url = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, retries: int | None = None, backoff: float | None = None) -> None:
        self.api_key = api_key or settings.alpha_vantage_key
        self.retries = retries or settings.retry_attempts
        self.backoff = backoff or settings.retry_backoff

    def _request(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        params = {**params, "apikey": self.api_key}
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            start = time.perf_counter()
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                elapsed = time.perf_counter() - start
                response.raise_for_status()
                payload = response.json()
                if "Note" in payload:
                    raise RuntimeError(payload["Note"])
                if "Error Message" in payload:
                    raise RuntimeError(payload["Error Message"])
                return payload, elapsed
            except Exception as exc:
                last_error = exc
                time.sleep(self.backoff * attempt)

        raise RuntimeError(f"AlphaVantage request failed after {self.retries} attempts: {last_error}") from last_error

    def get_company_overview(self, symbol: str) -> Tuple[Dict[str, Any], float]:
        params = {"function": "OVERVIEW", "symbol": symbol}
        return self._request(params)

    def get_daily_time_series(self, symbol: str, outputsize: str = "compact") -> Tuple[Dict[str, Any], float]:
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,
        }
        payload, elapsed = self._request(params)
        if "Time Series (Daily)" not in payload:
            raise RuntimeError(f"No daily time series returned for {symbol}")
        return payload["Time Series (Daily)"], elapsed