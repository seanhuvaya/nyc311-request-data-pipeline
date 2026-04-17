from pyspark.sql import DataFrame

from utils.config import settings


def load_to_postgres(df: DataFrame, table_name: str, truncate: bool = False) -> None:
    db_url = f"jdbc:postgresql://{settings.db_host}:{settings.db_port}/{settings.db_name}"

    db_writer = df.coalesce(1).write.format("jdbc") \
        .option("url", db_url) \
        .option("dbtable", table_name) \
        .option("user", settings.db_user) \
        .option("password", settings.db_password) \
        .option("driver", "org.postgresql.Driver")

    if truncate:
        db_writer.option("truncate", truncate).mode("overwrite").save()
    else:
        db_writer.mode("append").save()
