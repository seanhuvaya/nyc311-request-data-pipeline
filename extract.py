import logging
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Tuple

import boto3
import pandas as pd
import requests

from config import settings
from db import get_db_session
from models import ExtractMetadata
from models.extraction_metadata import ExtractionStatus
from validate import perform_validation

logger = logging.getLogger(__name__)


def log_extraction_start(extract_params: dict = None) -> int:
    with get_db_session() as session:
        new_record = ExtractMetadata(
            status=ExtractionStatus.INITIATED.value,
            parameters=extract_params or {},
        )

        session.add(new_record)
        session.flush()

        logger.info(f"Created new extract metadata: {new_record.id}")
        return new_record.id


def log_extraction_end(extraction_id: int,
                       status: str,
                       num_records: int = 0,
                       latest_record_created_date=None,
                       error_message: str = None) -> None:
    with get_db_session() as session:
        record = session.get(ExtractMetadata, extraction_id)

        if not record:
            message = f"Extraction record: {extraction_id} not found"
            logger.error(message)
            raise Exception(message)

        record.extraction_completed_at = datetime.now(timezone.utc)
        record.status = status
        record.num_records_pulled = num_records
        record.latest_record_created_date = latest_record_created_date
        record.error_message = error_message

        logger.info(f"Extraction: {record.id} finished with status `{status}`")


def fetch_all_311_requests(last_update_date: str, limit: int = 1000, offset: int = 0) -> Tuple[pd.DataFrame, int]:
    ingested_data = []

    params = {
        "$where": f"created_date > '{last_update_date}'",
        "$order": "created_date ASC",
        "$limit": limit,
        "$offset": offset
    }

    extraction_id = log_extraction_start(params)

    try:
        logger.info(f"Fetching data: GET {settings.DATASET_URL}")

        while True:
            response = requests.get(settings.DATASET_URL, params=params)

            if not response.ok:
                error_message = response.json()['message']
                log_extraction_end(extraction_id=extraction_id, status=ExtractionStatus.FAILED.value,
                                   error_message=error_message)
                raise Exception(
                    f"GET {settings.DATASET_URL.split('/')[-1]} failed [{response.status_code}]: {error_message}"
                )

            response_data = response.json()

            if not response_data:
                break

            ingested_data.extend(response_data)

            params["$offset"] += limit

        logger.info(f"Fetched {len(ingested_data)} records")

        return pd.DataFrame(ingested_data), extraction_id
    except Exception as e:
        logger.exception(str(e))
        raise e


def upload_raw_data_to_s3(df: pd.DataFrame, extraction_id: int) -> None:
    logger.info(f"Uploading raw data to s3...")
    buffer = StringIO()
    df.to_csv(buffer, index=False)

    last_created_record_date = pd.to_datetime(df['created_date']).max()
    file_key = f"raw/date={last_created_record_date.strftime('%Y-%m-%d')}/{settings.AWS_S3_RAW_DATA_CSV_FILENAME}"

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=file_key,
        Body=buffer.getvalue(),
        ContentType="text/csv",
    )
    logger.info(f"Raw CSV successfully saved to s3: s3://{settings.AWS_S3_BUCKET}/{file_key}")

    log_extraction_end(extraction_id, ExtractionStatus.COMPLETED.value, num_records=len(df),
                       latest_record_created_date=last_created_record_date)


def extract_nyc311_requests():
    latest_record_created_date = None
    with get_db_session() as session:
        latest_record = session.query(ExtractMetadata).order_by(
            ExtractMetadata.latest_record_created_date.desc()).first()
        if latest_record:
            latest_record_created_date = latest_record.latest_record_created_date

    if not latest_record_created_date:
        latest_record_created_date = datetime.today() - timedelta(days=1)

    logger.info(f"Latest record created date: {latest_record_created_date}")

    latest_record_created_date = f"{latest_record_created_date.strftime('%Y-%m-%d')}T00:00:00.000"
    raw_data_df, extraction_id = fetch_all_311_requests(latest_record_created_date)

    perform_validation(raw_data_df, "extract")
    upload_raw_data_to_s3(raw_data_df, extraction_id)


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()
    extract_nyc311_requests()
