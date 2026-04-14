import os
from functools import lru_cache

from sqlmodel import create_engine


@lru_cache(maxsize=1)
def get_db_engine():
    db_url = os.getenv(
        "APP_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
    )
    return create_engine(db_url, pool_pre_ping=True, future=True)
