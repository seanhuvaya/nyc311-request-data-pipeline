import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select

from src.db.models import IngestionMetadata
from src.db.session import get_db_session

logger = logging.getLogger(__name__)


def get_latest_record_created_date() -> Optional[datetime]:
    with get_db_session() as session:
        stmt = select(IngestionMetadata.latest_record_created_date) \
            .order_by(desc(IngestionMetadata.latest_record_created_date)) \
            .limit(1)

        return session.execute(stmt).scalar_one_or_none()


def save_ingestion_metadata(latest_record_date: datetime, row_count: int, s3_key: str, pipeline_run_id: int) -> int:
    with get_db_session() as session:
        record = IngestionMetadata(
            num_records_pulled=row_count,
            latest_record_created_date=latest_record_date,
            s3_key=s3_key,
            pipeline_run_id=pipeline_run_id
        )

        session.add(record)
        session.flush()

        return record.id


def get_s3_key_by_pipeline_run_id(pipeline_run_id: int) -> str:
    with get_db_session() as session:
        stmt = select(IngestionMetadata.s3_key) \
            .where(IngestionMetadata.pipeline_run_id == pipeline_run_id) \
            .limit(1)

        return session.execute(stmt).scalar_one_or_none()
