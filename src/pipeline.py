from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, List

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from db.models import ApiLog, CompanyInfo, PriceData, SrcTicker, TechnicalIndicator
from src.alphavantage_client import AlphaVantageClient
from src.indicators import calculate_indicators


class ETLPipeline:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory
        self.client = AlphaVantageClient()

    def run(self, tickers: Iterable[str]) -> None:
        for symbol in tickers:
            self._process_symbol(symbol.upper())

    def _process_symbol(self, symbol: str) -> None:
        session: Session = self.session_factory()
        status = "SUCCESS"
        total_request_time = 0.0

        try:
            ticker = self._get_or_create_ticker(session, symbol)

            company_payload, elapsed = self.client.get_company_overview(symbol)
            total_request_time += elapsed
            self._upsert_company_info(session, ticker, company_payload)

            price_payload, elapsed = self.client.get_daily_time_series(symbol)
            total_request_time += elapsed
            price_rows = self._transform_price_payload(price_payload)
            self._load_price_data(session, ticker.id, price_rows)
            self._refresh_indicators(session, ticker.id)

            session.commit()
            print(f"[OK] Loaded {symbol} ({len(price_rows)} rows)")
        except Exception as exc:
            session.rollback()
            status = "FAILED"
            print(f"[ERROR] {symbol}: {exc}")
        finally:
            self._log_run(session, symbol, status, total_request_time)
            session.commit()
            session.close()

    def _get_or_create_ticker(self, session: Session, symbol: str) -> SrcTicker:
        ticker = session.execute(
            select(SrcTicker).where(SrcTicker.symbol == symbol)
        ).scalar_one_or_none()
        if ticker:
            return ticker

        ticker = SrcTicker(symbol=symbol, source="AlphaVantage")
        session.add(ticker)
        session.flush()
        return ticker

    def _upsert_company_info(self, session: Session, ticker: SrcTicker, payload: Dict) -> None:
        company = session.execute(
            select(CompanyInfo).where(CompanyInfo.ticker_id == ticker.id)
        ).scalar_one_or_none()
        market_cap = self._safe_float(payload.get("MarketCapitalization"))

        if not ticker.name and payload.get("Name"):
            ticker.name = payload["Name"]

        if company:
            company.name = payload.get("Name") or company.name
            company.sector = payload.get("Sector") or company.sector
            company.market_cap = market_cap if market_cap is not None else company.market_cap
        else:
            company = CompanyInfo(
                ticker_id=ticker.id,
                name=payload.get("Name"),
                sector=payload.get("Sector"),
                market_cap=market_cap,
            )
            session.add(company)

    def _transform_price_payload(self, payload: Dict) -> List[Dict]:
        rows: List[Dict] = []
        for date_str, values in payload.items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            rows.append(
                {
                    "date": date,
                    "open": Decimal(values["1. open"]),
                    "high": Decimal(values["2. high"]),
                    "low": Decimal(values["3. low"]),
                    "close": Decimal(values["4. close"]),
                    "volume": float(values["6. volume"]),
                }
            )
        rows.sort(key=lambda r: r["date"])
        return rows

    def _load_price_data(self, session: Session, ticker_id: int, price_rows: List[Dict]) -> None:
        existing_dates = {
            row[0]
            for row in session.execute(
                select(PriceData.date).where(PriceData.ticker_id == ticker_id)
            )
        }

        new_entries = []
        for row in price_rows:
            if row["date"] in existing_dates:
                continue
            new_entries.append(
                PriceData(
                    ticker_id=ticker_id,
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
            )
        if new_entries:
            session.bulk_save_objects(new_entries)

    def _refresh_indicators(self, session: Session, ticker_id: int) -> None:
        price_points = session.execute(
            select(PriceData.date, PriceData.close)
            .where(PriceData.ticker_id == ticker_id)
            .order_by(PriceData.date)
        ).all()

        price_rows = [{"date": row.date, "close": float(row.close)} for row in price_points]
        indicators = calculate_indicators(price_rows)

        session.query(TechnicalIndicator).filter(TechnicalIndicator.ticker_id == ticker_id).delete()

        indicator_rows = [
            TechnicalIndicator(
                ticker_id=ticker_id,
                date=item["date"],
                rsi=item["rsi"],
                sma=item["sma"],
                ema=item["ema"],
            )
            for item in indicators
        ]
        if indicator_rows:
            session.bulk_save_objects(indicator_rows)

    def _log_run(self, session: Session, symbol: str, status: str, request_time: float) -> None:
        session.add(
            ApiLog(
                ticker=symbol,
                api_status=status,
                request_time=round(request_time, 4),
            )
        )

    @staticmethod
    def _safe_float(value) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None