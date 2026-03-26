from typing import List

from config import settings
from db import get_db_session
from models import ExtractMetadata
from models.extraction_metadata import ExtractionStatus


def get_raw_file_paths() -> List[str]:
    """Get all completed raw parquet paths from metadata."""
    with get_db_session() as session:
        records = session.query(ExtractMetadata).where(
            ExtractMetadata.status == ExtractionStatus.COMPLETED.value
        ).all()

        return [
            f"s3a://{settings.AWS_S3_BUCKET}/raw/date={record.latest_record_created_date.strftime('%Y-%m-%d')}/"
            f"{settings.AWS_S3_DATA_PARQUET_FILENAME}"
            for record in records
        ]


def get_silver_file_key(date_str: str) -> str:
    """Generate silver layer S3 key."""
    return f"silver/date={date_str}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
