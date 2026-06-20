from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    db_name: str = Field(default="nyc311", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")
    db_host: str = Field(default="postgres", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")

    dataset_url: str = Field(default="https://data.cityofnewyork.us/resource/erm2-nwe9.csv", alias="DATASET_URL")

    aws_access_key_id: str = Field(default="changemeuser", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="changemepass", alias="AWS_SECRET_ACCESS_KEY")
    s3_endpoint_url: str = Field(default="http://minio:9000", alias="S3_ENDPOINT_URL")
    s3_bucket_name: str = Field(default="nyc311-data", alias="S3_BUCKET_NAME")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_save_key: str = Field(default="nyc311_requests", alias="S3_SAVE_KEY")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
