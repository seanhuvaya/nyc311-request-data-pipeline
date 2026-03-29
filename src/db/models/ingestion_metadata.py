from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from src.db.models import Base


class IngestionMetadata(Base):
    __tablename__ = "ingestion_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)

    num_records_pulled = Column(Integer, nullable=False, default=0)
    latest_record_created_date = Column(DateTime(timezone=True))

    s3_key = Column(String)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.pipeline_run_id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
