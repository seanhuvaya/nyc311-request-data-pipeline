import logging

import pandas as pd

logger = logging.getLogger(__name__)


def enrich_nyc311_requests(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_closed"] = df["closed_date"].notna()
    df["resolution_time_in_hours"] = (
        (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600
    ).where(df["closed_date"].notna())

    _log_imputation_stats(df)
    df = df.drop(columns=["_incident_zip_imputed"], errors="ignore")
    return df


def _log_imputation_stats(df: pd.DataFrame) -> None:
    if "_incident_zip_imputed" not in df.columns:
        return
    total = len(df)
    imputed = int(df["_incident_zip_imputed"].sum())
    still_null = int(df["incident_zip"].isna().sum())
    originally_null = imputed + still_null
    logger.info(
        f"incident_zip imputation | total={total}, "
        f"originally_null={originally_null} ({100 * originally_null / total:.1f}%), "
        f"filled={imputed} ({100 * imputed / total:.1f}%), "
        f"still_null={still_null} ({100 * still_null / total:.1f}%)"
    )
