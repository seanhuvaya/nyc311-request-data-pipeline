import io
import logging
from datetime import datetime, timedelta
from io import StringIO
from typing import List

import boto3
import pandas as pd
import requests
from jinja2.bccache import Bucket

from constants import DATA_BASE_URL, NYC_311_DATASET

logger = logging.getLogger(__name__)


def fetch_all_311_requests(last_update_date: str, limit: int = 1000, offset: int = 0) -> List[any]:
    ingested_data = []

    params = {
        "$where": f"created_date > '{last_update_date}'",
        "$order": "created_date ASC",
        "$limit": limit,
        "$offset": offset
    }

    try:
        url = DATA_BASE_URL + f"/{NYC_311_DATASET}"
        logger.info(f"Fetching data: GET {url}")

        while True:
            response = requests.get(url, params=params)

            if not response.ok:
                raise Exception(
                    f"GET {NYC_311_DATASET} failed [{response.status_code}]: {response.json()['message']}"
                )

            response_data = response.json()

            if not response_data:
                break

            ingested_data.extend(response_data)

            params["$offset"] += limit

        logger.info(f"Fetched {len(ingested_data)} records")

        return ingested_data
    except Exception as e:
        logger.exception(str(e))
        raise e


def upload_raw_data_to_s3(df: pd.DataFrame):
    logger.info(f"Uploading raw data to s3...")
    buffer = StringIO()
    df.to_csv(buffer, index=False)

    last_created_record_date = pd.to_datetime(df['created_date']).max()
    bucket = "nyc311-requests-data"
    file_key = f"raw/nyc311-requests-data_{last_created_record_date.strftime('%Y-%m-%d %H:%M:%S').replace(' ', '_')}.csv"

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=file_key,
        Body=buffer.getvalue(),
        ContentType="text/csv",
    )
    logger.info(f"Raw CSV successfully saved to s3: s3://{bucket}/{file_key}")


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()

    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_update_date_example = yesterday + "T00:00:00.000"
    records = fetch_all_311_requests(last_update_date_example)

    df = pd.DataFrame(records)
    upload_raw_data_to_s3(df)
