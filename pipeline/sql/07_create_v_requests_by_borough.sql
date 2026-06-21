CREATE OR REPLACE VIEW gold.v_requests_by_borough AS
SELECT
    l.borough,
    COUNT(*)                                                                                    AS total_count,
    COUNT(*) FILTER (WHERE f.is_closed)                                                         AS closed_count,
    COUNT(*) FILTER (WHERE NOT f.is_closed)                                                     AS open_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_closed) / COUNT(*), 2)                           AS pct_closed,
    ROUND(AVG(f.resolution_time_in_hours)::numeric, 2)                                         AS avg_resolution_hours,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_time_in_hours)::numeric, 2) AS median_resolution_hours
FROM gold.nyc311_requests_daily f
JOIN gold.dim_location l ON f.location_id = l.location_id
GROUP BY l.borough
ORDER BY total_count DESC;
