from fastapi import APIRouter, Depends

from dependencies import get_db_session
from services.overview_service import get_requests_30d_summary, get_requests_7d_summary
from sqlalchemy.orm import Session

from schema.overview import SummaryStatsResponse

router = APIRouter(prefix="/overview", tags=["Overview"])


@router.get("/30-day-summary", response_model=SummaryStatsResponse)
async def get_30d_summary(db: Session = Depends(get_db_session)):
    return await get_requests_30d_summary(db)


@router.get("/weekly-summary", response_model=SummaryStatsResponse)
async def get_7d_summary(db: Session = Depends(get_db_session)):
    return await get_requests_7d_summary(db)
