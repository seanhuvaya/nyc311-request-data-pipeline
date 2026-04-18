from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
