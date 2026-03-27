import logging
from datetime import datetime

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from src.utils.config import settings

logger = logging.getLogger(__name__)


class NYC311ServiceRequestsClient:
    def __init__(self, resource_url: str):
        self.resource_url = resource_url

        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_nyc311_service_requests(self, start_date: datetime, limit: int = 1000) -> pd.DataFrame:
        params = {
            "$where": f"created_date > '{start_date.strftime('%Y-%m-%d')}'",
            "$order": "created_date ASC",
            "$limit": limit,
            "$offset": 0,
        }

        logger.info(f"Fetching 311 requests from date: {start_date}")

        nyc311_service_requests = []

        while True:
            response = self.session.get(self.resource_url, params=params, timeout=30)

            if not response.ok:
                err_msg = response.json().get("message", response.text)
                logger.error(f"API request failed [{response.status_code}]: {err_msg}")
                raise Exception(err_msg)

            data = response.json()
            if not data:
                break

            nyc311_service_requests.extend(data)
            params["$offset"] += limit

        logger.info(f"Successfully fetched {len(nyc311_service_requests)} requests")
        return pd.DataFrame(nyc311_service_requests)


if __name__ == "__main__":
    from src.utils.logger import setup_logging

    setup_logging()
    service_requests_client = NYC311ServiceRequestsClient(settings.DATASET_URL)
    res_data = service_requests_client.fetch_nyc311_service_requests(start_date=datetime(2026, 3, 24))
    print(res_data.head())
