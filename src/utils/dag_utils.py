import logging
from datetime import datetime, timezone

from airflow.sdk import get_current_context

from db.models import PipelineStepRun
from pipeline.pipeline_logger import save_pipeline_step_run

logger = logging.getLogger(__name__)


def failure_callback(context, step_name: str):
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    exception = context.get('exception')
    started_at = context["dag_run"].start_date

    logger.error(f"Step '{step_name}' failed in DAG '{dag_id}' on task '{task_id}': {str(exception)}")

    pipeline_step_run = PipelineStepRun(
        dag_id=dag_id,
        step_name=step_name,
        status="failed",
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        error_message=str(exception),
    )

    save_pipeline_step_run(pipeline_step_run)
