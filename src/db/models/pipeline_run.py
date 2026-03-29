from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from src.db.models import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    pipeline_run_id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_name = Column(String)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime)
    overall_status = Column(String)

    pipeline_step_runs = relationship("PipelineStepRun", back_populates="pipeline_run")
    ingestion_metadata_records = relationship("IngestionMetadata", back_populates="pipeline_run")
