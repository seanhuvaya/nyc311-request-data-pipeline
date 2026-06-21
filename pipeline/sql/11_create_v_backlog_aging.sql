CREATE OR REPLACE VIEW gold.v_backlog_aging AS
SELECT
    SUM(CASE WHEN NOW() - created_date <  INTERVAL '7 days'  THEN 1 ELSE 0 END) AS lt_7d,
    SUM(CASE WHEN NOW() - created_date >= INTERVAL '7 days'
             AND NOW() - created_date <  INTERVAL '30 days'  THEN 1 ELSE 0 END) AS d7_to_30,
    SUM(CASE WHEN NOW() - created_date >= INTERVAL '30 days'
             AND NOW() - created_date <  INTERVAL '90 days'  THEN 1 ELSE 0 END) AS d30_to_90,
    SUM(CASE WHEN NOW() - created_date >= INTERVAL '90 days' THEN 1 ELSE 0 END) AS gt_90d
FROM gold.nyc311_requests_daily
WHERE NOT is_closed;
