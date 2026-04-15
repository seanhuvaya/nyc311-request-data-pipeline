import requests
from io import StringIO
from datetime import datetime

import boto3
import pandas as pd
from botocore.client import Config

BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"

S3_CLIENT = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="changemeuser",
    aws_secret_access_key="changemepass",
    region_name="us-east-1",
    config=Config(signature_version="s3v4")
)


def extract_nyc311_requests_since(extraction_date: datetime, start_date: datetime, is_backfill: bool = False,
                                  limit: int = 1000, offset: int = 0):
    latest_created_date = start_date
    start_date = start_date.strftime("%Y-%m-%dT00:00:00")

    condition = f"created_date>='{start_date}'"

    while True:
        url = (
            f"{BASE_URL}"
            f"?$where={condition}"
            f"&$limit={limit}"
            f"&$offset={offset}"
            f"&$order=created_date DESC"
        )

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        csv_buffer = StringIO(response.text)

        chunk = pd.read_csv(csv_buffer)

        if chunk.empty:
            break

        chunk["created_date"] = pd.to_datetime(chunk["created_date"])

        latest_created_date = max(latest_created_date, chunk["created_date"].max())

        s3_key = f"raw/historical/nyc_311_requests_offset_{offset}.csv" if is_backfill else \
            f"raw/daily/date={extraction_date.strftime('%Y-%m-%d')}/nyc_311_requests_offset_{offset}.csv"

        S3_CLIENT.put_object(Body=csv_buffer.getvalue(), Bucket="nyc311-data", Key=s3_key)

        offset += limit

    return latest_created_date


if __name__ == "__main__":
    print(extract_nyc311_requests_since(extraction_date=datetime.now(), start_date=datetime(2026, 4, 1)))
