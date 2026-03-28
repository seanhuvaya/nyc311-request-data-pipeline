from datetime import datetime

from airflow.sdk import dag, task

from extract.incremental import incremental_pull
from src.utils.logger import setup_logging

setup_logging()


@dag(
    dag_id="nyc311_service_requests_dag",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_service_requests_dag():
    @task
    def pull_latest_nyc311_service_requests():
        incremental_pull()

    pull_latest_nyc311_service_requests()


nyc311_service_requests_dag()
