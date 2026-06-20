import logging
from io import StringIO
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from nyc311.utils.config import settings
from nyc311.utils.db import get_db_engine
from nyc311.utils.s3 import make_s3_client
from nyc311.transforms.clean import clean_nyc311_requests
from nyc311.transforms.enrich import enrich_nyc311_requests

logger = logging.getLogger(__name__)

_FACT_TABLE = "gold.nyc311_requests_daily"

_FACT_COLUMNS = [
    "unique_key", "created_date", "closed_date", "agency", "complaint_type",
    "descriptor", "community_board", "incident_zip", "location_type", "address_type",
    "city", "borough", "status", "council_district", "police_precinct",
    "latitude", "longitude", "is_closed", "resolution_time_in_hours",
]

_UPSERT_SQL = f"""
    INSERT INTO {_FACT_TABLE} ({", ".join(_FACT_COLUMNS)})
    VALUES ({", ".join(f":{c}" for c in _FACT_COLUMNS)})
    ON CONFLICT (unique_key) DO UPDATE SET
        closed_date              = COALESCE(EXCLUDED.closed_date, nyc311_requests_daily.closed_date),
        status                   = EXCLUDED.status,
        is_closed                = EXCLUDED.is_closed,
        resolution_time_in_hours = COALESCE(EXCLUDED.resolution_time_in_hours, nyc311_requests_daily.resolution_time_in_hours)
"""

_VIEWS_FILE = Path(__file__).parent.parent.parent / "sql" / "06_create_views.sql"


def transform_and_load(s3_key: str) -> int:
    s3 = make_s3_client()
    engine = get_db_engine()

    _ensure_views(engine)

    paginator = s3.get_paginator("list_objects_v2")
    total = 0

    for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix=s3_key):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".csv"):
                continue

            logger.info(f"Processing chunk | key={key}")
            body = s3.get_object(Bucket=settings.s3_bucket_name, Key=key)["Body"].read().decode()
            df = pd.read_csv(StringIO(body))
            df = clean_nyc311_requests(df)
            df = enrich_nyc311_requests(df)
            rows = _upsert(df, engine)
            total += rows
            logger.info(f"Upserted chunk | key={key}, rows={rows}")

    logger.info(f"Load complete | s3_key={s3_key}, total_rows={total}")
    return total


def _upsert(df: pd.DataFrame, engine) -> int:
    present = [c for c in _FACT_COLUMNS if c in df.columns]
    records = [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df[present].to_dict(orient="records")
    ]
    with engine.begin() as conn:
        result = conn.execute(text(_UPSERT_SQL), records)
    return result.rowcount


def _ensure_views(engine) -> None:
    statements = [s.strip() for s in _VIEWS_FILE.read_text().split(";") if s.strip()]
    with engine.begin() as conn:
        for sql in statements:
            conn.execute(text(sql))
