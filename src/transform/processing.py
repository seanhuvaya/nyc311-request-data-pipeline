import logging

from pyspark.sql import DataFrame

from src.transform.cleaning import cast_column_types, drop_irrelevant_columns, impute_categorical_fields, \
    impute_coordinates

logger = logging.getLogger(__name__)


def process_nyc311_daily_data(df: DataFrame) -> DataFrame:
    df = df.dropDuplicates(["unique_key"])
    df = cast_column_types(df)
    df = drop_irrelevant_columns(df)
    df = impute_categorical_fields(df)
    df = impute_coordinates(df)
    return df
