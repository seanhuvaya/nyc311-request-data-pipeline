CREATE OR REPLACE VIEW gold.v_requests_by_complaint_type AS
SELECT
    ct.complaint_type,
    COUNT(*)                                                                                    AS total_count,
    COUNT(*) FILTER (WHERE f.is_closed)                                                         AS closed_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_closed) / COUNT(*), 2)                           AS pct_closed,
    ROUND(AVG(f.resolution_time_in_hours)::numeric, 2)                                         AS avg_resolution_hours,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.resolution_time_in_hours)::numeric, 2) AS median_resolution_hours,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY f.resolution_time_in_hours)::numeric, 2) AS p90_resolution_hours
FROM gold.nyc311_requests_daily f
JOIN gold.dim_complaint_type ct ON f.complaint_type_id = ct.complaint_type_id
GROUP BY ct.complaint_type
ORDER BY total_count DESC;
