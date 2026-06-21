import logging

import pandas as pd

COLUMNS_TO_DROP = [
    "vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
    "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type",
    "agency_name", "incident_address", "street_name", "cross_street_1", "cross_street_2",
    "intersection_street_1", "intersection_street_2", "park_borough", "location",
    "x_coordinate_state_plane", "y_coordinate_state_plane", "open_data_channel_type",
    "park_facility_name", "landmark", "bbl", "resolution_description",
    "resolution_action_updated_date", "due_date", "taxi_company_borough",
]

logger = logging.getLogger(__name__)


def clean_nyc311_requests(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    logger.info("Casting columns to correct types")
    df["created_date"] = pd.to_datetime(df["created_date"])
    df["closed_date"] = pd.to_datetime(df.get("closed_date"))
    df["latitude"] = pd.to_numeric(df.get("latitude"), errors="coerce")
    df["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")
    df["unique_key"] = pd.to_numeric(df["unique_key"], errors="coerce").astype("Int64")
    df["incident_zip"] = pd.to_numeric(df.get("incident_zip"), errors="coerce").astype("Int64")
    df["council_district"] = pd.to_numeric(df.get("council_district"), errors="coerce").astype("Int64")

    drop = [c for c in COLUMNS_TO_DROP if c in df.columns]
    df = df.drop(columns=drop)
    logger.info(f"Dropped {len(drop)} columns")

    df = df.drop_duplicates(subset=["unique_key"])

    df = _impute_categorical_fields(df)
    df = _impute_coordinates(df)

    return df


def _fill_from_group(df: pd.DataFrame, col: str, group_cols: list[str]) -> pd.Series:
    """Fill nulls in col with the first non-null value from each group."""
    valid_cols = [c for c in group_cols if c in df.columns]
    if not valid_cols or df[col].notna().all():
        return df[col]
    lookup = (
        df.dropna(subset=[col] + valid_cols)
        .groupby(valid_cols, as_index=False)[col]
        .first()
        .rename(columns={col: "_fill"})
    )
    filled = df[valid_cols].merge(lookup, on=valid_cols, how="left")["_fill"]
    return df[col].fillna(filled.set_axis(df.index))


def _impute_categorical_fields(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Imputing categorical fields")
    zip_null_before = df["incident_zip"].isna()
    df["incident_zip"] = _fill_from_group(df, "incident_zip", ["latitude", "longitude"])
    df["incident_zip"] = _fill_from_group(df, "incident_zip", ["borough"])
    df["_incident_zip_imputed"] = zip_null_before & df["incident_zip"].notna()

    df["address_type"] = _fill_from_group(df, "address_type", ["complaint_type"])
    df["address_type"] = _fill_from_group(df, "address_type", ["agency"])
    df["address_type"] = df["address_type"].fillna("UNKNOWN")

    df["city"] = _fill_from_group(df, "city", ["borough"])
    df["city"] = df["city"].fillna("UNKNOWN")

    df["location_type"] = _fill_from_group(df, "location_type", ["complaint_type"])
    df["location_type"] = _fill_from_group(df, "location_type", ["descriptor"])
    df["location_type"] = df["location_type"].fillna("UNKNOWN")

    df["council_district"] = _fill_from_group(df, "council_district", ["incident_zip"])
    df["council_district"] = _fill_from_group(df, "council_district", ["community_board"])

    return df


def _impute_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Imputing coordinates")
    valid = df.dropna(subset=["latitude", "longitude"])

    zip_centroids = (
        valid.dropna(subset=["incident_zip"])
        .groupby("incident_zip")[["latitude", "longitude"]]
        .mean()
        .rename(columns={"latitude": "_zip_lat", "longitude": "_zip_lon"})
    )
    cb_centroids = (
        valid.dropna(subset=["community_board"])
        .groupby("community_board")[["latitude", "longitude"]]
        .mean()
        .rename(columns={"latitude": "_cb_lat", "longitude": "_cb_lon"})
    )

    df = df.join(zip_centroids, on="incident_zip")
    df = df.join(cb_centroids, on="community_board")
    df["latitude"] = df["latitude"].fillna(df["_zip_lat"]).fillna(df["_cb_lat"])
    df["longitude"] = df["longitude"].fillna(df["_zip_lon"]).fillna(df["_cb_lon"])
    return df.drop(columns=["_zip_lat", "_zip_lon", "_cb_lat", "_cb_lon"])
