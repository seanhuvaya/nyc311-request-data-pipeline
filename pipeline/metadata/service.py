from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from utils.db import get_db_engine
from .models import IngestionMetadata


def get_metadata(pipeline_name: str, source_name: str, watermark_column: str) -> IngestionMetadata | None:
    with Session(get_db_engine()) as session:
        statement = select(IngestionMetadata).where(
            IngestionMetadata.pipeline_name == pipeline_name,
            IngestionMetadata.source_name == source_name,
            IngestionMetadata.watermark_column == watermark_column
        )

        return session.execute(statement).scalar_one_or_none()


def update_metadata(pipeline_name: str, source_name: str, watermark_column: str, watermark_value: datetime):
    with Session(get_db_engine()) as session:
        statement = select(IngestionMetadata).where(
            IngestionMetadata.pipeline_name == pipeline_name,
            IngestionMetadata.source_name == source_name,
            IngestionMetadata.watermark_column == watermark_column
        )

        record = session.execute(statement).scalar_one_or_none()

        if record:
            record.watermark_value = watermark_value
            record.updated_at = datetime.now(timezone.utc)
        else:
            record = IngestionMetadata(
                pipeline_name=pipeline_name,
                source_name=source_name,
                watermark_column=watermark_column,
                watermark_value=watermark_value,
            )
            session.add(record)

        session.commit()


if __name__ == "__main__":
    result = get_metadata(pipeline_name="nyc_311_api", source_name="requests", watermark_column="created_date")
    print(result)
    # update_metadata(pipeline_name="nyc_311_api", source_name="requests", watermark_column="created_date",
    #                 watermark_value=datetime.now(timezone.utc))
    #
    # result = get_metadata(pipeline_name="nyc_311_api", source_name="requests", watermark_column="created_date")
    # print(result)
