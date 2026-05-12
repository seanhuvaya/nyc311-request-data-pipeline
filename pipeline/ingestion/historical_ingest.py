from datetime import datetime
from typing import Tuple

from .nyc_311_api_ingest import extract_nyc311_requests_since


def backfill_nyc311_requests(s3_key: str, start_date: datetime = datetime(2026, 4, 12)) -> Tuple[str, datetime]:
    latest_created_date = extract_nyc311_requests_since(
        start_date=start_date,
        s3_save_key=s3_key
    )
    return latest_created_date
