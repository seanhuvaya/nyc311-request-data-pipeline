from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_requests_30d_summary(db: AsyncSession):
    result = await db.execute(text("""
        SELECT
            request_date,
            total_count,
            closed_count,
            open_count,
            pct_closed              AS pct_closure_daily,
            avg_resolution_hours    AS avg_resolution_time_in_hours,
            median_resolution_hours AS median_resolution_time_in_hours
        FROM gold.v_requests_daily
        WHERE request_date >= NOW() - INTERVAL '30 days'
        ORDER BY request_date ASC
    """))
    return result.mappings().all()


async def get_requests_7d_summary(db: AsyncSession):
    result = await db.execute(text("""
        WITH current_week AS (
            SELECT
                MIN(request_date) AS week_start,
                SUM(total_count)  AS week_total_requests,
                SUM(closed_count) AS week_closed_requests,
                ROUND(100.0 * SUM(closed_count) / NULLIF(SUM(total_count), 0), 2)
                    AS week_closed_requests_pct,
                ROUND(AVG(avg_resolution_hours)::numeric, 2)
                    AS week_avg_resolution_time_in_hours
            FROM gold.v_requests_daily
            WHERE request_date >= NOW() - INTERVAL '7 days'
        ),
        prev_week AS (
            SELECT
                SUM(total_count)  AS prev_week_total_requests,
                SUM(closed_count) AS prev_week_total_closed_requests,
                ROUND(AVG(avg_resolution_hours)::numeric, 2)
                    AS prev_week_avg_resolution_time_in_hours
            FROM gold.v_requests_daily
            WHERE request_date >= NOW() - INTERVAL '14 days'
              AND request_date <  NOW() - INTERVAL '7 days'
        )
        SELECT
            cw.week_start,
            cw.week_total_requests,
            cw.week_closed_requests,
            cw.week_closed_requests_pct,
            cw.week_avg_resolution_time_in_hours,
            pw.prev_week_total_requests,
            pw.prev_week_total_closed_requests,
            ROUND(
                100.0 * (cw.week_total_requests - pw.prev_week_total_requests)
                / NULLIF(pw.prev_week_total_requests, 0), 2
            ) AS prev_week_change_in_requests_pct,
            ROUND(
                100.0 * (cw.week_closed_requests - pw.prev_week_total_closed_requests)
                / NULLIF(pw.prev_week_total_closed_requests, 0), 2
            ) AS prev_week_change_in_closed_requests_pct,
            pw.prev_week_avg_resolution_time_in_hours,
            ROUND(
                100.0 * (cw.week_avg_resolution_time_in_hours - pw.prev_week_avg_resolution_time_in_hours)
                / NULLIF(pw.prev_week_avg_resolution_time_in_hours, 0), 2
            ) AS prev_week_avg_resolution_time_in_hours_pct
        FROM current_week cw, prev_week pw
    """))
    return result.mappings().first()
