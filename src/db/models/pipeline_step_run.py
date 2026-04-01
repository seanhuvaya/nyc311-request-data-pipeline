from sqlalchemy import Integer, Column, String, DateTime

from src.db.models import Base


class PipelineStepRun(Base):
    __tablename__ = "pipeline_step_runs"

    pipeline_step_run_id = Column(Integer, primary_key=True, autoincrement=True)
    dag_id = Column(String, nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="running")
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    num_records_in = Column(Integer)
    num_records_out = Column(Integer)
    error_message = Column(String)
    s3_file_key = Column(String)
