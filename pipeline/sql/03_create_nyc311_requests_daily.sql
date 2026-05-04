CREATE TABLE IF NOT EXISTS staging.nyc311_requests_daily
(
    unique_key               BIGINT PRIMARY KEY,
    created_date             TIMESTAMP NOT NULL,
    closed_date              TIMESTAMP NULL,
    agency                   TEXT,
    complaint_type           TEXT,
    descriptor               TEXT,
    community_board          TEXT,
    incident_zip             VARCHAR(10),
    location_type            TEXT,
    address_type             TEXT,
    city                     TEXT,
    borough                  TEXT,
    status                   TEXT,
    council_district         INTEGER,
    police_precinct          TEXT,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    is_closed                BOOLEAN   NOT NULL DEFAULT FALSE,
    resolution_time_in_hours NUMERIC(10, 2),
    created_at               TIMESTAMP          DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.nyc311_requests_daily
(
    unique_key               BIGINT PRIMARY KEY,
    created_date             TIMESTAMP NOT NULL,
    closed_date              TIMESTAMP NULL,
    agency                   TEXT,
    complaint_type           TEXT,
    descriptor               TEXT,
    community_board          TEXT,
    incident_zip             VARCHAR(10),
    location_type            TEXT,
    address_type             TEXT,
    city                     TEXT,
    borough                  TEXT,
    status                   TEXT,
    council_district         INTEGER,
    police_precinct          TEXT,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    is_closed                BOOLEAN   NOT NULL DEFAULT FALSE,
    resolution_time_in_hours NUMERIC(10, 2),
    created_at               TIMESTAMP          DEFAULT CURRENT_TIMESTAMP
);
