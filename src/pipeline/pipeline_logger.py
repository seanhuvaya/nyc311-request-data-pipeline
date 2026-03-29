from datetime import datetime

from src.db.models import PipelineRun, PipelineStepRun
from src.db.session import get_db_session


def create_pipeline_run(pipeline_name: str):
    pipeline_run = PipelineRun(
        pipeline_name=pipeline_name,
        overall_status="running"
    )

    with get_db_session() as session:
        session.add_all([pipeline_run])
        session.flush()
        session.commit()

        return pipeline_run.pipeline_run_id


def create_pipeline_step_run(pipeline_run_id: int, dag_id: str, step_name: str, status: str, started_at: datetime,
                             finished_at: datetime, num_records_in: int, num_records_out: int,
                             error_message: str = None):
    pipeline_step_run = PipelineStepRun(
        pipeline_run_id=pipeline_run_id,
        dag_id=dag_id,
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        num_records_in=num_records_in,
        num_records_out=num_records_out,
        error_message=error_message
    )

    with get_db_session() as session:
        session.add_all([pipeline_step_run])
        session.flush()
        session.commit()

        return pipeline_step_run.pipeline_step_run_id


def save_pipeline_run(pipeline_run: PipelineRun):
    with get_db_session() as session:
        session.add_all([pipeline_run])
        session.flush()
        session.commit()

        return pipeline_run.pipeline_run_id


def save_pipeline_step_run(pipeline_step_run: PipelineStepRun):
    with get_db_session() as session:
        session.add_all([pipeline_step_run])
        session.flush()
        session.commit()

        return pipeline_step_run.pipeline_step_run_id
