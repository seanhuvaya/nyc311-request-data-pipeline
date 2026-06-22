# NYC 311 Data Pipeline
![Live](https://img.shields.io/badge/Live%20Demo-Available-brightgreen)

🚀 API: https://api.nyc311.seanhuvaya.dev/docs

📊 Dashboard: https://nyc311.seanhuvaya.dev

## Overview

End-to-end data engineering pipeline that ingests NYC 311 service request data, transforms it through a medallion architecture, and exposes curated datasets through a REST API and analytics dashboard.

The pipeline pulls data from the [NYC Open Data API](https://data.cityofnewyork.us/resource/erm2-nwe9.csv), stores raw CSVs in MinIO (bronze), cleans and enriches them with Pandas (silver), and upserts records into a PostgreSQL gold schema that the API reads from.

## Architecture

![Architecture Diagram](./docs/NYC%20311%20Data%20Pipeline%20Architecture.png)

### Data Flow

```
NYC Open Data API (erm2-nwe9.csv)
      │
      ▼
[Airflow] ingest_nyc311_requests()
      │  Watermark-based, paginated extraction
      │  Watermark stored in {s3_key}/metadata.json after each run
      ▼
MinIO → bronze/daily/date={date} or bronze/historical
      │  Raw CSVs
      ▼
[Airflow] transform()
      │  clean.py: type casting, deduplication, null imputation
      │  enrich.py: is_closed flag, resolution_time_in_hours
      ▼
MinIO → silver/
      ▼
[Airflow] load()
      │  Upsert on unique_key; COALESCE handles late-arriving closures
      ▼
PostgreSQL gold schema → FastAPI → React Dashboard
```

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 3.x |
| Object Storage | MinIO (S3-compatible) |
| Transforms | Pandas |
| Database | PostgreSQL 16 |
| API | FastAPI + asyncpg + SQLAlchemy 2.0 |
| Frontend | React 19, Vite 7, Tailwind 4, Recharts, shadcn/ui |
| Package mgmt | `uv` (Python), `npm` (frontend) |
| Containerization | Docker Compose |
| CI/CD | GitHub Actions → SSH deploy to VPS |

## Project Structure

```
nyc311-request-data-pipeline/
├── pipeline/               # Airflow DAGs + ingestion/transform/load (Python/uv)
│   ├── dags/
│   │   ├── nyc_311_dag.py          # Daily and backfill DAGs
│   │   └── shared/tasks.py         # Airflow task wrappers
│   ├── nyc311/
│   │   ├── ingestion/
│   │   │   ├── api.py              # Paginated extraction from NYC Open Data API
│   │   │   └── ingest.py           # Watermark loading and ingestion orchestration
│   │   ├── jobs/
│   │   │   └── load.py             # Transform + upsert into PostgreSQL
│   │   ├── transforms/
│   │   │   ├── clean.py            # Type casting, deduplication, imputation
│   │   │   └── enrich.py           # Derived fields (is_closed, resolution time)
│   │   └── utils/
│   │       ├── config.py           # Pydantic settings (env-driven)
│   │       ├── db.py               # SQLAlchemy engine
│   │       ├── http.py             # HTTP session with retry
│   │       ├── log.py              # Logging setup
│   │       └── s3.py               # MinIO/S3 client and metadata helpers
│   ├── sql/                        # DB init DDL (00–11) and view definitions
│   └── tests/
├── backend/                # FastAPI REST API (Python/uv)
│   ├── routers/            # overview, borough, complaints, agency, backlog, health
│   ├── schema/             # Pydantic response models
│   └── services/           # DB query logic
├── frontend/               # React + Vite + Tailwind dashboard (npm)
│   └── src/
├── docker-compose.yml          # Production (no host ports; uses proxy network)
├── docker-compose-dev.yml      # Local dev (publishes all ports to host)
└── .env                        # Local env vars
```

## Database Schema

Star schema with one fact table, four dimension tables, and eight analytical views — all in the `gold` PostgreSQL schema.

```mermaid
erDiagram
    nyc311_requests_daily {
        BIGINT unique_key PK
        INT date_id FK
        INT agency_id FK
        INT complaint_type_id FK
        INT location_id FK
        TIMESTAMP created_date
        TIMESTAMP closed_date
        DOUBLE_PRECISION latitude
        DOUBLE_PRECISION longitude
        TEXT location_type
        TEXT address_type
        TEXT status
        BOOLEAN is_closed
        NUMERIC resolution_time_in_hours
        TIMESTAMP created_at
    }
    dim_date {
        INT date_id PK
        DATE full_date
        INT year
        INT quarter
        INT month
        TEXT month_name
        INT day
        INT day_of_week
        TEXT day_name
    }
    dim_agency {
        INT agency_id PK
        TEXT agency_code
    }
    dim_complaint_type {
        INT complaint_type_id PK
        TEXT complaint_type
        TEXT descriptor
    }
    dim_location {
        INT location_id PK
        TEXT borough
        TEXT community_board
        VARCHAR incident_zip
        TEXT city
        INT council_district
        TEXT police_precinct
    }

    nyc311_requests_daily }o--|| dim_date : "date_id"
    nyc311_requests_daily }o--|| dim_agency : "agency_id"
    nyc311_requests_daily }o--|| dim_complaint_type : "complaint_type_id"
    nyc311_requests_daily }o--|| dim_location : "location_id"
```

### Analytical Views

| View | Description |
|---|---|
| `v_requests_daily` | Daily aggregates: count, closed %, avg/median/p90 resolution hours |
| `v_requests_7d` | Same metrics over the last 7 days (single row) |
| `v_requests_30d` | Same metrics over the last 30 days (single row) |
| `v_requests_by_borough` | Metrics grouped by borough |
| `v_requests_by_complaint_type` | Metrics grouped by complaint type |
| `v_requests_by_agency` | Metrics + open backlog grouped by agency |
| `v_requests_by_day_of_week` | Metrics grouped by day of week |
| `v_backlog_aging` | Open requests bucketed by age: <7d, 7–30d, 30–90d, >90d |

SQL init scripts in `pipeline/sql/` (files `00`–`11`) run automatically when the postgres container starts.

## DAGs

**`nyc_311_daily_ingest`** — nightly at midnight ET. Reads the watermark from the previous run's S3 metadata file and fetches all records created or updated since then.

**`nyc_311_backfill`** — manually triggered. Accepts a `logical_date` and ingests all records from that date forward into `bronze/historical`.

Both follow the same three-task pattern: `ingest → transform → load`.

### Ingestion Design

Incremental extraction uses a watermark stored in `{s3_key}/metadata.json` after each successful run. The API query filters on both `created_date` and `resolution_action_updated_date` so late-arriving closures (records created before the watermark but closed after it) are always captured. The effective watermark advances to the maximum of the two date columns across the entire batch.

## Running Locally (Full Stack)

Use `docker-compose-dev.yml` — it publishes all ports to the host.

```bash
# 1. Set credentials (MinIO creds are required; DB defaults work)
cp .env.example .env   # or edit the existing .env

# 2. Spin up everything
docker compose -f docker-compose-dev.yml up -d --build
```

Services after startup:

| Service | URL | Default credentials |
|---|---|---|
| Airflow UI | http://localhost:8080 | admin / pass1234 |
| MinIO Console | http://localhost:9001 | changemeuser / changemepass |
| Backend API (Swagger) | http://localhost:8000/docs | — |
| Frontend Dashboard | http://localhost:5173 | — |
| PostgreSQL | localhost:5432 | postgres / postgres (db: nyc311) |

> `airflow-init` must complete before the API server and scheduler start. Docker Compose health-checks handle the ordering automatically.

## Running Individual Services

### Frontend

```bash
cd frontend
npm install                   # first time only
cp .env.example .env          # set VITE_API_URL=http://localhost:8000
npm run dev                   # http://localhost:5173
```

Other scripts:

```bash
npm run typecheck   # TypeScript type check
npm run lint        # ESLint
npm run format      # Prettier
npm run build       # Production build (bakes VITE_API_URL at build time)
```

### Backend API

```bash
# Start only postgres
docker compose -f docker-compose-dev.yml up -d postgres

cd backend
uv run uvicorn main:app --reload --port 8000
```

Required env vars (set in `backend/.env` or shell):

- `DATABASE_URL` — e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/nyc311`
- `CORS_ALLOWED_ORIGINS` — comma-separated, defaults to `http://localhost:5173`

### Pipeline Tests

```bash
# Start pipeline dependencies
docker compose -f docker-compose-dev.yml up -d postgres minio minio-init

cd pipeline
uv run pytest
```

## Environment Variables

Root `.env` is consumed by Docker Compose. Key vars:

| Variable | Default | Notes |
|---|---|---|
| `DB_HOST` | `postgres` | Use `localhost` when running backend outside Docker |
| `DB_PORT` | `5432` | |
| `DB_USER` | `postgres` | |
| `DB_PASSWORD` | `postgres` | |
| `DB_NAME` | `nyc311` | |
| `AWS_ACCESS_KEY_ID` | `changemeuser` | MinIO root user |
| `AWS_SECRET_ACCESS_KEY` | `changemepass` | MinIO root password |
| `S3_BUCKET_NAME` | `nyc311` | |
| `S3_ENDPOINT_URL` | `http://minio:9000` | Defaults to in-Docker MinIO |
| `AIRFLOW_ADMIN_USER` | `admin` | |
| `AIRFLOW_ADMIN_PASSWORD` | `pass1234` | Change for real deployments |
| `AIRFLOW_JWT_SECRET` | `supersecret...` | Change for real deployments |
| `VITE_API_URL` | `http://localhost:8000` | Baked at frontend build time — not a runtime var |

## API Routes

All analytics routes are prefixed `/api/v1`:

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/overview` | 7d/30d aggregate metrics |
| GET | `/api/v1/borough` | Metrics by borough |
| GET | `/api/v1/complaints` | Metrics by complaint type |
| GET | `/api/v1/agency` | Metrics by agency |
| GET | `/api/v1/backlog` | Open request aging buckets |

Full interactive docs available at `/docs` (Swagger UI).

## Deployment

Pushes to `main` trigger `.github/workflows/deploy.yml`, which SSH's into the VPS, pulls the latest code, and runs:

```bash
docker compose down --remove-orphans
docker compose up -d --build --force-recreate
```

The production `docker-compose.yml` uses an external `proxy-net` Docker network (Nginx Proxy Manager) — the API and frontend containers are only exposed to that network, not directly to the host.

Required GitHub secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_PORT`.
