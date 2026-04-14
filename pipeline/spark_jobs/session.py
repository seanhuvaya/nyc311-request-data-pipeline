from pyspark.sql import SparkSession


def get_spark_session(
        app_name: str,
        s3_endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        use_ssl: bool = False,
) -> SparkSession:
    session_builder = SparkSession.builder.appName(app_name).master("local[*]")

    if s3_endpoint:
        session_builder.config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.4.1")
        session_builder.config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        session_builder.config("spark.hadoop.fs.s3a.access.key", access_key)
        session_builder.config("spark.hadoop.fs.s3a.secret.key", secret_key)
        session_builder.config("spark.hadoop.fs.s3a.path.style.access", "true")
        session_builder.config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        session_builder.config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(use_ssl).lower())

    return session_builder.getOrCreate()
