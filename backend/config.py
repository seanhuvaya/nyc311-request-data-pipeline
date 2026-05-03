from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")

    # Comma-separated list of origins allowed by CORS, e.g.
    # "https://nyc311.seanhuvaya.dev,http://localhost:5173"
    #
    # Stored as a raw string because pydantic-settings tries to JSON-decode
    # list-typed env vars before any validator runs. We split in `cors_origins`
    # below.
    cors_allowed_origins_raw: str = Field(
        default="http://localhost:5173",
        alias="CORS_ALLOWED_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins_raw.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
