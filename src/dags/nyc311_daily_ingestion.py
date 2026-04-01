import logging
from datetime import datetime, timezone, timedelta

from airflow.sdk import dag, task

from extract.nyc311_fact_service_request import get_latest_created_date
from src.db.models import PipelineStepRun
from src.extract.client import NYC311ServiceRequestsClient
from src.pipeline.pipeline_logger import save_pipeline_step_run
from src.utils.config import settings
from src.utils.logger import setup_logging
from src.utils.s3_utils import upload_data_to_s3
from src.utils.dag_utils import failure_callback

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_daily_ingestion",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
    default_args={
        "on_failure_callback": lambda context: failure_callback(context, step_name="extract"),
    }
)
def nyc311_daily_ingestion():
    @task()
    def determine_start_date():
        latest_created_date = get_latest_created_date()

        if not latest_created_date:
            latest_created_date = (datetime.now(timezone.utc) - timedelta(days=7)) \
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

        s3_key = f"bronze/date={datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
        upload_data_to_s3(service_requests_df, s3_key)

        return {
            "start_date": start_date,
            "row_count": len(service_requests_df),
            "s3_key": s3_key,
            "status": "success",
        }

    @task()
    def log_pipeline_run_step(result: dict, **context):
        started_at = context["dag_run"].start_date
        dag_id = context["dag"].dag_id

        pipeline_step_run = PipelineStepRun(
            dag_id=dag_id,
            step_name="extract",
            status="success",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            num_records_in=result["row_count"],
            num_records_out=result["row_count"],
            s3_file_key=result["s3_key"]
        )

        save_pipeline_step_run(pipeline_step_run)

        return result

    start_date = determine_start_date()
    upload_result = extract_and_upload_to_s3_bronze(start_date)
    log_result = log_pipeline_run_step(upload_result)

    start_date >> upload_result >> log_result


nyc311_daily_ingestion()
