import logging
from datetime import timedelta, datetime

from airflow.sdk import dag, task
from pyspark.sql import functions as F
from spark_jobs.session import get_spark_session
from utils.logging import setup_logging

from utils.config import settings

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_historical_backfill",
    schedule=None,
    catchup=False,
    tags=["nyc311", "historical", "backfill"],
)
def nyc_311_historical_backfill():
    @task
    def historical_backfill(logical_date=None):
        from ingestion.historical_ingest import backfill_nyc311_requests
        logger.info(f"Running historical backfill from {logical_date}")
        backfill_nyc311_requests(logical_date)

    @task(retries=3, retry_delay=timedelta(minutes=1), retry_exponential_backoff=True)
    def transform_and_save_requests():
        from spark_jobs.transforms.clean_nyc311_requests import clean_nyc311_requests
        from spark_jobs.transforms.enrich_nyc311_requests import enrich_nyc311_requests

        spark = get_spark_session(app_name="nyc_311_historical_backfill", use_s3=True)

        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        df = spark.read.csv(f"s3a://{settings.s3_bucket_name}/raw/historical/*.csv",
                            header=True,
                            inferSchema=True)

        cleaned_df = clean_nyc311_requests(df)
        enriched_df = enrich_nyc311_requests(cleaned_df)

        enriched_df = enriched_df.withColumn("date", F.to_date("created_date"))

        logger.info(f"partitions before write: {enriched_df.rdd.getNumPartitions()}")

        enriched_df.write.mode("overwrite").partitionBy("date").parquet(
            f"s3a://{settings.s3_bucket_name}/silver/historical/")

        spark.stop()

    @task
    def build_staging_nyc311_requests_daily():
        from spark_jobs.staging.nyc311_requests_daily_staging import build_nyc311_requests_daily_staging_tables
        spark = get_spark_session(app_name="nyc_311_historical_backfill", use_s3=True, use_postgres=True)
        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        df = spark.read.parquet(f"s3a://{settings.s3_bucket_name}/silver/historical/")
        build_nyc311_requests_daily_staging_tables(df)

        spark.stop()

    @task
    def build_gold_nyc311_requests_daily():
        from spark_jobs.gold.nyc311_requests_daily_gold import build_gold_nyc311_requests_daily
        build_gold_nyc311_requests_daily()

    historical_backfill() >> transform_and_save_requests() >> build_staging_nyc311_requests_daily() >> build_gold_nyc311_requests_daily()


nyc_311_historical_backfill()
