import logging
from datetime import datetime, timezone, timedelta

from src.db.models import ExtractMetadata
from src.db.models.extraction_metadata import ExtractionStatus
from src.db.session import get_db_session
from src.extract.client import service_requests_client
from src.extract.metadata import log_extraction_start, log_extraction_end

logger = logging.getLogger(__name__)


def incremental_pull():
    with get_db_session() as session:
        extract_metadata = session.query(ExtractMetadata) \
            .order_by(ExtractMetadata.latest_record_created_date.desc()) \
            .first()

        if extract_metadata and extract_metadata.latest_record_created_date:
            latest_record_created_date = extract_metadata.latest_record_created_date
        else:
            latest_record_created_date = datetime.now(timezone.utc) - timedelta(days=1)

    start_date = latest_record_created_date.replace(hour=0, minute=0, second=0, microsecond=0)

    extraction_id = log_extraction_start(extract_params={'start_date': start_date.isoformat()})

    try:
        data = service_requests_client.fetch_nyc311_service_requests(start_date=start_date)

        latest_record_created_date = data['created_date'].max()
        log_extraction_end(extraction_id, ExtractionStatus.SUCCESS.value, len(data), latest_record_created_date)

    except Exception as e:
        logger.error(f"Incremental pull failed: {e}")
        log_extraction_end(extraction_id, ExtractionStatus.FAILED.value, error_message=str(e))


if __name__ == "__main__":
    from src.utils.logger import setup_logging

    setup_logging()
    incremental_pull()
