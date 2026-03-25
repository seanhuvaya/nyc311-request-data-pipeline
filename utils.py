import logging
from datetime import datetime, timezone
from io import BytesIO

import boto3
from pandas import DataFrame

logger = logging.getLogger(__name__)


def upload_data_to_s3(df: DataFrame, bucket: str, object_name: str):
    logger.info(f"Uploading {len(df)} rows to s3://{bucket}/{object_name}")
    buffer = BytesIO()
    df.to_parquet(
        buffer,
        engine="pyarrow",
        compression="snappy",
        index=False
    )

    buffer.seek(0)

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=object_name,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
        Metadata={
            "load_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            "row_count": str(len(df)),
        }
    )
    logger.info(f"Successfully uploaded parquet to s3://{bucket}/{object_name}")
