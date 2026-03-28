from sqlalchemy import Integer, Column, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship

from src.db.models import Base


class PipelineStepRun(Base):
    __tablename__ = "pipeline_step_runs"

    pipeline_step_run_id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.pipeline_run_id"), nullable=False)
    dag_id = Column(String, nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="running")
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    num_records_in = Column(Integer, nullable=False)
    num_records_out = Column(Integer, nullable=False)
    error_message = Column(String, nullable=False)

    pipeline_run = relationship("PipelineRun", back_populates="pipeline_step_runs")
