import logging

from pyspark.sql import DataFrame, SparkSession

from src.transform.cleaning import cast_column_types, drop_irrelevant_columns, impute_categorical_fields, \
    impute_coordinates
from src.utils.config import settings

logger = logging.getLogger(__name__)


def transform_nyc311_data(s3_key: str) -> DataFrame:
    spark = SparkSession.builder \
        .appName("NYC311Transform") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID) \
        .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
        .getOrCreate()

    df = spark.read.parquet(f"s3a://{settings.AWS_S3_BUCKET}/{s3_key}")

    df = cast_column_types(df)
    df = drop_irrelevant_columns(df)
    df = impute_categorical_fields(df)
    return impute_coordinates(df)
