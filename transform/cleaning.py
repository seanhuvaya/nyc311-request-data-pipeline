import logging

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    when, col, first, lit, avg, coalesce
)

from .config import TransformationConfig

logger = logging.getLogger(__name__)


def handle_missing_values(df: DataFrame, config: TransformationConfig) -> DataFrame:
    """Clean and impute missing values with clear priority logic."""
    logger.info("Starting data cleaning and imputation...")

    # Drop unnecessary columns
    df = df.drop(*config.columns_to_drop)
    logger.info(f"Dropped {len(config.columns_to_drop)} irrelevant columns.")

    # Derived columns
    df = df.withColumn(
        "is_closed",
        when(col("closed_date").isNotNull(), True).otherwise(False)
    ).withColumn(
        "resolution_time",
        when(
            col("closed_date").isNotNull(),
            (col("closed_date").cast("long") - col("created_date").cast("long")) / 3600.0
        ).otherwise(lit(None).cast("double"))
    )

    # Define windows once
    win_lat_lon = Window.partitionBy("latitude", "longitude")
    win_borough = Window.partitionBy("borough")
    win_complaint = Window.partitionBy("complaint_type")
    win_agency = Window.partitionBy("agency")
    win_descriptor = Window.partitionBy("descriptor")
    win_zip = Window.partitionBy("incident_zip")
    win_cb = Window.partitionBy("community_board")

    # Impute categorical fields with fallback hierarchy
    df = (
        df.withColumn("incident_zip",
                      coalesce(
                          col("incident_zip"),
                          first("incident_zip", ignorenulls=True).over(win_lat_lon),
                          first("incident_zip", ignorenulls=True).over(win_borough)
                      ))
        .withColumn("address_type",
                    coalesce(
                        col("address_type"),
                        first("address_type", ignorenulls=True).over(win_complaint),
                        first("address_type", ignorenulls=True).over(win_agency),
                        lit(config.imputation_fallback)
                    ))
        .withColumn("city",
                    coalesce(
                        col("city"),
                        first("city", ignorenulls=True).over(win_borough),
                        lit(config.imputation_fallback)
                    ))
        .withColumn("location_type",
                    coalesce(
                        col("location_type"),
                        first("location_type", ignorenulls=True).over(win_complaint),
                        first("location_type", ignorenulls=True).over(win_descriptor),
                        lit(config.imputation_fallback)
                    ))
        .withColumn("council_district",
                    coalesce(
                        col("council_district"),
                        first("council_district", ignorenulls=True).over(win_zip),
                        first("council_district", ignorenulls=True).over(win_cb)
                    ))
    )

    # Enforce coordinate pair integrity
    df = df.withColumn("latitude",
                       when(col("latitude").isNull() | col("longitude").isNull(), lit(None)).otherwise(col("latitude"))) \
        .withColumn("longitude",
                    when(col("latitude").isNull() | col("longitude").isNull(), lit(None)).otherwise(col("longitude")))

    # Build centroid lookup tables
    zip_centroids = (
        df.filter(col("incident_zip").isNotNull() & col("latitude").isNotNull() & col("longitude").isNotNull())
        .groupBy("incident_zip")
        .agg(avg("latitude").alias("zip_lat"), avg("longitude").alias("zip_lon"))
    )

    cb_centroids = (
        df.filter(col("community_board").isNotNull() & col("latitude").isNotNull() & col("longitude").isNotNull())
        .groupBy("community_board")
        .agg(avg("latitude").alias("cb_lat"), avg("longitude").alias("cb_lon"))
    )

    # Impute coordinates with priority: original → zip centroid → cb centroid
    df = (
        df.alias("d")
        .join(zip_centroids.alias("z"), on="incident_zip", how="left")
        .join(cb_centroids.alias("c"), on="community_board", how="left")
        .withColumn("latitude",
                    coalesce(
                        col("d.latitude"),
                        col("z.zip_lat"),
                        col("c.cb_lat")
                    ))
        .withColumn("longitude",
                    coalesce(
                        col("d.longitude"),
                        col("z.zip_lon"),
                        col("c.cb_lon")
                    ))
        .withColumn("coord_imputation_source",
                    when(col("d.latitude").isNotNull() & col("d.longitude").isNotNull(), lit("original"))
                    .when(col("z.zip_lat").isNotNull() & col("z.zip_lon").isNotNull(), lit("incident_zip_centroid"))
                    .when(col("c.cb_lat").isNotNull() & col("c.cb_lon").isNotNull(), lit("community_board_centroid"))
                    .otherwise(lit("not_imputed")))
    )

    return df.select(*config.final_columns)
