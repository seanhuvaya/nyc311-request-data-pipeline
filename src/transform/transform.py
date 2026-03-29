import logging

from pyspark.sql import DataFrame, SparkSession

from src.extract.metadata import get_s3_key_by_pipeline_run_id
from src.transform.cleaning import cast_column_types, drop_irrelevant_columns, impute_categorical_fields, \
    impute_coordinates
from src.utils.config import settings

logger = logging.getLogger(__name__)


def transform_nyc311_data(pipeline_run_id: int) -> DataFrame:
    s3_key = get_s3_key_by_pipeline_run_id(pipeline_run_id=pipeline_run_id)
    logger.info(f"Retrieved s3_key: {s3_key}")

    spark = SparkSession.builder \
        .appName("NYC311Transform") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.4.3") \
        .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID) \
        .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
        .getOrCreate()

    df = spark.read.parquet(f"s3a://{settings.AWS_S3_BUCKET}/{s3_key}")

    df = cast_column_types(df)
    df = drop_irrelevant_columns(df)
    df = impute_categorical_fields(df)
    return impute_coordinates(df)
