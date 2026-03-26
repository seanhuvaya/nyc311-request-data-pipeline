import logging
from typing import Tuple

import pandas as pd
import requests

from config import settings
from metadata import log_extraction_start, log_extraction_end
from models.extraction_metadata import ExtractionStatus

logger = logging.getLogger(__name__)


def fetch_all_311_requests(
        last_update_date: str, limit: int = 1000
) -> Tuple[pd.DataFrame, int]:
    """Fetch all 311 requests since last_update_date using Socrata-style pagination.

    Returns:
        Tuple of (DataFrame with all records, extraction_id)
    """
    params = {
        "$where": f"created_date > '{last_update_date}'",
        "$order": "created_date ASC",
        "$limit": limit,
        "$offset": 0,
    }

    extraction_id = log_extraction_start(params)
    ingested_data: list = []

    try:
        logger.info(f"Starting fetch from {settings.DATASET_URL} with date filter: {last_update_date}")

        while True:
            response = requests.get(settings.DATASET_URL, params=params, timeout=30)

            if not response.ok:
                error_msg = response.json().get("message", response.text)
                log_extraction_end(
                    extraction_id=extraction_id,
                    status=ExtractionStatus.FAILED.value,
                    error_message=error_msg,
                )
                raise RuntimeError(
                    f"API request failed [{response.status_code}]: {error_msg}"
                )

            data = response.json()
            if not data:
                break

            ingested_data.extend(data)
            params["$offset"] += limit

        logger.info(f"Successfully fetched {len(ingested_data)} records")
        return pd.DataFrame(ingested_data), extraction_id

    except Exception as e:
        logger.exception(f"Extraction failed for ID {extraction_id}")
        log_extraction_end(
            extraction_id=extraction_id,
            status=ExtractionStatus.FAILED.value,
            error_message=str(e),
        )
        raise
