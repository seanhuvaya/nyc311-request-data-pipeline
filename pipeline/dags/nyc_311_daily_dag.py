import logging

import pendulum
from airflow.sdk import dag, task
from utils.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_daily_ingest",
    schedule="0 3 * * *",  # Runs at 3 AM every day
    start_date=pendulum.datetime(2026, 4, 13, 3, 0, tz="America/New_York"),
    catchup=False,
    tags=["nyc311", "daily", "ingest"],
)
def nyc_311_daily_ingest():
    @task()
    def incremental_ingest():
        from ingestion.incremental_ingest import ingest_nyc311_daily_requests

        ingest_nyc311_daily_requests()

    incremental_ingest()


nyc_311_daily_ingest()
