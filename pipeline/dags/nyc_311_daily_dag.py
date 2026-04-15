import logging
from datetime import datetime, timezone

import pendulum
from airflow.sdk import dag, task
from spark_jobs.session import get_spark_session
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

    @task()
    def transform_and_save_requests():
        from spark_jobs.transforms.clean_nyc311_requests import clean_nyc311_requests
        from spark_jobs.transforms.enrich_nyc311_requests import enrich_nyc311_requests

        spark = get_spark_session(app_name="nyc_311_historical_backfill", s3_endpoint="http://minio:9000",
                                  access_key="changemeuser", secret_key="changemepass")

        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        df = spark.read.csv(f"s3a://nyc311-data/raw/daily/date={date}/*.csv",
                            header=True,
                            inferSchema=True)

        cleaned_df = clean_nyc311_requests(df)
        enriched_df = enrich_nyc311_requests(cleaned_df)

        enriched_df.write.mode("overwrite") \
            .parquet(f"s3a://nyc311-data/silver/daily/date={date}/")

        spark.stop()

    @task
    def build_gold_nyc311_requests_daily():
        from spark_jobs.gold.build_nyc311_requests_daily import build_nyc311_requests_daily
        spark = get_spark_session(app_name="nyc_311_historical_backfill", s3_endpoint="http://minio:9000",
                                  access_key="changemeuser", secret_key="changemepass")
        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        df = spark.read.parquet(f"s3a://nyc311-data/silver/daily/date={date}/")
        build_nyc311_requests_daily(df)

        spark.stop()

    incremental_ingest() >> transform_and_save_requests() >> build_gold_nyc311_requests_daily()


nyc_311_daily_ingest()
