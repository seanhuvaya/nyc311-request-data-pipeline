import logging
from datetime import datetime, timezone

from airflow.sdk import dag, task, get_current_context
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.db.models import PipelineStepRun
from src.pipeline.pipeline_logger import get_latest_pipeline_step_run_by_step_name, save_pipeline_step_run
from src.utils.config import settings
from src.utils.spark_utils import load_to_postgres

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_daily_loading",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_daily_loading():
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
            .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
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
            .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
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

        requests_daily_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date").agg(F.count("*").alias("total_requests"),
                                         F.sum(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias(
                                             "closed_requests"),
                                         F.sum(F.when(F.col("is_closed") == False, 1).otherwise(0)).alias(
                                             "open_requests"),
                                         F.avg("resolution_time_in_minutes").alias("avg_resolution_time_in_minutes")) \
            .withColumn("pct_closed", F.when(F.col("total_requests") > 0,
                                             F.col("closed_requests") / F.col("total_requests")).otherwise(F.lit(0.0))) \
            .select("request_date", "total_requests", "closed_requests", "open_requests", "pct_closed",
                    "avg_resolution_time_in_minutes")

        load_to_postgres(requests_daily_df, "gold_nyc311_requests_daily")

        requests_by_complaint_type_df = df.withColumn("request_date", F.to_date("created_date")) \
            .groupBy("request_date", "complaint_type") \
            .agg(F.count("*").alias("total_requests"),
                 F.count(F.when(F.col("is_closed") == True, 1).otherwise(0)).alias("closed_requests"),
                 F.avg("resolution_time_in_minutes").alias("avg_resolution_time_in_minutes")) \
            .select("request_date", "complaint_type", "total_requests", "closed_requests",
                    "avg_resolution_time_in_minutes")

        load_to_postgres(requests_by_complaint_type_df, "gold_nyc311_requests_by_complaint_daily")

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
