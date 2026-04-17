from pyspark.sql import SparkSession

from utils.config import settings


def get_spark_session(
        app_name: str,
        use_s3: bool = False,
        use_postgres: bool = False,
        use_ssl: bool = False
) -> SparkSession:
    session_builder = SparkSession.builder.appName(app_name).master("local[*]")
    packages = []

    if use_s3:
        packages.append("org.apache.hadoop:hadoop-aws:3.4.2")
        session_builder.config("spark.hadoop.fs.s3a.endpoint", settings.s3_endpoint_url)
        session_builder.config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key_id)
        session_builder.config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_access_key)
        session_builder.config("spark.hadoop.fs.s3a.path.style.access", "true")
        session_builder.config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        session_builder.config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(use_ssl).lower())

    if use_postgres:
        packages.append("org.postgresql:postgresql:42.7.3")

    if len(packages) > 0:
        session_builder.config("spark.jars.packages", ",".join(packages))

    return session_builder.getOrCreate()
