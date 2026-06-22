import json
import logging
from datetime import datetime, timezone
from io import StringIO
from urllib.parse import urlencode

import pandas as pd

from nyc311.utils.config import settings
from nyc311.utils.http import get_session_with_retry

logger = logging.getLogger(__name__)

_DATE_COLS = ["created_date", "resolution_action_updated_date"]


def extract_nyc311_requests_since(
    start_date: datetime,
    s3_save_key: str,
    s3_client,
    limit: int = 1000,
    offset: int = 0,
) -> datetime:
    start_date_str = start_date.strftime("%Y-%m-%dT00:00:00")
    watermark = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date

    logger.info(f"Starting extraction | start_date={start_date_str}, s3_save_key={s3_save_key}, limit={limit}")

    session = get_session_with_retry()

    total_records_fetched = 0

    while True:
        params = {
            "$where": (
                f"resolution_action_updated_date>='{start_date_str}'"
                f" OR created_date>='{start_date_str}'"
            ),
            "$limit": limit,
            "$offset": offset,
            "$order": "created_date DESC",
        }
        url = f"{settings.dataset_url}?{urlencode(params)}"

        logger.debug(f"Fetching chunk | offset={offset}, limit={limit}")

        response = session.get(url, timeout=60)
        response.raise_for_status()

        dates_df = pd.read_csv(StringIO(response.text), usecols=_DATE_COLS)

        if dates_df.empty:
            logger.info(f"No more records found | final_offset={offset}, watermark={watermark}")
            break

        dates_df["created_date"] = pd.to_datetime(dates_df["created_date"])
        dates_df["resolution_action_updated_date"] = pd.to_datetime(dates_df["resolution_action_updated_date"])

        
        now = datetime.now()
        effective_watermarks = dates_df["resolution_action_updated_date"].fillna(dates_df["created_date"])
        chunk_latest_watermark = effective_watermarks.max().to_pydatetime().replace(tzinfo=None)
        watermark = max(watermark, min(chunk_latest_watermark, now))

        logger.debug(f"Chunk loaded | rows={len(dates_df)}, chunk_latest_watermark={chunk_latest_watermark}, watermark={watermark}")

        s3_file_key = f"{s3_save_key}/{start_date.strftime('%Y-%m-%d')}/nyc311_requests_offset_{offset}.csv"
        try:
            s3_client.put_object(
                Body=response.content,
                Bucket=settings.s3_bucket_name,
                Key=s3_file_key,
                ContentType="text/csv",
            )
        except Exception:
            logger.exception(f"Failed to upload chunk to S3 | s3_key={s3_file_key}, offset={offset}")
            raise

        logger.info(f"Chunk uploaded to S3 | s3_key={s3_file_key}, rows={len(dates_df)}, offset={offset}")

        offset += limit
        total_records_fetched += len(dates_df)

    logger.info(f"Extraction complete | total_records_fetched={total_records_fetched}, watermark={watermark}")

    _save_metadata(s3_client, watermark, records_fetched=total_records_fetched)

    return watermark


def _save_metadata(s3_client, watermark: datetime, records_fetched: int) -> None:
    metadata = {
        "latest_watermark": watermark.isoformat(),
        "total_records_fetched": records_fetched,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    key = "extraction_metadata.json"
    s3_client.put_object(
        Body=json.dumps(metadata).encode(),
        Bucket=settings.s3_bucket_name,
        Key=key,
        ContentType="application/json",
    )
    logger.info(f"Metadata saved to S3 | key={key}")
