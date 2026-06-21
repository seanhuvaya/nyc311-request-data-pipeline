from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_requests_30d_summary(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_requests_30d"))).mappings().first()


async def get_requests_7d_summary(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_requests_7d"))).mappings().first()
