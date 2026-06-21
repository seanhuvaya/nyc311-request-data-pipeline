CREATE TABLE IF NOT EXISTS gold.dim_date
(
    date_id     SERIAL PRIMARY KEY,
    full_date   DATE NOT NULL UNIQUE,
    year        INT  NOT NULL,
    quarter     INT  NOT NULL,
    month       INT  NOT NULL,
    month_name  TEXT NOT NULL,
    day         INT  NOT NULL,
    day_of_week INT  NOT NULL,
    day_name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_agency
(
    agency_id   SERIAL PRIMARY KEY,
    agency_code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.dim_complaint_type
(
    complaint_type_id SERIAL PRIMARY KEY,
    complaint_type    TEXT NOT NULL,
    descriptor        TEXT NOT NULL DEFAULT '',
    UNIQUE (complaint_type, descriptor)
);

CREATE TABLE IF NOT EXISTS gold.dim_location
(
    location_id      SERIAL PRIMARY KEY,
    borough          TEXT         NOT NULL DEFAULT 'UNKNOWN',
    community_board  TEXT         NOT NULL DEFAULT '',
    incident_zip     VARCHAR(10)  NOT NULL DEFAULT '',
    city             TEXT         NOT NULL DEFAULT 'UNKNOWN',
    council_district INTEGER      NOT NULL DEFAULT -1,
    police_precinct  TEXT         NOT NULL DEFAULT '',
    UNIQUE (borough, community_board, incident_zip, city, council_district, police_precinct)
);
