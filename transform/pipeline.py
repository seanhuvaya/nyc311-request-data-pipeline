import logging
import os

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from utils.config import settings
from validate import perform_spark_validation_sample

from .cleaning import handle_missing_values
from .config import TransformationConfig
from .paths import (
    get_silver_parquet_dir_s3a,
    list_pending_transform_jobs,
    mark_transform_processed,
)
from .schema import convert_data_types

logger = logging.getLogger(__name__)


def transform_dataframe(df: DataFrame, config: TransformationConfig) -> DataFrame:
    """Main transformation pipeline."""
    df = convert_data_types(df)
    df = handle_missing_values(df, config)
    return df


def build_spark_session() -> SparkSession:
    """SparkSession with S3A and credentials from settings."""
    master = os.environ.get("SPARK_MASTER", "local[*]")
    return (
        SparkSession.builder.appName("NYC311 Raw to Silver Transformation")
        .master(master)
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config(
            "spark.jars.packages",
            "org.apache.hadoop:hadoop-aws:3.4.1,org.apache.hadoop:hadoop-common:3.4.1",
        )
        .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID)
        .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY)
        .getOrCreate()
    )


def write_silver_parquet(df: DataFrame, silver_s3a_uri: str) -> None:
    """Write transformed data to silver as Parquet on S3 (Spark-native, distributed)."""
    df.write.mode("overwrite").option("compression", "snappy").parquet(silver_s3a_uri)


def process_raw_to_silver() -> None:
    """Orchestrate raw → silver transformation for pending completed extractions."""
    spark = build_spark_session()
    config = TransformationConfig()

    try:
        jobs = list_pending_transform_jobs()

        if not jobs:
            logger.info("No pending transform jobs.")
            return

        logger.info("Found %d pending transform job(s).", len(jobs))

        for job in jobs:
            logger.info(
                "Transforming extraction_id=%s raw=%s",
                job.extraction_id,
                job.raw_s3_uri,
            )

            df_raw = spark.read.format("parquet").load(job.raw_s3_uri)
            df_transformed = transform_dataframe(df_raw, config)

            perform_spark_validation_sample(df_transformed, "transform")

            silver_uri = get_silver_parquet_dir_s3a(job.partition_date_str)
            write_silver_parquet(df_transformed, silver_uri)

            logger.info(
                "Wrote silver parquet to %s for extraction_id=%s",
                silver_uri,
                job.extraction_id,
            )

            mark_transform_processed(job.extraction_id)

    except Exception:
        logger.exception("Silver transformation pipeline failed")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    from utils.logger import setup_logging

    setup_logging()
    process_raw_to_silver()
