import logging
from datetime import datetime, timedelta

import pendulum
from airflow.sdk import dag, task
from shared.tasks import transform_and_load
from nyc311.utils.log import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_daily_ingest",
    schedule="0 0 * * *",
    start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/New_York")),
    catchup=False,
    tags=["nyc311", "daily"],
)
def nyc_311_daily_ingest():
    @task()
    def get_date_str(logical_date=None) -> str:
        return logical_date.replace(tzinfo=None).strftime("%Y-%m-%d")

    @task()
    def ingest(date_str=None) -> dict:
        from nyc311.ingestion.ingest import ingest_nyc311_requests
        s3_key = f"bronze/daily/date={date_str}"
        logger.info(f"Starting daily ingest | date={date_str}, s3_key={s3_key}")
        return {"s3_key": s3_key, "latest_created_date": str(ingest_nyc311_requests(s3_key=s3_key))}

    date_str = get_date_str()
    ingest_result = ingest(date_str=date_str)
    transform_and_load(ingest_result)


@dag(
    dag_id="nyc_311_backfill",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/New_York")),
    catchup=False,
    tags=["nyc311", "backfill"],
)
def nyc_311_backfill():
    @task()
    def get_date_str(logical_date=None) -> str:
        return logical_date.replace(tzinfo=None).strftime("%Y-%m-%d")

    @task()
    def ingest(date_str=None) -> dict:
        from nyc311.ingestion.ingest import ingest_nyc311_requests
        start_date = datetime.strptime(date_str, "%Y-%m-%d")
        s3_key = "bronze/historical"
        logger.info(f"Starting backfill | start_date={start_date}, s3_key={s3_key}")
        return {"s3_key": s3_key, "latest_created_date": str(ingest_nyc311_requests(s3_key=s3_key, start_date=start_date))}

    date_str = get_date_str()
    ingest_result = ingest(date_str=date_str)
    transform_and_load.override(
        retries=3,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
    )(ingest_result)


nyc_311_daily_ingest()
nyc_311_backfill()
