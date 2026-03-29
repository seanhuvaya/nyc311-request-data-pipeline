import logging
from datetime import datetime
from airflow.sdk import dag, task, get_current_context

from src.transform.transform import transform_nyc311_data

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_transformation",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_transformation_dag():
    @task
    def run_nyc311_transformation():
        context = get_current_context()
        dag_run = context["dag_run"]
        pipeline_run_id = dag_run.conf["pipeline_run_id"]

        df = transform_nyc311_data(pipeline_run_id=pipeline_run_id)

        logger.info(f"Shape: {df.shape}")

        logger.info(
            "Running nyc311 transformation with pipeline_run_id: %s",
            pipeline_run_id,
        )

    run_nyc311_transformation()


nyc311_transformation_dag()
