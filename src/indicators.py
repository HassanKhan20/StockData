from __future__ import annotations

from typing import List, Dict

import pandas as pd


def calculate_indicators(price_rows: List[Dict]) -> List[Dict]:
    """Return RSI, SMA, and EMA aligned with each price row."""
    if not price_rows:
        return []

    df = pd.DataFrame(price_rows)
    df = df.sort_values("date").reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    window = 14
    df["sma"] = df["close"].rolling(window=window).mean()
    df["ema"] = df["close"].ewm(span=window, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    df["rsi"] = 100 - (100 / (1 + rs))

    indicators = []
    for row in df.itertuples(index=False):
        indicators.append(
            {
                "date": row.date,
                "rsi": None if pd.isna(row.rsi) else float(row.rsi),
                "sma": None if pd.isna(row.sma) else float(row.sma),
                "ema": None if pd.isna(row.ema) else float(row.ema),
            }
        )
    return indicators