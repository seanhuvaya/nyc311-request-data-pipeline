import logging

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from utils.spark import load_to_postgres

logger = logging.getLogger(__name__)


def load_nyc311_requests_daily_staging_table(df: DataFrame):
    load_to_postgres(df, "staging.nyc311_requests_daily", truncate=True)
    logger.info(f"Loaded {df.count()} rows to staging.nyc311_requests_daily")


def load_nyc311_requests_daily_summary_staging_table(df: DataFrame):
    df_daily = df.withColumn("request_date", F.to_date('created_date')) \
        .groupBy("request_date") \
        .agg(F.sum(F.when(F.col("is_closed"), 1).otherwise(0)).alias("closed_count"),
             F.sum(F.when(F.col("is_closed"), 0).otherwise(1)).alias("open_count"),
             F.round(F.avg("resolution_time_in_hours"), 2).alias("avg_resolution_time_in_hours"),
             F.round(F.median("resolution_time_in_hours"), 2).alias("median_resolution_time_in_hours"),
             F.count("*").alias("total_count"))

    df_daily = df_daily \
        .withColumn("pct_closure_daily", F.round((F.col("closed_count") / F.col("total_count")) * 100, 2))

    load_to_postgres(df_daily, "staging.nyc311_requests_daily_summary", truncate=True)
    logger.info(f"Loaded {df.count()} rows to staging.nyc311_requests_daily_summary")


def load_nyc311_requests_weekly_summary_staging_table(df: DataFrame):
    df_weekly = df.withColumn("week_start", F.date_trunc("week", F.col("created_date"))) \
        .groupBy("week_start") \
        .agg(
            F.sum(F.when(F.col("is_closed"), 1).otherwise(0)).alias("week_closed_requests"),
            F.count("*").alias("week_total_requests"),
            F.when(F.col("week_total_requests") > 0, F.round((F.col("week_closed_requests") / F.col("week_total_requests")) * 100, 2)).alias("week_closed_requests_pct"),
            F.round(F.avg("resolution_time_in_hours"), 2).alias("week_avg_resolution_time_in_hours")) \
        .orderBy("week_start")

    window_spec = Window.orderBy("week_start")
    df_weekly = df_weekly \
        .withColumn("prev_week_total_requests", F.lag("week_total_requests", default=0).over(window_spec)) \
        .withColumn("prev_week_change_in_requests_pct", F.when(F.col("prev_week_total_requests") > 0, F.round((F.col("week_total_requests") - F.col("prev_week_total_requests")) / F.col("prev_week_total_requests") * 100, 2))) \
        .withColumn("prev_week_total_closed_requests", F.lag("week_closed_requests", default=0).over(window_spec)) \
        .withColumn("prev_week_change_in_closed_requests_pct", F.when(F.col("prev_week_total_closed_requests") > 0, F.round((F.col("week_closed_requests") - F.col("prev_week_total_closed_requests")) / F.col("prev_week_total_closed_requests") * 100, 2))) \
        .withColumn("prev_week_avg_resolution_time_in_hours", F.round(F.lag("week_avg_resolution_time_in_hours", default=0).over(window_spec), 2)) \
        .withColumn("prev_week_avg_resolution_time_in_hours_pct", F.when(F.col("prev_week_avg_resolution_time_in_hours") > 0, F.round((F.col("week_avg_resolution_time_in_hours") - F.col("prev_week_avg_resolution_time_in_hours")) / F.col("prev_week_avg_resolution_time_in_hours") * 100, 2)))

    load_to_postgres(df_weekly, "staging.nyc311_requests_weekly_summary", truncate=True)
    logger.info(f"Loaded {df_weekly.count()} rows to staging.nyc311_requests_weekly_summary")


def build_nyc311_requests_daily_staging_tables(df: DataFrame):
    load_nyc311_requests_daily_staging_table(df)
    load_nyc311_requests_daily_summary_staging_table(df)
    load_nyc311_requests_weekly_summary_staging_table(df)
