from fastapi import APIRouter

from datetime import date

from src.api.services.requests_service import (
    get_requests_by_complaint_type,
    get_requests,
    get_requests_daily,
    get_requests_by_agency_daily,
    get_requests_geo_daily,
    get_open_backlog_daily,
    get_sla_performance_daily,
    get_top_complaints_monthly,
    get_resolution_time_distribution,
    get_location_hotspots,
    get_request_fact,
)

router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
)


@router.get("/")
async def requests_all():
    return get_requests()


@router.get("/daily")
async def requests_daily():
    return get_requests_daily()


@router.get("/by-complaint-type")
async def requests_by_complaint_type():
    return get_requests_by_complaint_type()


@router.get("/by-agency-daily")
async def requests_by_agency(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
):
    return get_requests_by_agency_daily(start_date=start_date, end_date=end_date, agency=agency)


@router.get("/geo-daily")
async def requests_geo(
    start_date: date | None = None,
    end_date: date | None = None,
    borough: str | None = None,
):
    return get_requests_geo_daily(start_date=start_date, end_date=end_date, borough=borough)


@router.get("/open-backlog-daily")
async def open_backlog(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
):
    return get_open_backlog_daily(
        start_date=start_date,
        end_date=end_date,
        agency=agency,
        borough=borough,
        complaint_type=complaint_type,
    )


@router.get("/sla-performance-daily")
async def sla_performance(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
):
    return get_sla_performance_daily(
        start_date=start_date,
        end_date=end_date,
        agency=agency,
        complaint_type=complaint_type,
    )


@router.get("/top-complaints-monthly")
async def top_complaints_monthly(
    start_date: date | None = None,
    end_date: date | None = None,
    borough: str | None = None,
):
    return get_top_complaints_monthly(start_date=start_date, end_date=end_date, borough=borough)


@router.get("/resolution-time-distribution")
async def resolution_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
):
    return get_resolution_time_distribution(
        start_date=start_date,
        end_date=end_date,
        agency=agency,
        complaint_type=complaint_type,
    )


@router.get("/location-hotspots")
async def location_hotspots(
    borough: str | None = None,
    complaint_type: str | None = None,
):
    return get_location_hotspots(borough=borough, complaint_type=complaint_type)


@router.get("/request-fact")
async def request_fact(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
):
    return get_request_fact(
        start_date=start_date,
        end_date=end_date,
        agency=agency,
        borough=borough,
        complaint_type=complaint_type,
    )
