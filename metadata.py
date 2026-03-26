from datetime import datetime, timezone
import logging
from typing import Optional

from db import get_db_session
from models import ExtractMetadata
from models.extraction_metadata import ExtractionStatus

logger = logging.getLogger(__name__)


def log_extraction_start(extract_params: dict) -> int:
    """Create a new extraction metadata record and return its ID."""
    with get_db_session() as session:
        record = ExtractMetadata(
            status=ExtractionStatus.INITIATED.value,
            parameters=extract_params or {},
        )
        session.add(record)
        session.flush()
        logger.info(f"Created new extract metadata record: {record.id}")
        return record.id


def log_extraction_end(
        extraction_id: int,
        status: str,
        num_records: int = 0,
        latest_record_created_date: Optional[datetime] = None,
        error_message: Optional[str] = None,
) -> None:
    """Update extraction metadata with final status and details."""
    with get_db_session() as session:
        record = session.get(ExtractMetadata, extraction_id)
        if not record:
            msg = f"Extraction record {extraction_id} not found"
            logger.error(msg)
            raise LookupError(msg)

        record.extraction_completed_at = datetime.now(timezone.utc)
        record.status = status
        record.num_records_pulled = num_records
        record.latest_record_created_date = latest_record_created_date
        record.error_message = error_message

        logger.info(f"Extraction {extraction_id} completed with status: {status}")
