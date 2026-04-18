from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_requests_daily_summary(db: AsyncSession):
    query = text("""
                 SELECT *
                 FROM gold.nyc311_requests_daily_summary
                 WHERE request_date >= DATE_TRUNC('day', NOW()) - INTERVAL '30 days'
                 ORDER BY request_date
                 """)
    return (await db.execute(query)).mappings().all()


async def get_requests_weekly_summary(db: AsyncSession):
    query = text("""
                 SELECT *
                 FROM gold.nyc311_requests_weekly_summary
                 ORDER BY week_start DESC
                 LIMIT 1
                 """)
    return (await db.execute(query)).mappings().first()
