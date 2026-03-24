import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, String, Enum, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base


class ExtractionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INITIATED = "INITIATED"


class ExtractMetadata(Base):
    __tablename__ = "extraction_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    extraction_started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    extraction_completed_at = Column(DateTime(timezone=True))

    status = Column(String(20), default=ExtractionStatus.PENDING.value)

    num_records_pulled = Column(Integer, nullable=False, default=0)
    latest_record_created_date = Column(DateTime(timezone=True))

    data_file_path = Column(String)
    data_file_size_in_bytes = Column(BigInteger)
    data_file_checksum = Column(String(64))

    error_message = Column(String)
    parameters = Column(JSONB)
