import logging
from datetime import datetime

from src.extract.client import service_requests_client

logger = logging.getLogger(__name__)


def incremental_pull(start_date: datetime):

    try:
        data = service_requests_client.fetch_nyc311_service_requests(start_date=start_date)

        return data
    except Exception as e:
        logger.error(f"Incremental pull failed: {e}")


if __name__ == "__main__":
    from src.utils.logger import setup_logging

    setup_logging()
    incremental_pull()
