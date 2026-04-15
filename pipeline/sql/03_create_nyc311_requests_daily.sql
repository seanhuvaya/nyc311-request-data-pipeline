CREATE TABLE IF NOT EXISTS gold.nyc311_requests_daily (
    request_date DATE NOT NULL,
    closed_count INT NOT NULL,
    open_count INT NOT NULL,
    total_count INT NOT NULL,
    avg_resolution_time_in_hours NUMERIC(10,2),
    median_resolution_time_in_hours NUMERIC(10,2),
    pct_closure_daily NUMERIC(10,2),

    PRIMARY KEY (request_date)
)