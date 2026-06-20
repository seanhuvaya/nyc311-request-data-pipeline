import logging
from functools import lru_cache

from sqlalchemy import text
from sqlmodel import create_engine

from nyc311.utils.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_db_engine():
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def run_sql_statements(*sql_statements: str) -> None:
    engine = get_db_engine()

    with engine.connect() as conn:
        for sql in sql_statements:
            conn.execute(text(sql))
            conn.commit()
