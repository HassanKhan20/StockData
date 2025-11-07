from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from db.base import Base

engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def init_db() -> None:
    from db import models  # noqa: F401  (ensures tables are registered)

    Base.metadata.create_all(bind=engine)