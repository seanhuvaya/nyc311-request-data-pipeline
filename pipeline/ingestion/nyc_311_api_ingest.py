import logging
from datetime import datetime
from io import StringIO

import boto3
import pandas as pd
from botocore.client import Config
from utils.http import get_session_with_retry

from utils.config import settings

S3_CLIENT = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name="us-east-1",
    config=Config(signature_version="s3v4")
)

logger = logging.getLogger(__name__)


def extract_nyc311_requests_since(start_date: datetime, s3_save_key: str, limit: int = 1000, offset: int = 0):
    latest_created_date = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
    start_date = start_date.strftime("%Y-%m-%dT00:00:00")
    condition = f"created_date>='{start_date}'"

    logger.info(f"Starting extraction | start_date={start_date}, s3_save_key={s3_save_key}, limit={limit}")

    while True:
        url = (
            f"{settings.dataset_url}"
            f"?$where={condition}"
            f"&$limit={limit}"
            f"&$offset={offset}"
            f"&$order=created_date DESC"
        )

        logger.debug(f"Fetching chunk | offset={offset}, limit={limit}, url={url}")

        session = get_session_with_retry()
        response = session.get(url, timeout=60)
        response.raise_for_status()

        csv_buffer = StringIO(response.text)
        chunk = pd.read_csv(csv_buffer)

        if chunk.empty:
            logger.info(f"No more records found | final_offset={offset}, latest_created_date={latest_created_date}")
            break

        chunk["created_date"] = pd.to_datetime(chunk["created_date"])
        chunk_latest = chunk["created_date"].max()
        latest_created_date = max(latest_created_date, chunk_latest)

        logger.debug(
            f"Chunk loaded | rows={len(chunk)}, chunk_latest={chunk_latest}, running_latest={latest_created_date}")

        s3_file_key = f"{s3_save_key}/nyc311_requests_offset_{offset}.csv"
        S3_CLIENT.put_object(Body=csv_buffer.getvalue(), Bucket=settings.s3_bucket_name, Key=s3_file_key)

        logger.info(f"Chunk uploaded to S3 | s3_key={s3_file_key}, rows={len(chunk)}, offset={offset}")

        offset += limit

    logger.info(f"Extraction complete | total_records_fetched={offset}, latest_created_date={latest_created_date}")

    return latest_created_date
