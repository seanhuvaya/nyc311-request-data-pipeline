import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from nyc311.utils.s3 import load_metadata_from_s3, make_s3_client
from .api import extract_nyc311_requests_since

logger = logging.getLogger(__name__)


def ingest_nyc311_requests(s3_key: str, start_date: datetime | None = None) -> datetime:
    """
    Extract NYC 311 requests and save to S3.

    If start_date is None, the watermark is loaded from the S3 metadata file written
    by the previous run. Falls back to now - 2 days when no metadata exists yet.
    Pass an explicit start_date to force a backfill from a known point in time.
    """
    s3_client = make_s3_client()

    if start_date is None:
        start_date = load_metadata_from_s3(s3_client, s3_save_key=s3_key)
        if start_date is None:
            start_date = datetime.now(ZoneInfo("America/New_York")) - timedelta(days=2)
            logger.warning(f"No S3 metadata found — falling back | effective_start_date={start_date}")
        else:
            logger.info(f"Resuming from S3 watermark | watermark={start_date}")

    logger.info(f"Starting ingestion | s3_key={s3_key}, start_date={start_date}")

    latest_created_date = extract_nyc311_requests_since(
        start_date=start_date,
        s3_save_key=s3_key,
        s3_client=s3_client,
    )
    logger.info(f"Extraction complete | latest_created_date={latest_created_date}")

    return latest_created_date
