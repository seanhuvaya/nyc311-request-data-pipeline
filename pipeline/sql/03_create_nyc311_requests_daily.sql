CREATE TABLE IF NOT EXISTS gold.nyc311_requests_daily
(
    unique_key               BIGINT PRIMARY KEY,
    date_id                  INT REFERENCES gold.dim_date(date_id),
    agency_id                INT REFERENCES gold.dim_agency(agency_id),
    complaint_type_id        INT REFERENCES gold.dim_complaint_type(complaint_type_id),
    location_id              INT REFERENCES gold.dim_location(location_id),
    created_date             TIMESTAMP        NOT NULL,
    closed_date              TIMESTAMP        NULL,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    location_type            TEXT,
    address_type             TEXT,
    status                   TEXT,
    is_closed                BOOLEAN          NOT NULL DEFAULT FALSE,
    resolution_time_in_hours NUMERIC(10, 2),
    created_at               TIMESTAMP        DEFAULT CURRENT_TIMESTAMP
);
