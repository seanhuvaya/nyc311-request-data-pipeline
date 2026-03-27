import logging

from utils.date_utils import format_date_for_api, get_latest_record_created_date
from extractor import fetch_all_311_requests
from metadata import log_extraction_end
from db.models.extraction_metadata import ExtractionStatus
from uploader import upload_raw_data_to_s3
from validate import perform_validation

logger = logging.getLogger(__name__)


def extract_nyc311_requests() -> None:
    """Main orchestration for NYC 311 extraction pipeline."""
    try:
        latest_date = get_latest_record_created_date()
        logger.info(f"Latest record date from metadata: {latest_date}")

        api_date_str = format_date_for_api(latest_date)

        raw_df, extraction_id = fetch_all_311_requests(api_date_str)

        try:
            perform_validation(raw_df, "extract")
        except Exception as e:
            log_extraction_end(
                extraction_id=extraction_id,
                status=ExtractionStatus.FAILED.value,
                error_message=f"Post-fetch validation failed: {e}",
            )
            raise

        upload_raw_data_to_s3(raw_df, extraction_id)

        logger.info("NYC 311 extraction pipeline completed successfully")

    except Exception as e:
        logger.exception("Pipeline failed")
        # Optional: re-raise or handle globally depending on your runner (Airflow, cron, etc.)
        raise


if __name__ == "__main__":
    from utils.logger import setup_logging

    setup_logging()
    extract_nyc311_requests()
