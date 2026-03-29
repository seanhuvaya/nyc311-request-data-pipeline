import logging

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import coalesce, col, first, lit, to_timestamp, avg
from pyspark.sql.types import FloatType, IntegerType

COLUMNS_TO_DROP = [
    "vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
    "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type",
    "agency_name", "incident_address", "street_name", "cross_street_1", "cross_street_2",
    "intersection_street_1", "intersection_street_2", "park_borough", "location",
    "x_coordinate_state_plane", "y_coordinate_state_plane", "open_data_channel_type",
    "park_facility_name", "landmark", "bbl", "resolution_description",
    "resolution_action_updated_date"
]

logger = logging.getLogger(__name__)


def cast_column_types(df: DataFrame) -> DataFrame:
    logger.info(f"Casting column types...")
    return df \
        .withColumn("created_date", to_timestamp("created_date", "yyyy-MM-dd HH:mm:ss")) \
        .withColumn("latitude", col("latitude").cast(FloatType())) \
        .withColumn("longitude", col("longitude").cast(FloatType())) \
        .withColumn("unique_key", col("unique_key").cast(IntegerType())) \
        .withColumn("incident_zip", col("incident_zip").cast(IntegerType()))


def drop_irrelevant_columns(df: DataFrame) -> DataFrame:
    logger.info(f"Dropping irrelevant columns: {COLUMNS_TO_DROP}")
    return df.drop(*COLUMNS_TO_DROP)


def impute_categorical_fields(df: DataFrame) -> DataFrame:
    logger.info(f"Imputing categorical fields...")
    win_lat_long = Window.partitionBy("latitude", "longitude")
    win_borough = Window.partitionBy("borough")
    win_complaint = Window.partitionBy("complaint_type")
    win_agency = Window.partitionBy("agency")
    win_descriptor = Window.partitionBy("descriptor")
    win_zip = Window.partitionBy("incident_zip")
    win_cb = Window.partitionBy("community_board")

    return df.withColumn("incident_zip",
                         coalesce(col("incident_zip"), first("incident_zip", ignorenulls=True).over(win_lat_long),
                                  first("incident_zip", ignorenulls=True).over(win_borough))) \
        .withColumn("address_type",
                    coalesce(col("address_type"), first("address_type", ignorenulls=True).over(win_complaint),
                             first("address_type", ignorenulls=True).over(win_agency), lit("UNKNOWN"))) \
        .withColumn("city", coalesce(col("city"), first("city", ignorenulls=True).over(win_borough), lit("UNKNOWN"))) \
        .withColumn("location_type",
                    coalesce(col("location_type"), first("location_type", ignorenulls=True).over(win_complaint),
                             first("location_type", ignorenulls=True).over(win_descriptor), lit("UNKNOWN"))) \
        .withColumn("council_district",
                    coalesce(col("council_district"), first("council_district", ignorenulls=True).over(win_zip),
                             first("council_district", ignorenulls=True).over(win_cb)))


def impute_coordinates(df: DataFrame) -> DataFrame:
    logger.info(f"Imputing coordinates...")
    zip_centroids = df \
        .filter(col("incident_zip").isNotNull() & col("longitude").isNotNull() & col("latitude").isNotNull()) \
        .groupBy("incident_zip") \
        .agg(avg("latitude").alias("zip_latitude"), avg("longitude").alias("zip_longitude"))

    cb_centroids = df \
        .filter(col("community_board").isNotNull() & col("latitude").isNotNull() & col("longitude").isNotNull()) \
        .groupBy("community_board") \
        .agg(avg("latitude").alias("cb_latitude"), avg("longitude").alias("cb_longitude"))

    return df \
        .alias("d") \
        .join(zip_centroids.alias("z"), on="incident_zip", how="left") \
        .join(cb_centroids.alias("c"), on="community_board", how="left") \
        .withColumn("latitude", coalesce(col("d.latitude"), col("z.zip_latitude"), col("c.cb_latitude"))) \
        .withColumn("longitude", coalesce(col("d.longitude"), col("z.zip_longitude"), col("c.cb_longitude")))
