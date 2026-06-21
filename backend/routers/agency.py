from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from schema.agency import AgencyStat
from services import agency_service

router = APIRouter(prefix="/agency", tags=["Agency"])


@router.get("/performance", response_model=List[AgencyStat])
async def get_agency_performance(db: AsyncSession = Depends(get_db_session)):
    return await agency_service.get_agency_performance(db)
