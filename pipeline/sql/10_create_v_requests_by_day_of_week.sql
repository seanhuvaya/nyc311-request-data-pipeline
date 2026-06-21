CREATE OR REPLACE VIEW gold.v_requests_by_day_of_week AS
SELECT
    d.day_of_week,
    d.day_name,
    COUNT(*)                                                                  AS total_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_closed) / COUNT(*), 2)         AS pct_closed,
    ROUND(AVG(f.resolution_time_in_hours)::numeric, 2)                       AS avg_resolution_hours
FROM gold.nyc311_requests_daily f
JOIN gold.dim_date d ON f.date_id = d.date_id
GROUP BY d.day_of_week, d.day_name
ORDER BY d.day_of_week;
