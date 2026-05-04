import logging
from datetime import timezone, datetime, timedelta

from metadata.service import update_metadata, get_metadata
from .nyc_311_api_ingest import extract_nyc311_requests_since

logger = logging.getLogger(__name__)


def ingest_nyc311_daily_requests():
    metadata = get_metadata(pipeline_name="nyc_311", source_name="erm2-nwe9", watermark_column="created_date")

    start_date = metadata.watermark_value if metadata else datetime.now(timezone.utc) - timedelta(days=1)

    logger.info(f"Fetching records since: {start_date}")

    latest_created_date = extract_nyc311_requests_since(
        extraction_date=datetime.now(timezone.utc),
        start_date=start_date
    )

    update_metadata(pipeline_name="nyc_311", source_name="erm2-nwe9", watermark_column="created_date",
                    watermark_value=latest_created_date)
