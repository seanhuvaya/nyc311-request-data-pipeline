import logging
from datetime import datetime

from airflow.sdk import task
from spark_jobs.session import get_spark_session
from utils.config import settings
from metadata.service import update_metadata

logger = logging.getLogger(__name__)


def make_spark_session(app_name: str, use_postgres: bool = False):
    """Standardised Spark session factory with shared config."""
    logger.info(f"Creating Spark session | app_name={app_name}, use_postgres={use_postgres}")
    spark = get_spark_session(app_name=app_name, use_s3=True, use_postgres=use_postgres)
    spark.sparkContext.setLogLevel("WARN")
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    logger.info(f"Spark session created | app_name={app_name}")
    return spark


def make_transform_task(**task_kwargs):
    """
    Factory that returns a parameterised @task for the clean→enrich pipeline.

    Usage:
        transform = make_transform_task()          # daily: pass s3_bronze_key at call time
        transform = make_transform_task(retries=3) # historical: add retry policy
    """

    @task(**task_kwargs)
    def transform_and_save_requests(input_glob: str, output_path: str) -> str:
        from spark_jobs.transforms.clean_nyc311_requests import clean_nyc311_requests
        from spark_jobs.transforms.enrich_nyc311_requests import enrich_nyc311_requests

        logger.info(f"Starting transform | input_glob={input_glob}, output_path={output_path}")

        spark = make_spark_session("nyc_311_transform")

        s3_input_path = f"s3a://{settings.s3_bucket_name}/{input_glob}"
        logger.info(f"Reading CSV from S3 | path={s3_input_path}")
        df = spark.read.csv(s3_input_path, header=True, inferSchema=True)
        logger.info(f"CSV loaded | rows={df.count()}, columns={len(df.columns)}")

        logger.info("Applying clean and enrich transforms")
        cleaned_df = clean_nyc311_requests(df)
        enriched_df = enrich_nyc311_requests(cleaned_df)
        logger.info(f"Transform complete | partitions={enriched_df.rdd.getNumPartitions()}")

        s3_output_path = f"s3a://{settings.s3_bucket_name}/{output_path}"
        logger.info(f"Writing parquet to S3 | path={s3_output_path}")
        enriched_df.write.mode("overwrite").parquet(s3_output_path)
        logger.info(f"Parquet write complete | path={s3_output_path}")

        spark.stop()
        logger.info("Spark session stopped")

        return output_path

    return transform_and_save_requests


def make_staging_task(**task_kwargs):
    """Factory for the staging-table builder task."""

    @task(**task_kwargs)
    def build_staging(silver_path: str):
        from spark_jobs.staging.nyc311_requests_daily_staging import (
            build_nyc311_requests_daily_staging_tables,
        )

        logger.info(f"Starting staging build | silver_path={silver_path}")

        spark = make_spark_session("nyc_311_staging", use_postgres=True)

        s3_silver_path = f"s3a://{settings.s3_bucket_name}/{silver_path}"
        logger.info(f"Reading parquet from S3 | path={s3_silver_path}")
        df = spark.read.parquet(s3_silver_path)
        logger.info(f"Parquet loaded | rows={df.count()}, columns={len(df.columns)}")

        logger.info("Building staging tables")
        build_nyc311_requests_daily_staging_tables(df)
        logger.info("Staging tables built successfully")

        spark.stop()
        logger.info("Spark session stopped")

    return build_staging


@task
def build_gold_nyc311_requests_daily():
    logger.info("Starting gold layer build | table=nyc311_requests_daily")
    from spark_jobs.gold.nyc311_requests_daily_gold import build_gold_nyc311_requests_daily
    build_gold_nyc311_requests_daily()
    logger.info("Gold layer build complete | table=nyc311_requests_daily")


@task
def update_watermark(latest_created_date: datetime):
    logger.info(
        f"Updating watermark | pipeline=nyc_311, source=erm2-nwe9, watermark_column=created_date, new_value={latest_created_date}")
    update_metadata(
        pipeline_name="nyc_311",
        source_name="erm2-nwe9",
        watermark_column="created_date",
        watermark_value=latest_created_date,
    )
    logger.info("Watermark updated successfully")
