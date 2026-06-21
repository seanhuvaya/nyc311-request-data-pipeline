from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from schema.borough import BoroughStat
from services import borough_service

router = APIRouter(prefix="/borough", tags=["Borough"])


@router.get("/summary", response_model=List[BoroughStat])
async def get_borough_summary(db: AsyncSession = Depends(get_db_session)):
    return await borough_service.get_borough_summary(db)
