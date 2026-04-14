from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def enrich_nyc311_requests(df: DataFrame):

    df = df \
        .withColumn("is_closed", F.when(F.col("closed_date").isNotNull(), True).otherwise(False)) \
        .withColumn("resolution_time_in_hours", F.when(F.col("closed_date").isNotNull(), (
            F.unix_timestamp(F.col("closed_date")) - F.unix_timestamp(F.col("created_date"))) / (60 * 60)).otherwise(None))

    return df

