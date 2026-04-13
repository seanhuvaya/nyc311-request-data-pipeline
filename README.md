# NYC 311 Data Pipeline

This project includes a FastAPI backend and a Streamlit frontend for exploring NYC 311 data.

## Install Dependencies

Install project dependencies (including shadcn UI components for Streamlit):

```bash
uv sync
```

## Run the API

Start the FastAPI service:

```bash
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API endpoints used by the Streamlit app:
- `GET /api/v1/requests/`
- `GET /api/v1/requests/daily`
- `GET /api/v1/requests/by-complaint-type`

## Run the Streamlit App

In a separate terminal, run:

```bash
uv run streamlit run src/web/app.py
```

Run this command from the repository root so Streamlit discovers the `src/web/pages` folder correctly.

The app reads the API host from `API_BASE_URL`, defaulting to `http://localhost:8000`.
The main dashboard landing page shows live summary cards for each API endpoint, with key metrics and graceful fallback states.
The Streamlit pages use `streamlit-shadcn-ui` for shadcn-style cards, badges, and metric components.

Example with explicit API URL:

```bash
API_BASE_URL=http://localhost:8000 uv run streamlit run src/web/app.py
```

## Run Full Stack in Docker Compose

The compose stack includes:
- FastAPI (`http://localhost:8000`)
- Streamlit (`http://localhost:8501`)
- Airflow services (`airflow-init`, `airflow-apiserver`, `airflow-scheduler`, `airflow-dag-processor`)
- Postgres

Start everything:

```bash
docker compose up --build
```

Streamlit calls FastAPI over the compose network with:
- `API_BASE_URL=http://fastapi:8000`