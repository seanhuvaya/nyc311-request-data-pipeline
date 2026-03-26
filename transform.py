import logging

from pyspark.sql import SparkSession, Window, DataFrame
from pyspark.sql.functions import when, col, first, to_timestamp, lit, avg
from pyspark.sql.types import FloatType, IntegerType, DoubleType

from config import settings
from db import get_db_session
from models import ExtractMetadata
from models.extraction_metadata import ExtractionStatus
from utils import upload_data_to_s3
from validate import perform_validation

logger = logging.getLogger(__name__)


def handle_missing_values(df: DataFrame) -> DataFrame:
    cols_to_drop = [
        "vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
        "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type", "agency_name",
        "incident_address", "street_name", "cross_street_1", "cross_street_2", "intersection_street_1",
        "intersection_street_2", "park_borough", "location", "x_coordinate_state_plane",
        "y_coordinate_state_plane", "open_data_channel_type", "park_facility_name", "landmark", "bbl",
        "resolution_description", "resolution_action_updated_date"
    ]

    df_clean = df.drop(*cols_to_drop)
    logger.info(f"Dropped {len(cols_to_drop)} columns.")

    # Keep business meaning of closed_date nulls
    df_with_closed_flag = df_clean.withColumn(
        "is_closed",
        when(col("closed_date").isNotNull(), True).otherwise(False)
    )

    df_with_resolution_time = df_with_closed_flag.withColumn(
        "resolution_time",
        when(
            col("closed_date").isNotNull(),
            (col("closed_date").cast("long") - col("created_date").cast("long")) / 3600.0
        ).otherwise(lit(None).cast("double"))
    )

    # -----------------------------
    # Impute easier categorical cols
    # -----------------------------
    latitude_longitude_window = Window.partitionBy("latitude", "longitude")
    borough_window = Window.partitionBy("borough")
    complaint_type_window = Window.partitionBy("complaint_type")
    agency_window = Window.partitionBy("agency")
    descriptor_window = Window.partitionBy("descriptor")
    zip_window = Window.partitionBy("incident_zip")
    community_board_window = Window.partitionBy("community_board")

    df_incident_zip_filled = (
        df_with_resolution_time
        .withColumn(
            "incident_zip",
            when(
                col("incident_zip").isNotNull(),
                col("incident_zip")
            ).otherwise(first("incident_zip", ignorenulls=True).over(latitude_longitude_window))
        )
        .withColumn(
            "incident_zip",
            when(
                col("incident_zip").isNotNull(),
                col("incident_zip")
            ).otherwise(first("incident_zip", ignorenulls=True).over(borough_window))
        )
    )

    df_address_type_filled = (
        df_incident_zip_filled
        .withColumn(
            "address_type",
            when(
                col("address_type").isNotNull(),
                col("address_type")
            ).otherwise(first("address_type", ignorenulls=True).over(complaint_type_window))
        )
        .withColumn(
            "address_type",
            when(
                col("address_type").isNotNull(),
                col("address_type")
            ).otherwise(first("address_type", ignorenulls=True).over(agency_window))
        )
        .withColumn(
            "address_type",
            when(col("address_type").isNotNull(), col("address_type")).otherwise(lit("UNKNOWN"))
        )
    )

    df_city_filled = (
        df_address_type_filled
        .withColumn(
            "city",
            when(
                col("city").isNotNull(),
                col("city")
            ).otherwise(first("city", ignorenulls=True).over(borough_window))
        )
        .withColumn(
            "city",
            when(col("city").isNotNull(), col("city")).otherwise(lit("UNKNOWN"))
        )
    )

    df_with_location_type_filled = (
        df_city_filled
        .withColumn(
            "location_type",
            when(
                col("location_type").isNotNull(),
                col("location_type")
            ).otherwise(first("location_type", ignorenulls=True).over(complaint_type_window))
        )
        .withColumn(
            "location_type",
            when(
                col("location_type").isNotNull(),
                col("location_type")
            ).otherwise(first("location_type", ignorenulls=True).over(descriptor_window))
        )
        .withColumn(
            "location_type",
            when(col("location_type").isNotNull(), col("location_type")).otherwise(lit("UNKNOWN"))
        )
    )

    df_with_council_district_filled = (
        df_with_location_type_filled
        .withColumn(
            "council_district",
            when(
                col("council_district").isNotNull(),
                col("council_district")
            ).otherwise(first("council_district", ignorenulls=True).over(zip_window))
        )
        .withColumn(
            "council_district",
            when(
                col("council_district").isNotNull(),
                col("council_district")
            ).otherwise(first("council_district", ignorenulls=True).over(community_board_window))
        )
    )

    # -----------------------------------------
    # Enforce coordinate-pair logic BEFORE fill
    # if one is missing, null both, then impute
    # -----------------------------------------
    df_coords_base = (
        df_with_council_district_filled
        .withColumn("lat_orig", col("latitude"))
        .withColumn("lon_orig", col("longitude"))
        .withColumn(
            "latitude",
            when(
                col("lat_orig").isNull() | col("lon_orig").isNull(),
                lit(None).cast(DoubleType())
            ).otherwise(col("lat_orig"))
        )
        .withColumn(
            "longitude",
            when(
                col("lat_orig").isNull() | col("lon_orig").isNull(),
                lit(None).cast(DoubleType())
            ).otherwise(col("lon_orig"))
        )
        .drop("lat_orig", "lon_orig")
    )

    # -----------------------------------------
    # Build real centroid lookup tables
    # -----------------------------------------
    zip_centroids = (
        df_coords_base
        .filter(
            col("incident_zip").isNotNull() &
            col("latitude").isNotNull() &
            col("longitude").isNotNull()
        )
        .groupBy("incident_zip")
        .agg(
            avg("latitude").alias("zip_latitude"),
            avg("longitude").alias("zip_longitude")
        )
    )

    cb_centroids = (
        df_coords_base
        .filter(
            col("community_board").isNotNull() &
            col("latitude").isNotNull() &
            col("longitude").isNotNull()
        )
        .groupBy("community_board")
        .agg(
            avg("latitude").alias("cb_latitude"),
            avg("longitude").alias("cb_longitude")
        )
    )

    # -----------------------------------------
    # Impute latitude/longitude together
    # priority:
    # 1. original
    # 2. zip centroid
    # 3. community board centroid
    # 4. leave null
    # -----------------------------------------
    df_with_coords = (
        df_coords_base.alias("d")
        .join(zip_centroids.alias("z"), on="incident_zip", how="left")
        .join(cb_centroids.alias("c"), on="community_board", how="left")
        .withColumn(
            "latitude_imputed",
            when(
                col("d.latitude").isNotNull() & col("d.longitude").isNotNull(),
                col("d.latitude")
            ).when(
                col("z.zip_latitude").isNotNull() & col("z.zip_longitude").isNotNull(),
                col("z.zip_latitude")
            ).when(
                col("c.cb_latitude").isNotNull() & col("c.cb_longitude").isNotNull(),
                col("c.cb_latitude")
            ).otherwise(lit(None).cast(DoubleType()))
        )
        .withColumn(
            "longitude_imputed",
            when(
                col("d.latitude").isNotNull() & col("d.longitude").isNotNull(),
                col("d.longitude")
            ).when(
                col("z.zip_latitude").isNotNull() & col("z.zip_longitude").isNotNull(),
                col("z.zip_longitude")
            ).when(
                col("c.cb_latitude").isNotNull() & col("c.cb_longitude").isNotNull(),
                col("c.cb_longitude")
            ).otherwise(lit(None).cast(DoubleType()))
        )
        .withColumn(
            "coord_imputation_source",
            when(
                col("d.latitude").isNotNull() & col("d.longitude").isNotNull(),
                lit("original")
            ).when(
                col("z.zip_latitude").isNotNull() & col("z.zip_longitude").isNotNull(),
                lit("incident_zip_centroid")
            ).when(
                col("c.cb_latitude").isNotNull() & col("c.cb_longitude").isNotNull(),
                lit("community_board_centroid")
            ).otherwise(lit("not_imputed"))
        )
        .drop("latitude", "longitude")
        .withColumnRenamed("latitude_imputed", "latitude")
        .withColumnRenamed("longitude_imputed", "longitude")
    )

    final_columns = [
        "unique_key",
        "created_date",
        "closed_date",
        "is_closed",
        "resolution_time",
        "agency",
        "complaint_type",
        "descriptor",
        "incident_zip",
        "address_type",
        "city",
        "status",
        "community_board",
        "council_district",
        "police_precinct",
        "borough",
        "latitude",
        "longitude",
        "location_type",
        "coord_imputation_source"
    ]

    df_final = df_with_coords.select(*final_columns)

    return df_final


