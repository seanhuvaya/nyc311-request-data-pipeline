from datetime import datetime
from .nyc_311_api_ingest import extract_nyc311_requests_since
from metadata.service import update_metadata


def backfill_nyc311_requests():
    backfill_date = datetime.now()
    backfill_start_date = datetime(2026, 4, 1)

    latest_created_date = extract_nyc311_requests_since(
        extraction_date=backfill_date,
        start_date=backfill_start_date
    )

    update_metadata(pipeline_name="nyc_311", source_name="erm2-nwe9", watermark_column="created_date",
                    watermark_value=latest_created_date)


if __name__ == "__main__":
    backfill_nyc311_requests()
