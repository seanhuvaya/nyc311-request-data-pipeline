import os
from typing import Any

import requests


DEFAULT_TIMEOUT_SECONDS = 20


class ApiClientError(Exception):
    pass


def _base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _get(path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    url = f"{_base_url()}{path}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
    try:
        response = requests.get(url, params=clean_params, timeout=DEFAULT_TIMEOUT_SECONDS)
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


def get_requests_by_agency_daily(
    start_date: str | None = None,
    end_date: str | None = None,
    agency: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/by-agency-daily",
        params={"start_date": start_date, "end_date": end_date, "agency": agency},
    )


def get_requests_geo_daily(
    start_date: str | None = None,
    end_date: str | None = None,
    borough: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/geo-daily",
        params={"start_date": start_date, "end_date": end_date, "borough": borough},
    )


def get_open_backlog_daily(
    start_date: str | None = None,
    end_date: str | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/open-backlog-daily",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "agency": agency,
            "borough": borough,
            "complaint_type": complaint_type,
        },
    )


def get_sla_performance_daily(
    start_date: str | None = None,
    end_date: str | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/sla-performance-daily",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "agency": agency,
            "complaint_type": complaint_type,
        },
    )


def get_top_complaints_monthly(
    start_date: str | None = None,
    end_date: str | None = None,
    borough: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/top-complaints-monthly",
        params={"start_date": start_date, "end_date": end_date, "borough": borough},
    )


def get_resolution_time_distribution(
    start_date: str | None = None,
    end_date: str | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/resolution-time-distribution",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "agency": agency,
            "complaint_type": complaint_type,
        },
    )


def get_location_hotspots(
    borough: str | None = None,
    complaint_type: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/location-hotspots",
        params={"borough": borough, "complaint_type": complaint_type},
    )


def get_request_fact(
    start_date: str | None = None,
    end_date: str | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
) -> list[dict[str, Any]]:
    return _get(
        "/api/v1/requests/request-fact",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "agency": agency,
            "borough": borough,
            "complaint_type": complaint_type,
        },
    )


def get_configured_base_url() -> str:
    return _base_url()
