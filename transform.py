import logging

from dotenv import load_dotenv
from pyspark.sql import SparkSession

from validate import perform_validation

load_dotenv()

logger = logging.getLogger(__name__)

cols_to_drop = ["vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
                "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type", "agency_name",
                "incident_address", "street_name", "cross_street_1", "cross_street_2", "intersection_street_1",
                "intersection_street_2", "park_borough", "location", "x_coordinate_state_plane",
                "y_coordinate_state_plane", "open_data_channel_type", "park_facility_name", "landmark", "bbl"]


def transform_data():
    spark = SparkSession.builder \
        .appName("Read S3 File") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.4.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    s3_path = "s3a://nyc311-requests-data/raw/nyc311-requests-data_2026-03-21_02:24:50.csv"

    df = spark.read.csv(s3_path, header=True, inferSchema=True)

    df_clean = df.drop(*cols_to_drop)
    logger.info(f"Dropped {len(cols_to_drop)} columns.")

    df_pandas = df_clean.toPandas()

    spark.stop()

    return df_pandas

if __name__ == "__main__":
    from logger import setup_logging
    setup_logging()
    df_cleaned = transform_data()
    perform_validation(df_cleaned, "transform")
