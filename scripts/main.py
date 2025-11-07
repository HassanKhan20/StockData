from config.settings import settings
from db.session import SessionLocal, init_db
from src.pipeline import ETLPipeline

TICKERS = ["AAPL", "MSFT", "TSLA", "NVDA", "GOOG", "AMZN", "META", "JPM", "NFLX", "AMD"]


def main() -> None:
    settings.validate()
    init_db()
    pipeline = ETLPipeline(SessionLocal)
    pipeline.run(TICKERS)


if __name__ == "__main__":
    main()