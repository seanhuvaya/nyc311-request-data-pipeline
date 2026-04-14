from sqlmodel import SQLModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from utils.db import get_db_engine
from .models import IngestionMetadata


def ensure_pipeline_tables():
    with Session(get_db_engine()) as session:
        session.execute(text("CREATE SCHEMA IF NOT EXISTS metadata"))
        session.commit()

    SQLModel.metadata.create_all(get_db_engine())


if __name__ == "__main__":
    ensure_pipeline_tables()
