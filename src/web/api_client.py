import os
from typing import Any

import requests


DEFAULT_TIMEOUT_SECONDS = 20


class ApiClientError(Exception):
    pass


def _base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _get(path: str) -> list[dict[str, Any]]:
    url = f"{_base_url()}{path}"
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ApiClientError(f"Request failed for {url}: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise ApiClientError(f"Invalid JSON response from {url}") from exc

    if not isinstance(payload, list):
        raise ApiClientError(f"Unexpected response shape from {url}: expected a list")

    return payload


def get_requests() -> list[dict[str, Any]]:
    return _get("/api/v1/requests/")


def get_requests_daily() -> list[dict[str, Any]]:
    return _get("/api/v1/requests/daily")


def get_requests_by_complaint_type() -> list[dict[str, Any]]:
    return _get("/api/v1/requests/by-complaint-type")


def get_configured_base_url() -> str:
    return _base_url()
