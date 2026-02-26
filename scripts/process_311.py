import os

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_timestamp, coalesce, when, current_timestamp, unix_timestamp, dayofweek, \
    dayofmonth, hour, year, month
from pyspark.sql.types import IntegerType, FloatType

from utils.config import yml_config


def clean_and_validate_data(df: DataFrame) -> DataFrame:
    # Parse Timestamps
    df = df.withColumn("created_date", to_timestamp(col("created_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS"))
    df = df.withColumn("closed_date",
                       coalesce(to_timestamp(col("closed_date"), "yyyy-MM-dd'T'HH:mm:ss.SSS"), col("created_date")))

    # Handling missing values
    df = df.withColumn("closed_date",
                       when(col("closed_date").isNull(), current_timestamp()).otherwise(col("closed_date")))
    df = df.dropna(subset=["borough", "incident_zip"])

    # Data Type correction
    df = df.withColumn("unique_key", col("unique_key").cast(IntegerType()))
    df = df.withColumn("incident_zip", col("incident_zip").cast(IntegerType()))
    df = df.withColumn("longitude", col("longitude").cast(FloatType()))
    df = df.withColumn("latitude", col("latitude").cast(FloatType()))

    # Remove Duplicates
    df = df.dropDuplicates(["unique_key"])
    return df


def enrich_data(df: DataFrame) -> DataFrame:
    # Calculate resolution time
    df = df.withColumn("resolution_time_hours", (unix_timestamp("closed_date") - unix_timestamp("created_date")) / 3600)
    df = df.filter(col("resolution_time_hours") >= 0)

    # Extract Date Components
    df = df.withColumn("created_year", year("created_date")) \
        .withColumn("created_month", month("created_date")) \
        .withColumn("created_day", dayofmonth("created_date")) \
        .withColumn("created_hour", hour("created_date")) \
        .withColumn("created_weekday", dayofweek("created_date"))

    # Geospatial Enrichment (Rough NYC bounds)
    df = df.filter((col("latitude").between(40.5, 45.0)) & (col("longitude").between(-74.25, -73.7)))

    return df


def aggregate_data(df: DataFrame) -> None:
    processed_path = os.path.join(os.getcwd(), "processed")
    agg_df = df.groupBy("borough", "complaint_type").count().orderBy("count", ascending=False)
    agg_df.write.parquet(os.path.join(processed_path, "nyc311_complaint_by_borough.parquet"), mode="overwrite")

    avg_res_df = df.groupBy("agency", "complaint_type").agg({"resolution_time_hours": "avg"}).alias(
        "avg_resolution_hours")
    avg_res_df.write.parquet(os.path.join(processed_path, "nyc311_complaint_resolution_hours_by_agency.parquet"),
                             mode="overwrite")

    hourly_df = df.groupBy("created_hour").count().orderBy("created_hour")
    hourly_df.write.parquet(os.path.join(processed_path, "nyc311_complaint_by_created_hour.parquet"), mode="overwrite")

    status_df = df.groupBy("borough").pivot("status").count()
    status_df.write.parquet(os.path.join(processed_path, "nyc311_complaint_status_by_borough.parquet"),
                            mode="overwrite")


def process():
    spark = SparkSession.builder.appName("NYC311Processing").master(yml_config.config['spark']['master']).getOrCreate()

    file_path = os.path.join(os.getcwd(), "raw/nyc311_raw_*.csv")

    df = spark.read \
        .option("timestampFormat", "yyyy-MM-dd'T'HH:mm:ss.SSS") \
        .csv(file_path, header=True, inferSchema=True)

    df = clean_and_validate_data(df)
    df = enrich_data(df)
    aggregate_data(df)

    spark.stop()


if __name__ == "__main__":
    process()
