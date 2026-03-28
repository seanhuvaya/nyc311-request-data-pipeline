import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from src.db.models import Base


class ExtractionStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INITIATED = "INITIATED"
    PROCESSED = "PROCESSED"


class ExtractMetadata(Base):
    __tablename__ = "extraction_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    extraction_started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    extraction_completed_at = Column(DateTime(timezone=True))

    status = Column(String(20), default=ExtractionStatus.INITIATED.value)

    num_records_pulled = Column(Integer, nullable=False, default=0)
    latest_record_created_date = Column(DateTime(timezone=True))

    error_message = Column(String)
    parameters = Column(JSONB)
