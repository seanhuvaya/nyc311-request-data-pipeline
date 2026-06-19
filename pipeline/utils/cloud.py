import logging
import time
from contextlib import contextmanager

import boto3
import pandas as pd
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError

from utils.config import settings

logger = logging.getLogger(__name__)


def make_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


@contextmanager
def s3_client_context():
    client = make_s3_client()
    try:
        yield client
    finally:
        client.close()


def upload_data_to_s3(data: pd.DataFrame, s3_client, bucket: str, key: str, retry_attempts: int = 3):
    data_bytes = data.to_csv(index=False, encoding="utf-8", lineterminator="\n").encode("utf-8")
    for attempt in range(1, retry_attempts + 1):
        try:
            s3_client.put_object(
                Body=data_bytes,
                Bucket=bucket,
                Key=key,
                ContentType="text/csv",
            )
            logger.info(f"Data uploaded successfully to S3 | bucket={bucket}, key={key}, rows={len(data)}")
            return
        except (ClientError, NoCredentialsError) as e:
            if attempt == retry_attempts:
                logger.error(f"Failed to upload chunk after {retry_attempts} attempts: {e}")
                raise
            wait_time = 2 ** (attempt - 1)
            logger.warning(f"S3 upload failed, retry {attempt}/{retry_attempts}. Waiting {wait_time}s...")
            time.sleep(wait_time)
