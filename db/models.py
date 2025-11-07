from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from db.base import Base


class SrcTicker(Base):
    __tablename__ = "src_tickers"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(128))
    source = Column(String(64), default="AlphaVantage", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("CompanyInfo", back_populates="ticker", uselist=False, cascade="all,delete-orphan")
    prices = relationship("PriceData", back_populates="ticker", cascade="all,delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="ticker", cascade="all,delete-orphan")


class CompanyInfo(Base):
    __tablename__ = "company_info"
    __table_args__ = (UniqueConstraint("ticker_id", name="uq_company_ticker"),)

    id = Column(Integer, primary_key=True)
    ticker_id = Column(Integer, ForeignKey("src_tickers.id"), nullable=False)
    name = Column(String(128))
    sector = Column(String(128))
    market_cap = Column(Float)

    ticker = relationship("SrcTicker", back_populates="company")


class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__ = (UniqueConstraint("ticker_id", "date", name="uq_price_ticker_date"),)

    id = Column(Integer, primary_key=True)
    ticker_id = Column(Integer, ForeignKey("src_tickers.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 6), nullable=False)
    high = Column(Numeric(18, 6), nullable=False)
    low = Column(Numeric(18, 6), nullable=False)
    close = Column(Numeric(18, 6), nullable=False)
    volume = Column(Float, nullable=False)

    ticker = relationship("SrcTicker", back_populates="prices")


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    __table_args__ = (UniqueConstraint("ticker_id", "date", name="uq_indicator_ticker_date"),)

    id = Column(Integer, primary_key=True)
    ticker_id = Column(Integer, ForeignKey("src_tickers.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    rsi = Column(Float)
    sma = Column(Float)
    ema = Column(Float)

    ticker = relationship("SrcTicker", back_populates="indicators")


class ApiLog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ticker = Column(String(16), nullable=False)
    api_status = Column(String(32), nullable=False)
    request_time = Column(Float, nullable=False)