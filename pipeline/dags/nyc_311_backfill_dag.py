import logging

from airflow.sdk import dag, task
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from spark_jobs.gold.build_nyc311_requests_fact import build_nyc311_requests_fact
from spark_jobs.session import get_spark_session
from utils.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@dag(
    dag_id="nyc_311_historical_backfill",
    schedule="@once",
    catchup=False,
    tags=["nyc311", "historical", "backfill"],
)
def nyc_311_historical_backfill():
    @task
    def historical_backfill():
        from ingestion.historical_ingest import backfill_nyc311_requests
        logger.info("Running historical backfill")
        backfill_nyc311_requests()

    @task
    def transform_and_save_requests():
        from spark_jobs.transforms.clean_nyc311_requests import clean_nyc311_requests
        from spark_jobs.transforms.enrich_nyc311_requests import enrich_nyc311_requests

        spark = get_spark_session(app_name="nyc_311_historical_backfill", s3_endpoint="http://minio:9000",
                                  access_key="changemeuser", secret_key="changemepass")

        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        cleaned_df = clean_nyc311_requests(spark)
        enriched_df = enrich_nyc311_requests(cleaned_df)

        enriched_df = enriched_df.withColumn("date", F.to_date("created_date"))

        logger.info(f"partitions before write: {enriched_df.rdd.getNumPartitions()}")

        enriched_df.write.mode("overwrite").partitionBy("date").parquet("s3a://nyc311-data/silver/")

    @task
    def build_gold_nyc311_requests_fact():
        spark = get_spark_session(app_name="nyc_311_historical_backfill", s3_endpoint="http://minio:9000",
                                  access_key="changemeuser", secret_key="changemepass")
        spark.sparkContext.setLogLevel("WARN")
        spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

        build_nyc311_requests_fact(spark)

    historical_backfill() >> transform_and_save_requests() >> build_gold_nyc311_requests_fact()


nyc_311_historical_backfill()
