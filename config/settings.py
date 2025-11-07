from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    alpha_vantage_key: str = os.getenv("ALPHAVANTAGE_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///alphavantage.db")
    retry_attempts: int = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
    retry_backoff: float = float(os.getenv("API_RETRY_BACKOFF", "1.5"))

    def validate(self) -> None:
        if not self.alpha_vantage_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY must be set in the .env file.")


settings = Settings()