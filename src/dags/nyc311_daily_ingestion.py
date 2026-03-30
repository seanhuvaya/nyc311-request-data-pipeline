import logging
from datetime import datetime, timezone, timedelta

from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import dag, task

from src.db.models import PipelineStepRun
from src.pipeline.pipeline_logger import save_pipeline_step_run, create_pipeline_run
from src.extract.metadata import save_ingestion_metadata
from src.extract.client import NYC311ServiceRequestsClient
from src.extract.metadata import get_latest_record_created_date
from src.utils.config import settings
from src.utils.logger import setup_logging
from src.utils.s3_utils import upload_data_to_s3

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_daily_ingestion",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_daily_ingestion():
    @task()
    def start_pipeline_run():
        return create_pipeline_run("nyc_311_daily")

    @task()
    def determine_start_date():
        latest_created_date = get_latest_record_created_date()

        if not latest_created_date:
            latest_created_date = (datetime.now(timezone.utc) - timedelta(days=2)) \
                .replace(hour=0, minute=0, second=0, microsecond=0)

        return latest_created_date

    @task()
    def extract_and_upload_to_s3_bronze(start_date: datetime):
        logger.info(f"Creating nyc311 service requests client...")
        service_requests_client = NYC311ServiceRequestsClient(settings.DATASET_URL)

        service_requests_df = service_requests_client.fetch_nyc311_service_requests(start_date=start_date)
        if service_requests_df is None or service_requests_df.empty:
            logger.info(f"No new records found for start_date: {start_date}")
            return {
                "start_date": start_date,
                "status": "no_data",
                "latest_record_created_date": None,
                "row_count": 0,
                "s3_key": None
            }

        s3_key = f"bronze/date={start_date.strftime('%Y-%m-%d')}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
        upload_data_to_s3(service_requests_df, s3_key)

        latest_record_created_date = service_requests_df['created_date'].max()

        return {
            "start_date": start_date,
            "row_count": len(service_requests_df),
            "latest_record_created_date": latest_record_created_date,
            "s3_key": s3_key,
            "status": "success",
        }

    @task()
    def log_ingestion_metadata(result: dict, pipeline_run_id: int):
        latest_record_created_date = result["latest_record_created_date"]
        row_count = result["row_count"]

        return save_ingestion_metadata(latest_record_date=latest_record_created_date,
                                       row_count=row_count,
                                       pipeline_run_id=pipeline_run_id)

    @task()
    def log_pipeline_run_step(result: dict, pipeline_run_id: int, **context):
        started_at = context["dag_run"].start_date
        dag_id = context["dag"].dag_id

        logger.info(f"Logging ingestion metadata for pipeline_run: {pipeline_run_id}")

        pipeline_step_run = PipelineStepRun(
            pipeline_run_id=pipeline_run_id,
            dag_id=dag_id,
            step_name="extract",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            num_records_in=result["row_count"],
            num_records_out=result["row_count"],
            s3_file_key=result["s3_key"],
        )

        save_pipeline_step_run(pipeline_step_run)

        return result

    @task()
    def build_transformation_conf(pipeline_run_id: int, result: dict):
        return {
            "pipeline_run_id": pipeline_run_id,
            "s3_key": result["s3_key"],
            "latest_record_created_date": result["latest_record_created_date"],
        }

    pipeline_run_id = start_pipeline_run()
    start_date = determine_start_date()
    upload_result = extract_and_upload_to_s3_bronze(start_date)
    ingestion_metadata_id = log_ingestion_metadata(upload_result, pipeline_run_id)
    log_result = log_pipeline_run_step(upload_result, pipeline_run_id)
    transformation_conf = build_transformation_conf(pipeline_run_id, upload_result)

    logger.info(transformation_conf)

    trigger_processing = TriggerDagRunOperator(
        task_id="trigger_processing",
        trigger_dag_id="nyc311_daily_processing",
        conf=transformation_conf
    )

    pipeline_run_id >> start_date >> upload_result >> (ingestion_metadata_id, log_result) >> trigger_processing


nyc311_daily_ingestion()
