from pyspark.sql import DataFrame
from pyspark.sql.functions import coalesce, col, to_timestamp
from pyspark.sql.types import FloatType, IntegerType

def convert_data_types(df: DataFrame) -> DataFrame:
    """Convert columns to proper types."""
    return df \
        .withColumn("created_date", to_timestamp("created_date", "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
        .withColumn(
            "closed_date",
            coalesce(
                to_timestamp("closed_date", "yyyy-MM-dd'T'HH:mm:ss.SSS"),
                col("created_date"),
            ),
        ) \
        .withColumn("latitude", col("latitude").cast(FloatType())) \
        .withColumn("longitude", col("longitude").cast(FloatType())) \
        .withColumn("unique_key", col("unique_key").cast(IntegerType())) \
        .withColumn("incident_zip", col("incident_zip").cast(IntegerType()))