import logging

from pyspark.sql import SparkSession

from config import settings
from db import get_db_session
from models import ExtractMetadata
from models.extraction_metadata import ExtractionStatus
from validate import perform_validation

logger = logging.getLogger(__name__)

cols_to_drop = ["vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
                "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type", "agency_name",
                "incident_address", "street_name", "cross_street_1", "cross_street_2", "intersection_street_1",
                "intersection_street_2", "park_borough", "location", "x_coordinate_state_plane",
                "y_coordinate_state_plane", "open_data_channel_type", "park_facility_name", "landmark", "bbl"]


def transform_data():
    raw_data_csv_file_paths = []
    with (get_db_session() as session):
        extraction_metadata = session.query(ExtractMetadata).where(
            ExtractMetadata.status == ExtractionStatus.COMPLETED.value).all()
        latest_record_created_dates = [record.latest_record_created_date.strftime('%Y-%m-%d') for record in
                                       extraction_metadata]

        raw_data_csv_file_paths = [
            f"s3a://{settings.AWS_S3_BUCKET}/raw/date={date}/{settings.AWS_S3_RAW_DATA_PARQUET_FILENAME}"
            for date in latest_record_created_dates]

    root_raw_data_csv_file_paths = list(set(['/'.join(p.split('/')[:-1]) for p in raw_data_csv_file_paths]))
    print(root_raw_data_csv_file_paths)

    spark = SparkSession.builder \
        .appName("Read S3 File") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.4.1,org.apache.hadoop:hadoop-common:3.4.1") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    df = spark.read \
        .format("parquet") \
        .option("recursiveFileLookup", "true") \
        .option("pathGlobFilter", "*.parquet") \
        .load(root_raw_data_csv_file_paths)

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
