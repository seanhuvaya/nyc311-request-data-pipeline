import logging

from airflow.sdk import task

logger = logging.getLogger(__name__)


@task
def transform_and_load(ingest_result: dict) -> int:
    from nyc311.jobs.load import transform_and_load as _load
    s3_key = ingest_result["s3_key"]
    logger.info(f"Starting transform and load | s3_key={s3_key}")
    rows = _load(s3_key=s3_key)
    logger.info(f"Transform and load complete | s3_key={s3_key}, rows={rows}")
    return rows
