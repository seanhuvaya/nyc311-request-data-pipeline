import logging
from datetime import datetime

import pendulum
from airflow.sdk import dag, task
from shared.spark_tasks import make_transform_task, make_staging_task, build_gold_nyc311_requests_daily, \
    update_watermark
from utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_daily_ingest",
    schedule="0 0 * * *",
    start_date=datetime(2026, 1, 1, tzinfo=pendulum.timezone("America/New_York")),
    catchup=False,
    tags=["nyc311", "daily", "ingest"],
)
def nyc_311_daily_ingest():
    @task()
    def get_logical_date_str(logical_date=None) -> str:
        date = logical_date.replace(tzinfo=None)
        return date.strftime("%Y-%m-%d")

    @task()
    def incremental_ingest(date_str=None) -> dict:
        from ingestion.incremental_ingest import ingest_nyc311_daily_requests

        s3_key = f"bronze/daily/date={date_str}"

        logger.info(f"Starting incremental ingest | logical_date={date_str}, s3_key={s3_key}")
        latest_created_date = ingest_nyc311_daily_requests(s3_key=s3_key)
        logger.info(f"Incremental ingest complete | s3_key={s3_key}")

        return {"s3_key": s3_key, "latest_created_date": str(latest_created_date)}

    @task()
    def get_bronze(ingest_result: dict) -> str:
        return ingest_result["s3_key"]

    @task()
    def get_latest_created_date(ingest_result: dict) -> datetime:
        return ingest_result["latest_created_date"]

    transform = make_transform_task()
    staging = make_staging_task()

    logical_date = get_logical_date_str()
    ingest_result = incremental_ingest(date_str=logical_date)
    bronze = get_bronze(ingest_result)
    latest_date = get_latest_created_date(ingest_result)

    silver = transform(input_glob=f"{bronze}/*.csv", output_path=f"silver/daily/date={logical_date}/")

    bronze >> silver >> staging(silver_path=silver) >> build_gold_nyc311_requests_daily() >> \
    update_watermark(latest_created_date=latest_date)


nyc_311_daily_ingest()
