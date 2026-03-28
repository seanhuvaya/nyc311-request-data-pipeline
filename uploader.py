import logging

import pandas as pd

from config import settings
from metadata import log_extraction_end
from db.models.ingestion_metadata import ExtractionStatus
from utils import upload_data_to_s3

logger = logging.getLogger(__name__)


def upload_raw_data_to_s3(df: pd.DataFrame, extraction_id: int) -> None:
    """Upload raw DataFrame to S3 (partitioned by latest created_date) and log success."""
    if df.empty:
        logger.warning("No data to upload")
        log_extraction_end(extraction_id, ExtractionStatus.COMPLETED.value, num_records=0)
        return

    last_created = pd.to_datetime(df["created_date"]).max()

    file_key = (
        f"raw/date={last_created.strftime('%Y-%m-%d')}/"
        f"{settings.AWS_S3_DATA_PARQUET_FILENAME}"
    )

    upload_data_to_s3(df, settings.AWS_S3_BUCKET, file_key)

    log_extraction_end(
        extraction_id=extraction_id,
        status=ExtractionStatus.COMPLETED.value,
        num_records=len(df),
        latest_record_created_date=last_created,
    )

    logger.info(f"Uploaded {len(df)} records to s3://{settings.AWS_S3_BUCKET}/{file_key}")
