import os
import sys
import pandas as pd

from datetime import date, datetime, timedelta, timezone
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from utils.config import env_config, yml_config


class NYC311Client:
    def __init__(self):
        self.base_url = yml_config.config['api']['socrata_domain']

        self.headers = {
            "X-App-Token": env_config.APP_TOKEN,
            "Accept": "application/json"
        }

        self.session = Session()
        self.session.headers.update(self.headers)

        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get(self, params=None):
        url = self.base_url + f"/{yml_config.config['api']['dataset_id']}"
        response = self.session.request(
            "GET",
            url,
            params=params
        )

        if not response.ok:
            raise Exception(
                f"GET {yml_config.config['api']['dataset_id']} failed [{response.status_code}]: {response.text}"
            )

        return response.json()

    def fetch_all_complaints(self, last_update_date, limit: int = 1000, offset: int = 0):
        """
        Fetches all complaints created after the given last_update_date by handling pagination.
        Assumes last_update_date is in 'YYYY-MM-DD' format. To avoid potential duplicates or misses,
        the filter uses 'created_date > "{last_update_date}T23:59:59.999"' to get records strictly
        after the end of that day. If you want to include the day or use a precise timestamp, adjust accordingly.
        """
        all_records = []
        where_clause = f"created_date > '{last_update_date}T00:00:00.000'"

        while True:
            params = {
                "$select": "unique_key,created_date,closed_date,agency,agency_name,complaint_type,descriptor,"
                           "incident_zip,borough,status,open_data_channel_type,latitude,longitude",
                "$where": where_clause,
                "$order": "created_date ASC",
                "$limit": limit,
                "$offset": offset
            }
            records = self._get(params=params)
            if not records:
                break
            all_records.extend(records)
            offset += limit

        return all_records


def ingest():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    complaints = NYC311Client().fetch_all_complaints(yesterday)
    complaints_df = pd.DataFrame(complaints)

    raw_data_path = yml_config.config['data']['raw_path']
    raw_file_path = os.path.join(raw_data_path, f'nyc311_raw_{datetime.now(timezone.utc).timestamp()}.csv')

    complaints_df.to_csv(raw_file_path, index=False)


if __name__ == "__main__":
    ingest()
