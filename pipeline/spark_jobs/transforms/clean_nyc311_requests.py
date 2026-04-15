import logging

from pyspark.sql import DataFrame, Window, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType, IntegerType
from spark_jobs.session import get_spark_session

COLUMNS_TO_DROP = [
    "vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
    "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type",
    "agency_name", "incident_address", "street_name", "cross_street_1", "cross_street_2",
    "intersection_street_1", "intersection_street_2", "park_borough", "location",
    "x_coordinate_state_plane", "y_coordinate_state_plane", "open_data_channel_type",
    "park_facility_name", "landmark", "bbl", "resolution_description",
    "resolution_action_updated_date", "due_date", "taxi_company_borough"
]

logger = logging.getLogger(__name__)


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
                         F.coalesce(F.col("incident_zip"), F.first("incident_zip", ignorenulls=True).over(win_lat_long),
                                    F.first("incident_zip", ignorenulls=True).over(win_borough))) \
        .withColumn("address_type",
                    F.coalesce(F.col("address_type"), F.first("address_type", ignorenulls=True).over(win_complaint),
                               F.first("address_type", ignorenulls=True).over(win_agency), F.lit("UNKNOWN"))) \
        .withColumn("city",
                    F.coalesce(F.col("city"), F.first("city", ignorenulls=True).over(win_borough), F.lit("UNKNOWN"))) \
        .withColumn("location_type",
                    F.coalesce(F.col("location_type"), F.first("location_type", ignorenulls=True).over(win_complaint),
                               F.first("location_type", ignorenulls=True).over(win_descriptor), F.lit("UNKNOWN"))) \
        .withColumn("council_district",
                    F.coalesce(F.col("council_district"), F.first("council_district", ignorenulls=True).over(win_zip),
                               F.first("council_district", ignorenulls=True).over(win_cb)))


def impute_coordinates(df: DataFrame) -> DataFrame:
    logger.info(f"Imputing coordinates...")
    zip_centroids = df \
        .filter(F.col("incident_zip").isNotNull() & F.col("longitude").isNotNull() & F.col("latitude").isNotNull()) \
        .groupBy("incident_zip") \
        .agg(F.avg("latitude").alias("zip_latitude"), F.avg("longitude").alias("zip_longitude"))

    cb_centroids = df \
        .filter(F.col("community_board").isNotNull() & F.col("latitude").isNotNull() & F.col("longitude").isNotNull()) \
        .groupBy("community_board") \
        .agg(F.avg("latitude").alias("cb_latitude"), F.avg("longitude").alias("cb_longitude"))

    df = df \
        .alias("d") \
        .join(zip_centroids.alias("z"), on="incident_zip", how="left") \
        .join(cb_centroids.alias("c"), on="community_board", how="left") \
        .withColumn("latitude", F.coalesce(F.col("d.latitude"), F.col("z.zip_latitude"), F.col("c.cb_latitude"))) \
        .withColumn("longitude", F.coalesce(F.col("d.longitude"), F.col("z.zip_longitude"), F.col("c.cb_longitude")))

    return df.drop(*['zip_latitude', 'zip_longitude', 'cb_latitude', 'cb_longitude'])


def clean_nyc311_requests(df: DataFrame):
    logger.info("Casting columns to correct types")
    df = df \
        .withColumn("created_date", F.to_timestamp("created_date", "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
        .withColumn("closed_date", F.when(F.col("closed_date").isNotNull(),
                                          F.to_timestamp(F.col("closed_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS"))) \
        .withColumn("latitude", F.col("latitude").cast(FloatType())) \
        .withColumn("longitude", F.col("longitude").cast(FloatType())) \
        .withColumn("unique_key", F.col("unique_key").cast(IntegerType())) \
        .withColumn("incident_zip", F.col("incident_zip").cast(IntegerType()))

    df = df.drop(*COLUMNS_TO_DROP)
    logger.info(f"Dropped {len(COLUMNS_TO_DROP)} columns")

    df = impute_categorical_fields(df)
    return impute_coordinates(df)
