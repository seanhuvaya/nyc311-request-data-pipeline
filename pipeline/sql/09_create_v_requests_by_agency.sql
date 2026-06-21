CREATE OR REPLACE VIEW gold.v_requests_by_agency AS
SELECT
    a.agency_code,
    COUNT(*)                                                                                    AS total_count,
    COUNT(*) FILTER (WHERE f.is_closed)                                                         AS closed_count,
    COUNT(*) FILTER (WHERE NOT f.is_closed)                                                     AS open_backlog,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_closed) / COUNT(*), 2)                           AS pct_closed,
    ROUND(AVG(f.resolution_time_in_hours)::numeric, 2)                                         AS avg_resolution_hours,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY f.resolution_time_in_hours)::numeric, 2) AS p90_resolution_hours
FROM gold.nyc311_requests_daily f
JOIN gold.dim_agency a ON f.agency_id = a.agency_id
GROUP BY a.agency_code
ORDER BY total_count DESC;
