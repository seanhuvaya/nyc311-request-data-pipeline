import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from airflow.sdk import dag, task, get_current_context
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from src.db.models import PipelineStepRun
from src.pipeline.pipeline_logger import get_latest_pipeline_step_run_by_step_name, save_pipeline_step_run
from src.utils.config import settings
from src.utils.dag_utils import failure_callback
from src.utils.spark_utils import load_to_postgres, load_from_postgres

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_daily_loading",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
    default_args={
        "on_failure_callback": lambda context: failure_callback(context, step_name="load"),
    }
)
def nyc311_daily_loading():
    s3_endpoint = settings.AWS_S3_ENDPOINT_URL or "https://s3.amazonaws.com"
    parsed_endpoint = urlparse(s3_endpoint)
    s3a_endpoint = parsed_endpoint.netloc or parsed_endpoint.path
    use_ssl = parsed_endpoint.scheme != "http"

    @task()
    def get_silver_s3_key():
        pipeline_step_run = get_latest_pipeline_step_run_by_step_name("transform")
        return pipeline_step_run.s3_file_key

    @task()
    def load_daily_fact(s3_key: str):
        spark = SparkSession.builder \
            .appName("NYC311Transform") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID) \
            .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY) \
            .config("spark.hadoop.fs.s3a.endpoint", s3a_endpoint) \
            .config("spark.hadoop.fs.s3a.path.style.access", str(settings.AWS_S3_PATH_STYLE).lower()) \
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(use_ssl).lower()) \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3") \
            .getOrCreate()

        df = spark.read.parquet(f"s3a://{settings.AWS_S3_BUCKET}/{s3_key}")

        if df.count() == 0 or df.isEmpty():
            logger.info(f"No records found for {s3_key}")
            spark.stop()
            return {
                "records_count": df.count(),
            }

        df = df \
            .withColumn("created_date", F.to_timestamp(F.col("created_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
            .withColumn("closed_date", F.to_timestamp(F.col("closed_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS"))

        load_to_postgres(df, "fact_nyc311_service_requests")

        logger.info(f"Loaded {df.count()} rows to fact_nyc311_service_requests table")

        results = {
            "records_count": df.count(),
        }

        spark.stop()

        return results

    @task()
    def build_gold_tables(s3_key: str):
        spark = SparkSession.builder \
            .appName("NYC311GoldTables") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID) \
            .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY) \
            .config("spark.hadoop.fs.s3a.endpoint", s3a_endpoint) \
            .config("spark.hadoop.fs.s3a.path.style.access", str(settings.AWS_S3_PATH_STYLE).lower()) \
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(use_ssl).lower()) \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3") \
            .getOrCreate()

        df = spark.read.parquet(f"s3a://{settings.AWS_S3_BUCKET}/{s3_key}")

        if df.count() == 0 or df.isEmpty():
            logger.info(f"No records found for {s3_key}")
            spark.stop()
            return

        df = df \
            .withColumn("created_date", F.to_timestamp(F.col("created_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
            .withColumn("closed_date", F.to_timestamp(F.col("closed_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS"))

        df = df.withColumn("incident_zip", F.col("incident_zip").cast("string"))

        request_fact_df = df.select(
            "unique_key",
            "created_date",
            "closed_date",
            "is_closed",
            "resolution_time_in_hours",
            "agency",
            "complaint_type",
            "descriptor",
            "incident_zip",
            "borough",
            "community_board",
            "council_district",
            "latitude",
            "longitude",
            "location_type",
        )

        load_to_postgres(request_fact_df, "gold_nyc311_request_fact")

        requests_daily_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date").agg(F.count("*").alias("total_requests"),
                                         F.sum(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias(
                                             "closed_requests"),
                                         F.sum(F.when(F.col("is_closed") == False, 1).otherwise(0)).alias(
                                             "open_requests"),
                                         F.avg("resolution_time_in_hours").alias("avg_resolution_time_in_hours")) \
            .withColumn("pct_closed", F.when(F.col("total_requests") > 0,
                                             F.col("closed_requests") / F.col("total_requests")).otherwise(F.lit(0.0))) \
            .select("request_date", "total_requests", "closed_requests", "open_requests", "pct_closed",
                    "avg_resolution_time_in_hours")

        load_to_postgres(requests_daily_df, "gold_nyc311_requests_daily")

        requests_by_complaint_type_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date", "complaint_type") \
            .agg(F.count("*").alias("total_requests"),
                 F.count(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias("closed_requests"),
                 F.avg("resolution_time_in_hours").alias("avg_resolution_time_in_hours")) \
            .select("request_date", "complaint_type", "total_requests", "closed_requests",
                    "avg_resolution_time_in_hours")

        load_to_postgres(requests_by_complaint_type_df, "gold_nyc311_requests_by_complaint_daily")

        requests_by_agency_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date", "agency") \
            .agg(F.count("*").alias("total_requests"),
                 F.sum(F.when(F.col("is_closed") == False, 1).otherwise(0)).alias("open_requests"),
                 F.sum(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias("closed_requests"),
                 F.avg(F.when(F.col("is_closed") == True, F.col("resolution_time_in_hours"))).alias(
                     "avg_resolution_time_in_hours")) \
            .select("request_date", "agency", "total_requests", "open_requests", "closed_requests",
                    "avg_resolution_time_in_hours")

        load_to_postgres(requests_by_agency_df, "gold_nyc311_requests_by_agency_daily")

        requests_geo_daily_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date", "borough") \
            .agg(F.count("*").alias("total_requests"),
                 F.sum(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias("closed_requests"),
                 F.avg(F.when(F.col("is_closed") == True, F.col("resolution_time_in_hours"))).alias(
                     "avg_resolution_time_in_hours")) \
            .select("request_date", "borough", "total_requests", "closed_requests", "avg_resolution_time_in_hours")

        load_to_postgres(requests_geo_daily_df, "gold_nyc311_requests_geo_daily")

        sla_performance_daily_df = df.withColumn("request_date", F.to_date("created_date")) \
            .filter(F.col("is_closed") == True) \
            .groupBy("request_date", "agency", "complaint_type") \
            .agg(F.count("*").alias("total_closed_requests"),
                 F.sum(F.when(F.col("resolution_time_in_hours") <= 24, 1).otherwise(0)).alias("closed_within_24h"),
                 F.sum(F.when(F.col("resolution_time_in_hours") <= 72, 1).otherwise(0)).alias("closed_within_72h"),
                 F.sum(F.when(F.col("resolution_time_in_hours") > 72, 1).otherwise(0)).alias("closed_after_72h")) \
            .withColumn("pct_closed_within_24h", F.when(F.col("total_closed_requests") > 0,
                                                        F.col("closed_within_24h") / F.col("total_closed_requests"))
                        .otherwise(F.lit(0.0))) \
            .withColumn("pct_closed_within_72h", F.when(F.col("total_closed_requests") > 0,
                                                        F.col("closed_within_72h") / F.col("total_closed_requests"))
                        .otherwise(F.lit(0.0))) \
            .select("request_date", "agency", "complaint_type", "total_closed_requests", "closed_within_24h",
                    "closed_within_72h", "closed_after_72h", "pct_closed_within_24h", "pct_closed_within_72h")

        load_to_postgres(sla_performance_daily_df, "gold_nyc311_sla_performance_daily")

        full_fact_df = load_from_postgres(spark, "fact_nyc311_service_requests") \
            .withColumn("created_date", F.to_timestamp(F.col("created_date"))) \
            .withColumn("closed_date", F.to_timestamp(F.col("closed_date"))) \
            .withColumn("incident_zip", F.col("incident_zip").cast("string"))

        min_date_df = full_fact_df.agg(F.min(F.to_date("created_date")).alias("min_date"),
                                       F.max(F.to_date("created_date")).alias("max_date"))
        min_max_dates = min_date_df.collect()[0]
        min_date = min_max_dates["min_date"]
        max_date = min_max_dates["max_date"]

        if min_date and max_date:
            date_series_df = spark.sql(
                f"SELECT explode(sequence(to_date('{min_date}'), to_date('{max_date}'))) AS snapshot_date"
            )

            open_backlog_daily_df = full_fact_df \
                .crossJoin(date_series_df) \
                .filter(
                    (F.to_date(F.col("created_date")) <= F.col("snapshot_date")) &
                    (F.col("closed_date").isNull() | (F.to_date(F.col("closed_date")) > F.col("snapshot_date")))
                ) \
                .withColumn("age_open_hours", (F.unix_timestamp(F.col("snapshot_date")) -
                                               F.unix_timestamp(F.col("created_date"))) / 3600.0) \
                .groupBy("snapshot_date", "agency", "borough", "complaint_type") \
                .agg(F.count("*").alias("open_backlog_count"),
                     F.avg("age_open_hours").alias("avg_age_open_hours"),
                     F.max("age_open_hours").alias("max_age_open_hours")) \
                .select("snapshot_date", "agency", "borough", "complaint_type", "open_backlog_count",
                        "avg_age_open_hours", "max_age_open_hours")

            load_to_postgres(open_backlog_daily_df, "gold_nyc311_open_backlog_daily")

            dim_date_df = date_series_df \
                .withColumnRenamed("snapshot_date", "date") \
                .withColumn("year", F.year("date")) \
                .withColumn("month", F.month("date")) \
                .withColumn("month_name", F.date_format("date", "MMMM")) \
                .withColumn("week", F.weekofyear("date")) \
                .withColumn("day_of_week", F.dayofweek("date")) \
                .withColumn("is_weekend", F.dayofweek("date").isin([1, 7])) \
                .select("date", "year", "month", "month_name", "week", "day_of_week", "is_weekend")

            load_to_postgres(dim_date_df, "dim_date")

        top_complaints_base_df = full_fact_df.withColumn("month", F.date_trunc("month", F.col("created_date"))) \
            .groupBy("month", "borough", "complaint_type") \
            .agg(F.count("*").alias("request_count"))
        top_complaints_window = Window.partitionBy("month", "borough").orderBy(F.desc("request_count"))
        top_complaints_monthly_df = top_complaints_base_df \
            .withColumn("rank_in_borough", F.dense_rank().over(top_complaints_window)) \
            .select(F.to_date("month").alias("month"), "borough", "complaint_type", "request_count", "rank_in_borough")

        load_to_postgres(top_complaints_monthly_df, "gold_nyc311_top_complaints_monthly")

        resolution_distribution_df = full_fact_df \
            .filter(F.col("is_closed") == True) \
            .withColumn("request_month", F.to_date(F.date_trunc("month", F.col("created_date")))) \
            .withColumn("resolution_bucket",
                        F.when(F.col("resolution_time_in_hours") <= 24, F.lit("0-24h"))
                        .when(F.col("resolution_time_in_hours") <= 72, F.lit("24-72h"))
                        .when(F.col("resolution_time_in_hours") <= 168, F.lit("3-7d"))
                        .otherwise(F.lit("7+d"))) \
            .groupBy("request_month", "agency", "complaint_type", "resolution_bucket") \
            .agg(F.count("*").alias("request_count")) \
            .select("request_month", "agency", "complaint_type", "resolution_bucket", "request_count")

        load_to_postgres(resolution_distribution_df, "gold_nyc311_resolution_time_distribution")

        location_hotspots_df = full_fact_df \
            .groupBy("borough", "incident_zip", "complaint_type") \
            .agg(F.count("*").alias("request_count"),
                 F.avg("latitude").alias("avg_latitude"),
                 F.avg("longitude").alias("avg_longitude")) \
            .select("borough", "incident_zip", "complaint_type", "request_count", "avg_latitude", "avg_longitude")

        load_to_postgres(location_hotspots_df, "gold_nyc311_location_hotspots")

        dim_location_df = full_fact_df.select("incident_zip", "borough", "city", "community_board", "council_district") \
            .dropna(subset=["incident_zip", "borough", "city", "community_board", "council_district"]) \
            .dropDuplicates(["incident_zip", "borough"]) \
            .select("incident_zip", "borough", "city", "community_board", "council_district")

        load_to_postgres(dim_location_df, "dim_location")

        dim_complaint_df = full_fact_df.select("complaint_type", "descriptor", "location_type") \
            .dropna(subset=["complaint_type", "descriptor", "location_type"]) \
            .dropDuplicates(["complaint_type", "descriptor", "location_type"]) \
            .select("complaint_type", "descriptor", "location_type")

        load_to_postgres(dim_complaint_df, "dim_complaint")

        dim_agency_df = full_fact_df.select("agency") \
            .dropna(subset=["agency"]) \
            .dropDuplicates(["agency"])

        load_to_postgres(dim_agency_df, "dim_agency")

        spark.stop()

    @task()
    def log_pipeline_run_step(result: dict):
        context = get_current_context()
        dag_id = context["dag"].dag_id
        started_at = context["dag_run"].start_date

        pipeline_step_run = PipelineStepRun(
            dag_id=dag_id,
            step_name="load",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            num_records_in=result["records_count"],
            num_records_out=result["records_count"]
        )

        save_pipeline_step_run(pipeline_step_run)

        return result

    silver_s3_key = get_silver_s3_key()
    fact_result = load_daily_fact(silver_s3_key)
    log_result = log_pipeline_run_step(fact_result)

    silver_s3_key >> fact_result >> build_gold_tables(s3_key=silver_s3_key) >> log_result


nyc311_daily_loading()
