from datetime import datetime

from sqlalchemy import select

from src.db.models import PipelineStepRun
from src.db.session import get_db_session


def create_pipeline_step_run(dag_id: str, step_name: str, status: str, started_at: datetime,
                             finished_at: datetime, num_records_in: int, num_records_out: int,
                             latest_record_created_date: datetime,
                             error_message: str = None):
    pipeline_step_run = PipelineStepRun(
        dag_id=dag_id,
        step_name=step_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        num_records_in=num_records_in,
        num_records_out=num_records_out,
        error_message=error_message,
        latest_record_created_date=latest_record_created_date
    )

    with get_db_session() as session:
        session.add_all([pipeline_step_run])
        session.flush()
        session.commit()

        return pipeline_step_run.pipeline_step_run_id


def save_pipeline_step_run(pipeline_step_run: PipelineStepRun):
    with get_db_session() as session:
        session.add_all([pipeline_step_run])
        session.flush()
        session.commit()

        return pipeline_step_run.pipeline_step_run_id


def get_latest_pipeline_step_run_by_step_name(step_name: str):
    with get_db_session() as session:
        stmt = select(PipelineStepRun) \
            .order_by(PipelineStepRun.finished_at.desc()) \
            .where(PipelineStepRun.step_name == step_name) \
            .limit(1)

        return session.execute(stmt).scalar_one_or_none()
