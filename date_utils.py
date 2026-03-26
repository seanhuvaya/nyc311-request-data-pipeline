from datetime import datetime, timedelta, timezone

from db import get_db_session
from models import ExtractMetadata


def get_latest_record_created_date() -> datetime:
    """Determine the starting date for incremental extraction."""
    with get_db_session() as session:
        latest = (
            session.query(ExtractMetadata.latest_record_created_date)
            .order_by(ExtractMetadata.latest_record_created_date.desc())
            .first()
        )

    if latest and latest[0]:
        return latest[0]

    # Fallback: yesterday at midnight UTC
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)


def format_date_for_api(dt: datetime) -> str:
    """Format datetime for the API $where clause."""
    return dt.strftime("%Y-%m-%dT00:00:00.000")
