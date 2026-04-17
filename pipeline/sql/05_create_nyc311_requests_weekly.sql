CREATE TABLE IF NOT EXISTS gold.nyc311_requests_weekly_summary
(
    week_start                                 DATE           NOT NULL PRIMARY KEY,
    week_closed_requests                       INT            NOT NULL,
    week_total_requests                        INT            NOT NULL,
    week_closed_requests_pct                   NUMERIC(10, 2) NOT NULL,
    week_avg_resolution_time_in_hours          NUMERIC(10, 2) NOT NULL,
    prev_week_total_requests                   INT            NOT NULL,
    prev_week_total_closed_requests            INT            NOT NULL,
    prev_week_change_in_requests_pct           NUMERIC(10, 2),
    prev_week_change_in_closed_requests_pct    NUMERIC(10, 2),
    prev_week_avg_resolution_time_in_hours     NUMERIC(10, 2) NOT NULL,
    prev_week_avg_resolution_time_in_hours_pct NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS staging.nyc311_requests_weekly_summary
(
    week_start                                 DATE           NOT NULL PRIMARY KEY,
    week_closed_requests                       INT            NOT NULL,
    week_total_requests                        INT            NOT NULL,
    week_closed_requests_pct                   NUMERIC(10, 2) NOT NULL,
    week_avg_resolution_time_in_hours          NUMERIC(10, 2) NOT NULL,
    prev_week_total_requests                   INT            NOT NULL,
    prev_week_total_closed_requests            INT            NOT NULL,
    prev_week_change_in_requests_pct           NUMERIC(10, 2),
    prev_week_change_in_closed_requests_pct    NUMERIC(10, 2),
    prev_week_avg_resolution_time_in_hours     NUMERIC(10, 2) NOT NULL,
    prev_week_avg_resolution_time_in_hours_pct NUMERIC(10, 2)
);