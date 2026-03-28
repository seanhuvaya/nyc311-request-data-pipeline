import logging
from datetime import datetime, timezone, timedelta

from airflow.sdk import dag, task

from src.extract.metadata import save_ingestion_metadata
from src.extract.client import NYC311ServiceRequestsClient
from src.extract.metadata import get_latest_record_created_date
from src.utils.config import settings
from src.utils.logger import setup_logging
from src.utils.s3_utils import upload_data_to_s3

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc311_ingestion",
    schedule=None,
    start_date=datetime(2026, 3, 28),
    catchup=False,
    tags=["nyc311", "etl"],
)
def nyc311_ingestion():
    @task()
    def determine_start_date():
        latest_created_date = get_latest_record_created_date()

        if not latest_created_date:
            latest_created_date = (datetime.now(timezone.utc) - timedelta(days=1)) \
                .replace(hour=0, minute=0, second=0, microsecond=0)

        return latest_created_date

    @task()
    def extract_and_upload_to_s3(start_date: datetime):
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

        s3_key = f"raw/date={start_date.strftime('%Y%m%d')}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
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
    def log_ingestion_metadata(result: dict):
        latest_record_created_date = result["latest_record_created_date"]
        row_count = result["row_count"]
        s3_key = result["s3_key"]

        return save_ingestion_metadata(latest_record_date=latest_record_created_date,
                                       row_count=row_count,
                                       s3_key=s3_key)

    @task()
    def log_pipeline_run_step(result: dict, **context):
        conf = context["dag_run"].conf
        pipeline_run_id = conf["pipeline_run_id"]

        logger.info(f"Logging ingestion metadata for pipeline_run: {pipeline_run_id}")

        return result

    start_date = determine_start_date()
    upload_result = extract_and_upload_to_s3(start_date)
    log_result = log_pipeline_run_step(upload_result)
    ingestion_metadata_id = log_ingestion_metadata(upload_result)

    start_date >> upload_result >> (ingestion_metadata_id, log_result)


nyc311_ingestion()
