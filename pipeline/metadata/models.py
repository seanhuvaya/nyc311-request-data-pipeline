from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class IngestionMetadata(SQLModel, table=True):
    __tablename__ = "ingestion_metadata"
    __table_args__ = {"schema": "metadata"}

    pipeline_name: str = Field(primary_key=True)
    source_name: str = Field(primary_key=True)
    watermark_column: str = Field(primary_key=True)

    watermark_value: datetime
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
