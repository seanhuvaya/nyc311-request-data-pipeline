from datetime import datetime

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import dag, task

from pipeline.pipeline_logger import create_pipeline_run


@dag(
    dag_id="nyc311_pipeline_run",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_pipeline_run():
    @task()
    def start_pipeline_run():
        return create_pipeline_run("nyc_311_daily")

    pipeline_run_id = start_pipeline_run()

    trigger_ingestion = TriggerDagRunOperator(
        task_id="trigger_ingestion",
        trigger_dag_id="nyc311_ingestion",
        conf={
            "pipeline_run_id": pipeline_run_id,
        }
    )

    pipeline_run_id >> trigger_ingestion


nyc311_pipeline_run()
