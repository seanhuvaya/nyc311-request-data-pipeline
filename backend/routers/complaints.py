from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from schema.complaints import ComplaintTypeStat
from services import complaints_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("/summary", response_model=List[ComplaintTypeStat])
async def get_complaints_summary(db: AsyncSession = Depends(get_db_session)):
    return await complaints_service.get_complaints_summary(db)
