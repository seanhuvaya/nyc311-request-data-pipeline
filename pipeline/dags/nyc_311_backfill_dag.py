import logging

from airflow.sdk import dag, task
from datetime import datetime

from utils.logging import setup_logging

from metadata.init import ensure_pipeline_tables
from ingestion.historical_ingest import backfill_nyc311_requests

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_historical_backfill",
    start_date=datetime(2026, 4, 13),
    schedule="@once",
    catchup=False,
    tags=["nyc311", "historical", "backfill"],
)
def nyc_311_historical_backfill():
    @task
    def ensure_metadata():
        logger.info("Ensuring metadata tables exist")
        ensure_pipeline_tables()

    @task
    def historical_backfill():
        logger.info("Running historical backfill")
        backfill_nyc311_requests()

    ensure_metadata() >> historical_backfill()


nyc_311_historical_backfill()
