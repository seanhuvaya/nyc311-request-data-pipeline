import logging
from datetime import datetime, timezone

from airflow.sdk import dag, task, get_current_context
from pyspark.sql import SparkSession

from pipeline.pipeline_logger import save_pipeline_step_run
from src.db.models import PipelineStepRun
from src.transform.processing import process_nyc311_daily_data
from src.utils.config import settings
from utils.s3_utils import upload_data_to_s3

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_daily_processing",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_daily_processing():
    @task()
    def process_and_upload_to_s3_silver():
        context = get_current_context()
        dag_run = context["dag_run"]
        s3_bronze_key = dag_run.conf["s3_key"]
        latest_record_created_date = dag_run.conf["latest_record_created_date"]

        spark = SparkSession.builder \
            .appName("NYC311Transform") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.hadoop.fs.s3a.access.key", settings.AWS_ACCESS_KEY_ID) \
            .config("spark.hadoop.fs.s3a.secret.key", settings.AWS_SECRET_ACCESS_KEY) \
            .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
            .getOrCreate()

        logger.info(f"Processing NYC311 daily data from S3: {s3_bronze_key}")

        df = spark.read.parquet(f"s3a://{settings.AWS_S3_BUCKET}/{s3_bronze_key}")

        df_processed = process_nyc311_daily_data(df)

        date_format = '%Y-%m-%dT%H:%M:%S.%f'
        created_date = datetime.strptime(latest_record_created_date, date_format)

        s3_silver_key = f"silver/date={created_date.strftime('%Y-%m-%d')}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
        upload_data_to_s3(df_processed.toPandas(), s3_silver_key)

        result = {
            "records_in": df.count(),
            "records_out": df_processed.count(),
            "s3_key": s3_silver_key,
            "status": "success",
        }

        spark.stop()

        return result

    @task()
    def log_pipeline_run_step(result: dict):
        context = get_current_context()
        dag_id = context["dag"].dag_id
        started_at = context["dag_run"].start_date
        pipeline_run_id = context["dag_run"].conf["pipeline_run_id"]

        pipeline_step_run = PipelineStepRun(
            pipeline_run_id=pipeline_run_id,
            dag_id=dag_id,
            step_name="transform",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            num_records_in=result["records_in"],
            num_records_out=result["records_out"]
        )

        save_pipeline_step_run(pipeline_step_run)

        return result

    processing_result = process_and_upload_to_s3_silver()
    log_result = log_pipeline_run_step(processing_result)

    processing_result >> log_result


nyc311_daily_processing()
