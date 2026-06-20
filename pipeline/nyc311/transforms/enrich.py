import pandas as pd


def enrich_nyc311_requests(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_closed"] = df["closed_date"].notna()
    df["resolution_time_in_hours"] = (
        (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600
    ).where(df["closed_date"].notna())
    return df
