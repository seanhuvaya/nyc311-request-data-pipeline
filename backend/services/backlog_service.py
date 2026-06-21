from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_backlog_aging(db: AsyncSession):
    return (await db.execute(text("SELECT * FROM gold.v_backlog_aging"))).mappings().first()
