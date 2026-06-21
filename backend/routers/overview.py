from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from schema.day_of_week import DayOfWeekStat
from schema.overview import SummaryStatsResponse
from services import day_of_week_service
from services.overview_service import get_requests_30d_summary, get_requests_7d_summary

router = APIRouter(prefix="/overview", tags=["Overview"])


@router.get("/30-day-summary", response_model=SummaryStatsResponse)
async def get_30d_summary(db: AsyncSession = Depends(get_db_session)):
    return await get_requests_30d_summary(db)


@router.get("/weekly-summary", response_model=SummaryStatsResponse)
async def get_7d_summary(db: AsyncSession = Depends(get_db_session)):
    return await get_requests_7d_summary(db)


@router.get("/day-of-week", response_model=List[DayOfWeekStat])
async def get_day_of_week(db: AsyncSession = Depends(get_db_session)):
    return await day_of_week_service.get_day_of_week_stats(db)
