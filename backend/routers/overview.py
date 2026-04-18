from fastapi import APIRouter, Depends

from dependencies import get_db_session
from services.overview_service import get_requests_daily_summary, get_requests_weekly_summary
from sqlalchemy.orm import Session

from schema.overview import DailySummaryResponse, WeeklySummaryResponse

router = APIRouter(prefix="/overview", tags=["Overview"])


@router.get("/30-day-summary", response_model=list[DailySummaryResponse])
async def get_requests_daily_summary_overview(db: Session = Depends(get_db_session)):
    return await get_requests_daily_summary(db)


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_requests_weekly_summary_overview(db: Session = Depends(get_db_session)):
    return await get_requests_weekly_summary(db)
