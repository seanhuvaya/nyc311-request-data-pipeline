from pyspark.sql import DataFrame, SparkSession

from src.utils.config import settings


def load_to_postgres(df: DataFrame, table_name: str) -> None:
    df.write.format("jdbc") \
        .option("url", f"jdbc:postgresql://{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}") \
        .option("dbtable", table_name) \
        .option("user", settings.PG_USER) \
        .option("password", settings.PG_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()


def load_from_postgres(spark: SparkSession, table_name: str) -> DataFrame:
    return spark.read.format("jdbc") \
        .option("url", f"jdbc:postgresql://{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}") \
        .option("dbtable", table_name) \
        .option("user", settings.PG_USER) \
        .option("password", settings.PG_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .load()
