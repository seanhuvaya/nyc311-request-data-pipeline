from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_day_of_week_stats(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_requests_by_day_of_week"))).mappings().all()
