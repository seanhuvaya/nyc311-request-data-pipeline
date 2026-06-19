import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from metadata.service import get_metadata
from utils.cloud import make_s3_client
from .nyc_311_api_ingest import extract_nyc311_requests_since

logger = logging.getLogger(__name__)


def ingest_nyc311_daily_requests(s3_key: str) -> datetime:
    logger.info(f"Starting ingestion | s3_key={s3_key}")

    metadata = get_metadata(pipeline_name="nyc_311", source_name="erm2-nwe9", watermark_column="created_date")

    if metadata:
        start_date = metadata.watermark_value
        logger.info(f"Resuming from watermark | watermark_value={start_date}")
    else:
        start_date = datetime.now(ZoneInfo("America/New_York")) - timedelta(days=2)
        logger.warning(f"No metadata found — falling back to start_date param | effective_start_date={start_date}")

    logger.info(f"Extracting records since {start_date}")
    latest_created_date = extract_nyc311_requests_since(
        start_date=start_date,
        s3_save_key=s3_key,
        s3_client=make_s3_client(),
    )
    logger.info(f"Extraction complete | latest_created_date={latest_created_date}")

    return latest_created_date