def convert_data_types(df: DataFrame) -> DataFrame:
    return df \
        .withColumn("created_date", to_timestamp("created_date", "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
        .withColumn("closed_date", to_timestamp("closed_date", "yyyy-MM-dd'T'HH:mm:ss.SSS")) \
        .withColumn("latitude", col("latitude").cast(FloatType())) \
        .withColumn("longitude", col("longitude").cast(FloatType())) \
        .withColumn("unique_key", col('unique_key').cast(IntegerType())) \
        .withColumn("incident_zip", col('incident_zip').cast(IntegerType()))


def get_untransformed_data_file_paths():
    with get_db_session() as session:
        extraction_metadata = session.query(ExtractMetadata).where(
            ExtractMetadata.status == ExtractionStatus.COMPLETED.value).all()
        latest_record_created_dates = [record.latest_record_created_date.strftime('%Y-%m-%d') for record in
                                       extraction_metadata]

    return [
        f"s3a://{settings.AWS_S3_BUCKET}/raw/date={date}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"
        for date in latest_record_created_dates
    ]


def transform_dataframe(df: DataFrame) -> DataFrame:
    df = convert_data_types(df)
    df = handle_missing_values(df)
    return df


def process_raw_to_silver():
    spark = SparkSession.builder \
        .appName("Transform NYC311 Service Requests Data") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.4.1,org.apache.hadoop:hadoop-common:3.4.1") \
        .getOrCreate()

    with get_db_session() as session:
        extraction_metadata_records = session.query(ExtractMetadata) \
            .where(ExtractMetadata.status.in_([ExtractionStatus.COMPLETED.value])) \
            .all()

        for extraction_metadata_record in extraction_metadata_records:
            latest_record_created_date = extraction_metadata_record.latest_record_created_date.strftime('%Y-%m-%d')
            file_path = f"s3a://{settings.AWS_S3_BUCKET}/raw/date={latest_record_created_date}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"

            df = spark.read.format("parquet").load(file_path)

            df_transformed = transform_dataframe(df)

            df_pandas = df_transformed.toPandas()

            perform_validation(df_pandas, "transform")

            latest_record_created_date = df_pandas['created_date'].max()
            file_key = f"silver/date={latest_record_created_date.strftime('%Y-%m-%d')}/{settings.AWS_S3_DATA_PARQUET_FILENAME}"

            upload_data_to_s3(df_pandas, settings.AWS_S3_BUCKET, file_key)

            extraction_metadata_record.status = ExtractionStatus.PROCESSED.value

            session.flush()


if __name__ == "__main__":
    from logger import setup_logging

    setup_logging()
    process_raw_to_silver()
