import logging
from datetime import datetime

from airflow.sdk import dag, task, get_current_context

from transform.transform import transform_nyc311_data

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
        s3_key = dag_run.conf["s3_key"]

        logger.info(f"Retrieved s3_key: {s3_key}")

        df = transform_nyc311_data(s3_key)

        logger.info(f"Shape: ({df.count()}, {len(df.columns)})")

    run_nyc311_transformation()


nyc311_transformation_dag()
