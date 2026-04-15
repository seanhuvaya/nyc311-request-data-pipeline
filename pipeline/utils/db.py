import os
import logging
from functools import lru_cache

from sqlalchemy import text
from sqlmodel import create_engine

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_db_engine():
    db_url = os.getenv(
        "APP_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@postgres:5432/nyc311",
    )
    return create_engine(db_url, pool_pre_ping=True, future=True)


def truncate_table(table_name: str):
    engine = get_db_engine()

    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name}"))
        conn.commit()
