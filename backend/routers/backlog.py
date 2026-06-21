from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from schema.backlog import BacklogAging
from services import backlog_service

router = APIRouter(prefix="/backlog", tags=["Backlog"])


@router.get("/aging", response_model=BacklogAging)
async def get_backlog_aging(db: AsyncSession = Depends(get_db_session)):
    return await backlog_service.get_backlog_aging(db)
