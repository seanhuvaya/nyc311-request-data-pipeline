import logging
from datetime import timedelta, datetime

import pendulum
from airflow.sdk import dag, task
from shared.spark_tasks import make_transform_task, make_staging_task, build_gold_nyc311_requests_daily, \
    update_watermark
from utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_historical_backfill",
    schedule=None,
    start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/New_York")),
    catchup=False,
    tags=["nyc311", "historical", "backfill"],
)
def nyc_311_historical_backfill():
    @task()
    def get_logical_date_str(logical_date=None) -> str:
        date = logical_date.replace(tzinfo=None)
        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"Resolved logical date | date_str={date_str}")
        return date_str

    @task()
    def historical_backfill(date_str=None) -> dict:
        from ingestion.historical_ingest import backfill_nyc311_requests

        start_date = datetime.strptime(date_str, "%Y-%m-%d")
        s3_key = "bronze/historical"

        logger.info(f"Starting historical backfill | logical_date={date_str}, s3_key={s3_key}")
        latest_created_date = backfill_nyc311_requests(s3_key=s3_key, start_date=start_date)
        logger.info(f"Historical backfill complete | s3_key={s3_key}, latest_created_date={latest_created_date}")

        return {"s3_key": s3_key, "latest_created_date": str(latest_created_date)}

    @task()
    def get_bronze(ingest_result: dict) -> str:
        s3_key = ingest_result["s3_key"]
        logger.info(f"Extracted bronze path | s3_key={s3_key}")
        return s3_key

    @task()
    def get_latest_created_date(ingest_result: dict) -> datetime:
        latest_created_date = ingest_result["latest_created_date"]
        logger.info(f"Extracted latest created date | latest_created_date={latest_created_date}")
        return latest_created_date

    # Retry policy is specific to the historical pipeline
    transform = make_transform_task(
        retries=3,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
    )
    staging = make_staging_task()

    logical_date = get_logical_date_str()
    ingest_result = historical_backfill(date_str=logical_date)
    bronze = get_bronze(ingest_result)
    latest_date = get_latest_created_date(ingest_result)

    silver = transform(input_glob=f"{bronze}/*.csv", output_path="silver/historical/")

    bronze >> silver >> staging(silver_path=silver) >> build_gold_nyc311_requests_daily() >> \
    update_watermark(latest_created_date=latest_date)


nyc_311_historical_backfill()
