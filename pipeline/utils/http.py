import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session_with_retry(
        total_retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (429, 500, 502, 503, 504)) -> requests.Session:
    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
