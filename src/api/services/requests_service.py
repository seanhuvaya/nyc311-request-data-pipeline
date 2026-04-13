from datetime import date

from sqlalchemy import select

from src.db.models import (
    NYC311ServiceRequest,
    NYC311RequestsDaily,
    NYC311RequestsByComplaintDaily,
    NYC311RequestsByAgencyDaily,
    NYC311RequestsGeoDaily,
    NYC311OpenBacklogDaily,
    NYC311SLAPerformanceDaily,
    NYC311TopComplaintsMonthly,
    NYC311ResolutionTimeDistribution,
    NYC311LocationHotspots,
    NYC311GoldRequestFact,
)
from src.db.session import get_db_session


def get_requests_by_complaint_type():
    with get_db_session() as session:
        stmt = select(NYC311RequestsByComplaintDaily)

        return session.execute(stmt).scalars().all()


def get_requests():
    with get_db_session() as session:
        stmt = select(NYC311ServiceRequest)

        return session.execute(stmt).scalars().all()


def get_requests_daily():
    with get_db_session() as session:
        stmt = select(NYC311RequestsDaily)

        return session.execute(stmt).scalars().all()


def get_requests_by_agency_daily(start_date: date | None = None, end_date: date | None = None, agency: str | None = None):
    with get_db_session() as session:
        stmt = select(NYC311RequestsByAgencyDaily)
        if start_date:
            stmt = stmt.where(NYC311RequestsByAgencyDaily.request_date >= start_date)
        if end_date:
            stmt = stmt.where(NYC311RequestsByAgencyDaily.request_date <= end_date)
        if agency:
            stmt = stmt.where(NYC311RequestsByAgencyDaily.agency == agency)
        stmt = stmt.order_by(NYC311RequestsByAgencyDaily.request_date.asc(), NYC311RequestsByAgencyDaily.agency.asc())
        return session.execute(stmt).scalars().all()


def get_requests_geo_daily(start_date: date | None = None, end_date: date | None = None, borough: str | None = None):
    with get_db_session() as session:
        stmt = select(NYC311RequestsGeoDaily)
        if start_date:
            stmt = stmt.where(NYC311RequestsGeoDaily.request_date >= start_date)
        if end_date:
            stmt = stmt.where(NYC311RequestsGeoDaily.request_date <= end_date)
        if borough:
            stmt = stmt.where(NYC311RequestsGeoDaily.borough == borough)
        stmt = stmt.order_by(NYC311RequestsGeoDaily.request_date.asc(), NYC311RequestsGeoDaily.borough.asc())
        return session.execute(stmt).scalars().all()


def get_open_backlog_daily(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
):
    with get_db_session() as session:
        stmt = select(NYC311OpenBacklogDaily)
        if start_date:
            stmt = stmt.where(NYC311OpenBacklogDaily.snapshot_date >= start_date)
        if end_date:
            stmt = stmt.where(NYC311OpenBacklogDaily.snapshot_date <= end_date)
        if agency:
            stmt = stmt.where(NYC311OpenBacklogDaily.agency == agency)
        if borough:
            stmt = stmt.where(NYC311OpenBacklogDaily.borough == borough)
        if complaint_type:
            stmt = stmt.where(NYC311OpenBacklogDaily.complaint_type == complaint_type)
        stmt = stmt.order_by(
            NYC311OpenBacklogDaily.snapshot_date.asc(),
            NYC311OpenBacklogDaily.agency.asc(),
            NYC311OpenBacklogDaily.borough.asc(),
            NYC311OpenBacklogDaily.complaint_type.asc(),
        )
        return session.execute(stmt).scalars().all()


def get_sla_performance_daily(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
):
    with get_db_session() as session:
        stmt = select(NYC311SLAPerformanceDaily)
        if start_date:
            stmt = stmt.where(NYC311SLAPerformanceDaily.request_date >= start_date)
        if end_date:
            stmt = stmt.where(NYC311SLAPerformanceDaily.request_date <= end_date)
        if agency:
            stmt = stmt.where(NYC311SLAPerformanceDaily.agency == agency)
        if complaint_type:
            stmt = stmt.where(NYC311SLAPerformanceDaily.complaint_type == complaint_type)
        stmt = stmt.order_by(
            NYC311SLAPerformanceDaily.request_date.asc(),
            NYC311SLAPerformanceDaily.agency.asc(),
            NYC311SLAPerformanceDaily.complaint_type.asc(),
        )
        return session.execute(stmt).scalars().all()


def get_top_complaints_monthly(start_date: date | None = None, end_date: date | None = None, borough: str | None = None):
    with get_db_session() as session:
        stmt = select(NYC311TopComplaintsMonthly)
        if start_date:
            stmt = stmt.where(NYC311TopComplaintsMonthly.month >= start_date)
        if end_date:
            stmt = stmt.where(NYC311TopComplaintsMonthly.month <= end_date)
        if borough:
            stmt = stmt.where(NYC311TopComplaintsMonthly.borough == borough)
        stmt = stmt.order_by(
            NYC311TopComplaintsMonthly.month.asc(),
            NYC311TopComplaintsMonthly.borough.asc(),
            NYC311TopComplaintsMonthly.rank_in_borough.asc(),
        )
        return session.execute(stmt).scalars().all()


def get_resolution_time_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    complaint_type: str | None = None,
):
    with get_db_session() as session:
        stmt = select(NYC311ResolutionTimeDistribution)
        if start_date:
            stmt = stmt.where(NYC311ResolutionTimeDistribution.request_month >= start_date)
        if end_date:
            stmt = stmt.where(NYC311ResolutionTimeDistribution.request_month <= end_date)
        if agency:
            stmt = stmt.where(NYC311ResolutionTimeDistribution.agency == agency)
        if complaint_type:
            stmt = stmt.where(NYC311ResolutionTimeDistribution.complaint_type == complaint_type)
        stmt = stmt.order_by(
            NYC311ResolutionTimeDistribution.request_month.asc(),
            NYC311ResolutionTimeDistribution.agency.asc(),
            NYC311ResolutionTimeDistribution.complaint_type.asc(),
            NYC311ResolutionTimeDistribution.resolution_bucket.asc(),
        )
        return session.execute(stmt).scalars().all()


def get_location_hotspots(borough: str | None = None, complaint_type: str | None = None):
    with get_db_session() as session:
        stmt = select(NYC311LocationHotspots)
        if borough:
            stmt = stmt.where(NYC311LocationHotspots.borough == borough)
        if complaint_type:
            stmt = stmt.where(NYC311LocationHotspots.complaint_type == complaint_type)
        stmt = stmt.order_by(NYC311LocationHotspots.request_count.desc())
        return session.execute(stmt).scalars().all()


def get_request_fact(
    start_date: date | None = None,
    end_date: date | None = None,
    agency: str | None = None,
    borough: str | None = None,
    complaint_type: str | None = None,
):
    with get_db_session() as session:
        stmt = select(NYC311GoldRequestFact)
        if start_date:
            stmt = stmt.where(NYC311GoldRequestFact.created_date >= start_date)
        if end_date:
            stmt = stmt.where(NYC311GoldRequestFact.created_date <= end_date)
        if agency:
            stmt = stmt.where(NYC311GoldRequestFact.agency == agency)
        if borough:
            stmt = stmt.where(NYC311GoldRequestFact.borough == borough)
        if complaint_type:
            stmt = stmt.where(NYC311GoldRequestFact.complaint_type == complaint_type)
        stmt = stmt.order_by(NYC311GoldRequestFact.created_date.desc())
        return session.execute(stmt).scalars().all()
