CREATE OR REPLACE VIEW gold.v_requests_7d AS
SELECT
    COUNT(*)                                                                                   AS total_count,
    COUNT(*) FILTER (WHERE is_closed)                                                          AS closed_count,
    COUNT(*) FILTER (WHERE NOT is_closed)                                                      AS open_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_closed) / COUNT(*), 2)                            AS pct_closed,
    ROUND(AVG(resolution_time_in_hours)::numeric, 2)                                          AS avg_resolution_hours,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY resolution_time_in_hours)::numeric, 2)  AS median_resolution_hours,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY resolution_time_in_hours)::numeric, 2)  AS p90_resolution_hours
FROM gold.nyc311_requests_daily
WHERE created_date >= NOW() - INTERVAL '7 days';
