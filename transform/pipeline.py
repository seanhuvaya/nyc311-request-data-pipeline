import logging

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession

from config import settings
from db import get_db_session
from models.extraction_metadata import ExtractionStatus, ExtractMetadata
from utils import upload_data_to_s3
from validate import perform_validation
from .cleaning import handle_missing_values
from .config import TransformationConfig
from .paths import get_raw_file_paths, get_silver_file_key
from .schema import convert_data_types

logger = logging.getLogger(__name__)


def transform_dataframe(df: DataFrame, config: TransformationConfig) -> DataFrame:
    """Main transformation pipeline."""
    df = convert_data_types(df)
    df = handle_missing_values(df, config)
    return df


def process_raw_to_silver():
    """Orchestrate raw → silver transformation for all completed extractions."""
    spark = (
        SparkSession.builder
        .appName("NYC311 Raw to Silver Transformation")
        .master("local[*]")  # Change to yarn/k8s in production
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.4.1,org.apache.hadoop:hadoop-common:3.4.1")
        .getOrCreate()
    )

    config = TransformationConfig()

    try:
        raw_paths = get_raw_file_paths()

        if not raw_paths:
            logger.info("No completed raw files found to process.")
            return

        logger.info(f"Found {len(raw_paths)} raw files to transform.")

        with get_db_session() as session:
            for path in raw_paths:
                logger.info(f"Processing file: {path}")

                df_raw = spark.read.format("parquet").load(path)

                df_transformed = transform_dataframe(df_raw, config)

                # Convert to Pandas only for validation (consider custom Spark validation later)
                df_pandas = df_transformed.toPandas()

                perform_validation(df_pandas, "transform")

                # Determine output partition
                max_created_date = df_pandas["created_date"].max()
                date_str = max_created_date.strftime("%Y-%m-%d")
                file_key = get_silver_file_key(date_str)

                upload_data_to_s3(df_pandas, settings.AWS_S3_BUCKET, file_key)

                logger.info(f"Successfully wrote silver data to s3://{settings.AWS_S3_BUCKET}/{file_key}")

                # Mark as processed in metadata
                # Note: You may want to link by extraction_id instead of updating all
                # For now keeping your original logic
                extraction_record = session.query(ExtractMetadata).filter(
                    ExtractMetadata.latest_record_created_date == max_created_date.date()
                ).first()

                if extraction_record:
                    extraction_record.status = ExtractionStatus.PROCESSED.value
                    session.flush()

    except Exception as e:
        logger.exception("Silver transformation pipeline failed")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()
    process_raw_to_silver()
