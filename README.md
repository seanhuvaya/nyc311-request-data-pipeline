# NYC 311 Data Pipeline
![Live](https://img.shields.io/badge/Live%20Demo-Available-brightgreen)

🚀 API: https://api.nyc311.seanhuvaya.dev/docs

📊 Dashboard: https://nyc311.seanhuvaya.dev

## Overview
End-to-end data engineering pipeline that ingests NYC 311 service request data, transforms it through a medallion architecture, and exposes curated datasets through a REST API and analytics dashboard.

The pipeline pulls data from the [NYC Open Data API](https://data.cityofnewyork.us/resource/erm2-nwe9.csv), stores raw CSVs in object storage (bronze), cleans and enriches them with Pandas, and upserts records into a PostgreSQL gold table that the API reads from.

## Architecture
![Architecture Diagram](./docs/NYC%20311%20Data%20Pipeline%20Architecture.png)

### Data Flow

```
NYC Open Data API
      │
      ▼
[Airflow] Ingestion
      │  Watermark-based, paginated extraction
      │  OR filter on created_date + resolution_action_updated_date
      ▼
MinIO (Bronze)
      │  Raw CSVs partitioned by run
      ▼
[Airflow] Transform & Load
      │  Clean: type casting, deduplication, imputation
      │  Enrich: is_closed flag, resolution_time_in_hours
      ▼
PostgreSQL (Gold)
      │  Upsert on unique_key; late-arriving closures handled via COALESCE
      ▼
FastAPI → Dashboard
```

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 3.x |
| Object Storage | MinIO (S3-compatible) |
| Transforms | Pandas |
| Database | PostgreSQL 16 |
| Serving | FastAPI |
| Frontend | Vite / React |
| Containerization | Docker Compose |

## Project Structure

```
pipeline/
├── dags/
│   ├── nyc_311_dag.py          # Daily and backfill DAGs
│   └── shared/tasks.py         # Airflow task wrappers
├── nyc311/
│   ├── ingestion/
│   │   ├── api.py              # Paginated extraction from NYC Open Data API
│   │   └── ingest.py           # Watermark loading and ingestion orchestration
│   ├── jobs/
│   │   └── load.py             # Transform + upsert into PostgreSQL
│   ├── transforms/
│   │   ├── clean.py            # Type casting, deduplication, imputation
│   │   └── enrich.py           # Derived fields (is_closed, resolution time)
│   └── utils/
│       ├── config.py           # Pydantic settings (env-driven)
│       ├── db.py               # SQLAlchemy engine
│       ├── http.py             # HTTP session with retry
│       ├── log.py              # Logging setup
│       └── s3.py               # MinIO/S3 client and metadata helpers
├── sql/                        # Database init and view DDL
└── tests/
    └── ingestion/test_api.py
```

## DAGs

**`nyc_311_daily_ingest`** — runs nightly at midnight ET. Loads the watermark from the previous run's S3 metadata file and fetches all records created or updated since then.

**`nyc_311_backfill`** — triggered manually. Accepts a `logical_date` and ingests all records from that date forward into `bronze/historical`.

## Ingestion Design

Incremental extraction uses a watermark stored in `{s3_key}/metadata.json` after each successful run. The API query filters on both `created_date` and `resolution_action_updated_date` so late-arriving closures (records created before the watermark but closed after it) are always captured. The effective watermark advances to the maximum of the two date columns across the entire batch.

## Running Locally

```bash
cp .env.example .env   # fill in credentials
docker compose up -d
```

Services:
- Airflow UI: http://localhost:8080
- MinIO Console: http://localhost:9001
- Backend API docs: http://localhost:8000/docs

## Running Tests

```bash
cd pipeline
uv run pytest
```
