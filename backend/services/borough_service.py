from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_borough_summary(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_requests_by_borough"))).mappings().all()
