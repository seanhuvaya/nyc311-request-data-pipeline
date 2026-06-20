import json
import logging
from datetime import datetime

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from nyc311.utils.config import settings

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


def load_metadata_from_s3(s3_client, s3_save_key: str) -> datetime | None:
    key = f"{s3_save_key}/metadata.json"
    try:
        response = s3_client.get_object(Bucket=settings.s3_bucket_name, Key=key)
        metadata = json.loads(response["Body"].read().decode("utf-8"))
        latest_created_date = datetime.fromisoformat(metadata["latest_watermark"])
        logger.info(f"Loaded metadata from S3 | key={key}, latest_created_date={latest_created_date}")
        return latest_created_date
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.info(f"No metadata file found in S3 | key={key}")
            return None
        raise
