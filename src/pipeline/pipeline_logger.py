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

        return pipeline_run.pipeline_run_id


def save_pipeline_run(pipeline_run: PipelineRun):
    with get_db_session() as session:
        session.add_all([pipeline_run])
        session.flush()

        return pipeline_run.pipeline_run_id


def save_pipeline_step_run(pipeline_step_run: PipelineStepRun):
    with get_db_session() as session:
        session.add_all([pipeline_step_run])
        session.flush()

        return pipeline_step_run.pipeline_step_run_id
