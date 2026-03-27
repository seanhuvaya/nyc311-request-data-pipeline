from dataclasses import dataclass
from typing import List

from utils.config import settings
from db import get_db_session
from db.models import ExtractMetadata
from db.models.extraction_metadata import ExtractionStatus


@dataclass(frozen=True)
class PendingTransformJob:
    """One extraction that finished loading to raw S3 and still needs silver."""

    extraction_id: int
    raw_s3_uri: str
    partition_date_str: str


def list_pending_transform_jobs() -> List[PendingTransformJob]:
    """Return extractions with raw data in S3 (COMPLETED) not yet written to silver (not PROCESSED)."""
    with get_db_session() as session:
        records = (
            session.query(ExtractMetadata)
            .where(ExtractMetadata.status == ExtractionStatus.COMPLETED.value)
            .all()
        )

        jobs: List[PendingTransformJob] = []
        for record in records:
            if record.latest_record_created_date is None:
                continue
            date_str = record.latest_record_created_date.strftime("%Y-%m-%d")
            raw_uri = (
                f"s3a://{settings.AWS_S3_BUCKET}/raw/date={date_str}/"
                f"{settings.AWS_S3_DATA_PARQUET_FILENAME}"
            )
            jobs.append(
                PendingTransformJob(
                    extraction_id=record.id,
                    raw_s3_uri=raw_uri,
                    partition_date_str=date_str,
                )
            )
        return jobs


def get_silver_parquet_dir_s3a(partition_date_str: str) -> str:
    """S3A URI for Spark to write silver parquet (directory of part files)."""
    return f"s3a://{settings.AWS_S3_BUCKET}/silver/date={partition_date_str}/"


def mark_transform_processed(extraction_id: int) -> None:
    """Set extraction status to PROCESSED after silver has been written."""
    with get_db_session() as session:
        record = session.get(ExtractMetadata, extraction_id)
        if not record:
            raise LookupError(f"Extraction record {extraction_id} not found")
        record.status = ExtractionStatus.PROCESSED.value
