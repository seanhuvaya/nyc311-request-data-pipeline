from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")

    # Comma-separated list of origins allowed by CORS, e.g.
    # "https://nyc311.seanhuvaya.dev,http://localhost:5173"
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="CORS_ALLOWED_ORIGINS",
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
