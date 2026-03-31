import logging
from io import BytesIO

import boto3
from pandas import DataFrame

from src.utils.config import settings

logger = logging.getLogger(__name__)


def upload_data_to_s3(df: DataFrame, s3_key: str):
    try:
        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine="pyarrow", coerce_timestamps="us",
                      allow_truncated_timestamps=True)

        s3_client = boto3.client("s3")

        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=s3_key,
            Body=parquet_buffer.getvalue(),
            ContentType="application/octet-stream",
        )

        logger.info(f"Successfully uploaded {len(df)} rows to s3://{settings.AWS_S3_BUCKET}/{s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload data to s3: {str(e)}")
        raise e
