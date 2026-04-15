import os

from pyspark.sql import DataFrame


def load_to_postgres(df: DataFrame, table_name: str) -> None:
    db_host = os.environ.get("DB_HOST", "postgres")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "nyc311")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "postgres")

    db_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"

    df.write.format("jdbc") \
        .option("url", db_url) \
        .option("dbtable", table_name) \
        .option("user", db_user) \
        .option("password", db_password) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
