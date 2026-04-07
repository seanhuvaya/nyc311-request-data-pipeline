from fastapi import APIRouter

from src.api.services.requests_service import get_requests_by_complaint_type, get_requests, get_requests_daily

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
