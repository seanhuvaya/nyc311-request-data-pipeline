from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_agency_performance(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_requests_by_agency"))).mappings().all()
