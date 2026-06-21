import logging
from io import BytesIO
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from nyc311.utils.config import settings
from nyc311.utils.db import get_db_engine
from nyc311.utils.s3 import make_s3_client

logger = logging.getLogger(__name__)

_FACT_TABLE = "gold.nyc311_requests_daily"

_FACT_COLUMNS = [
    "unique_key", "date_id", "agency_id", "complaint_type_id", "location_id",
    "created_date", "closed_date", "latitude", "longitude",
    "location_type", "address_type", "status", "is_closed", "resolution_time_in_hours",
]

_UPSERT_FACT_SQL = f"""
    INSERT INTO {_FACT_TABLE} ({", ".join(_FACT_COLUMNS)})
    VALUES ({", ".join(f":{c}" for c in _FACT_COLUMNS)})
    ON CONFLICT (unique_key) DO UPDATE SET
        closed_date              = COALESCE(EXCLUDED.closed_date, nyc311_requests_daily.closed_date),
        status                   = EXCLUDED.status,
        is_closed                = EXCLUDED.is_closed,
        resolution_time_in_hours = COALESCE(EXCLUDED.resolution_time_in_hours, nyc311_requests_daily.resolution_time_in_hours)
"""

_SQL_DIR = Path(__file__).parent.parent.parent / "sql"


def load(silver_key: str) -> int:
    s3 = make_s3_client()
    engine = get_db_engine()

    body = s3.get_object(Bucket=settings.s3_bucket_name, Key=silver_key)["Body"].read()
    df = pd.read_parquet(BytesIO(body))
    logger.info(f"Read Parquet from silver | silver_key={silver_key}, rows={len(df)}")

    with engine.begin() as conn:
        date_map = _upsert_dim_date(df, conn)
        agency_map = _upsert_dim_agency(df, conn)
        ct_map = _upsert_dim_complaint_type(df, conn)
        loc_map = _upsert_dim_location(df, conn)

    df["date_id"] = pd.to_datetime(df["created_date"]).dt.date.map(date_map)
    df["agency_id"] = df["agency"].map(agency_map)
    df["complaint_type_id"] = [
        ct_map.get((_norm_str(ct), _norm_str(desc)))
        for ct, desc in zip(df["complaint_type"], df.get("descriptor", pd.Series([""] * len(df))))
    ]
    df["location_id"] = [
        loc_map.get((
            _norm_str(borough, "UNKNOWN"),
            _norm_str(cb),
            _norm_str(zip_),
            _norm_str(city, "UNKNOWN"),
            _norm_int(district),
            _norm_str(precinct),
        ))
        for borough, cb, zip_, city, district, precinct in zip(
            df.get("borough", pd.Series([None] * len(df))),
            df.get("community_board", pd.Series([None] * len(df))),
            df.get("incident_zip", pd.Series([None] * len(df))),
            df.get("city", pd.Series([None] * len(df))),
            df.get("council_district", pd.Series([None] * len(df))),
            df.get("police_precinct", pd.Series([None] * len(df))),
        )
    ]

    rows = _upsert_facts(df, engine)
    _ensure_views(engine)
    logger.info(f"Load complete | silver_key={silver_key}, rows={rows}")
    return rows


def _norm_str(val, default: str = "") -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return str(val)


def _norm_int(val, default: int = -1) -> int:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return int(val)


def _upsert_dim_date(df: pd.DataFrame, conn) -> dict:
    dates = pd.to_datetime(df["created_date"]).dt.date.dropna().unique()
    if len(dates) == 0:
        return {}

    rows = [
        {
            "full_date": d,
            "year": d.year,
            "quarter": (d.month - 1) // 3 + 1,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "day": d.day,
            "day_of_week": d.isoweekday(),
            "day_name": d.strftime("%A"),
        }
        for d in dates
    ]
    conn.execute(
        text("""
            INSERT INTO gold.dim_date (full_date, year, quarter, month, month_name, day, day_of_week, day_name)
            VALUES (:full_date, :year, :quarter, :month, :month_name, :day, :day_of_week, :day_name)
            ON CONFLICT (full_date) DO NOTHING
        """),
        rows,
    )
    result = conn.execute(
        text("SELECT date_id, full_date FROM gold.dim_date WHERE full_date = ANY(:dates)"),
        {"dates": [str(d) for d in dates]},
    )
    return {row.full_date: row.date_id for row in result}


