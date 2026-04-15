import os
import logging

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from utils.spark import load_to_postgres

logger = logging.getLogger(__name__)


def build_nyc311_requests_daily(df: DataFrame):
    df_daily = df.withColumn("request_date", F.to_date('created_date')) \
        .groupBy("request_date") \
        .agg(F.sum(F.when(F.col("is_closed"), 1).otherwise(0)).alias("closed_count"),
             F.sum(F.when(F.col("is_closed"), 0).otherwise(1)).alias("open_count"),
             F.round(F.avg("resolution_time_in_hours"), 2).alias("avg_resolution_time_in_hours"),
             F.round(F.median("resolution_time_in_hours"), 2).alias("median_resolution_time_in_hours"),
             F.count("*").alias("total_count"))

    df_daily = df_daily \
        .withColumn("pct_closure_daily", F.round((F.col("closed_count") / F.col("total_count")) * 100, 2))

    load_to_postgres(df_daily, "gold.nyc311_requests_daily")

    logger.info(f"Loaded {df_daily.count()} rows to gold.nyc311_requests_daily")
