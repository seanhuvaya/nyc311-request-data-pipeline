from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@postgres:5432/nyc311",
                              alias="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