def _upsert_dim_agency(df: pd.DataFrame, conn) -> dict:
    codes = df["agency"].dropna().unique().tolist()
    if not codes:
        return {}

    conn.execute(
        text("INSERT INTO gold.dim_agency (agency_code) VALUES (:agency_code) ON CONFLICT (agency_code) DO NOTHING"),
        [{"agency_code": c} for c in codes],
    )
    result = conn.execute(
        text("SELECT agency_id, agency_code FROM gold.dim_agency WHERE agency_code = ANY(:codes)"),
        {"codes": codes},
    )
    return {row.agency_code: row.agency_id for row in result}


def _upsert_dim_complaint_type(df: pd.DataFrame, conn) -> dict:
    pairs = (
        df[["complaint_type", "descriptor"]]
        .fillna({"complaint_type": "", "descriptor": ""})
        .drop_duplicates()
        .to_dict(orient="records")
    )
    if not pairs:
        return {}

    conn.execute(
        text("""
            INSERT INTO gold.dim_complaint_type (complaint_type, descriptor)
            VALUES (:complaint_type, :descriptor)
            ON CONFLICT (complaint_type, descriptor) DO NOTHING
        """),
        pairs,
    )
    result = conn.execute(
        text("SELECT complaint_type_id, complaint_type, descriptor FROM gold.dim_complaint_type")
    )
    return {(row.complaint_type, row.descriptor): row.complaint_type_id for row in result}


def _upsert_dim_location(df: pd.DataFrame, conn) -> dict:
    loc_cols = ["borough", "community_board", "incident_zip", "city", "council_district", "police_precinct"]
    present = {c: df[c] if c in df.columns else pd.Series([None] * len(df)) for c in loc_cols}
    loc_df = pd.DataFrame(present).drop_duplicates()

    rows = [
        {
            "borough": _norm_str(r.get("borough"), "UNKNOWN"),
            "community_board": _norm_str(r.get("community_board")),
            "incident_zip": _norm_str(r.get("incident_zip")),
            "city": _norm_str(r.get("city"), "UNKNOWN"),
            "council_district": _norm_int(r.get("council_district")),
            "police_precinct": _norm_str(r.get("police_precinct")),
        }
        for r in loc_df.to_dict(orient="records")
    ]

    conn.execute(
        text("""
            INSERT INTO gold.dim_location (borough, community_board, incident_zip, city, council_district, police_precinct)
            VALUES (:borough, :community_board, :incident_zip, :city, :council_district, :police_precinct)
            ON CONFLICT (borough, community_board, incident_zip, city, council_district, police_precinct) DO NOTHING
        """),
        rows,
    )
    result = conn.execute(
        text("SELECT location_id, borough, community_board, incident_zip, city, council_district, police_precinct FROM gold.dim_location")
    )
    return {
        (row.borough, row.community_board, row.incident_zip, row.city, row.council_district, row.police_precinct): row.location_id
        for row in result
    }


def _upsert_facts(df: pd.DataFrame, engine) -> int:
    present = [c for c in _FACT_COLUMNS if c in df.columns]
    records = [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df[present].to_dict(orient="records")
    ]
    with engine.begin() as conn:
        result = conn.execute(text(_UPSERT_FACT_SQL), records)
    return result.rowcount


def _ensure_views(engine) -> None:
    for sql_file in sorted(_SQL_DIR.glob("*_create_v_*.sql")):
        statements = [s.strip() for s in sql_file.read_text().split(";") if s.strip()]
        with engine.begin() as conn:
            for sql in statements:
                conn.execute(text(sql))
