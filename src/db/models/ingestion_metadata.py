from sqlalchemy import Column, Integer, String, DateTime

from src.db.models import Base


class IngestionMetadata(Base):
    __tablename__ = "ingestion_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)

    num_records_pulled = Column(Integer, nullable=False, default=0)
    latest_record_created_date = Column(DateTime(timezone=True))

    s3_key = Column(String)
