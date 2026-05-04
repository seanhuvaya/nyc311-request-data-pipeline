import logging
from datetime import datetime, timezone

import pendulum
from airflow.sdk import dag, task
from spark_jobs.session import get_spark_session
from utils.logging import setup_logging

from utils.config import settings

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

        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        s3_key = f"bronze/daily/date={date}"
        ingest_nyc311_daily_requests(s3_key=s3_key)

        return s3_key

    @task()
    def transform_and_save_requests(s3_bronze_key: str):
        from spark_jobs.transforms.clean_nyc311_requests import clean_nyc311_requests
        from spark_jobs.transforms.enrich_nyc311_requests import enrich_nyc311_requests

        spark = get_spark_session(app_name="nyc_311_historical_backfill", use_s3=True)

        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        df = spark.read.csv(f"s3a://{settings.s3_bucket_name}/{s3_bronze_key}/*.csv",
                            header=True,
                            inferSchema=True)

        cleaned_df = clean_nyc311_requests(df)
        enriched_df = enrich_nyc311_requests(cleaned_df)

        s3_silver_key = f"silver/daily/date={date}/"
        enriched_df.write.mode("overwrite") \
            .parquet(f"s3a://{settings.s3_bucket_name}/{s3_silver_key}")

        spark.stop()

        return s3_silver_key

    @task
    def build_staging_nyc311_requests_daily(s3_silver_key: str):
        from spark_jobs.staging.nyc311_requests_daily_staging import build_nyc311_requests_daily_staging_tables
        spark = get_spark_session(app_name="nyc_311_historical_backfill", use_s3=True, use_postgres=True)
        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        df = spark.read.parquet(f"s3a://{settings.s3_bucket_name}/{s3_silver_key}/")
        build_nyc311_requests_daily_staging_tables(df)

        spark.stop()

    @task
    def build_gold_nyc311_requests_daily():
        from spark_jobs.gold.nyc311_requests_daily_gold import build_gold_nyc311_requests_daily
        build_gold_nyc311_requests_daily()

    s3_bronze = incremental_ingest()
    s3_silver = transform_and_save_requests(s3_bronze_key=s3_bronze)
    s3_bronze >> s3_silver >> build_staging_nyc311_requests_daily(s3_silver_key=s3_silver) >> build_gold_nyc311_requests_daily()


nyc_311_daily_ingest()
