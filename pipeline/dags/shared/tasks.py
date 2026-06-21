import logging

from airflow.sdk import task

logger = logging.getLogger(__name__)


@task
def transform(ingest_result: dict) -> str:
    from nyc311.jobs.transform import transform as _transform
    s3_key = ingest_result["s3_key"]
    logger.info(f"Starting transform | s3_key={s3_key}")
    silver_key = _transform(s3_key=s3_key)
    logger.info(f"Transform complete | silver_key={silver_key}")
    return silver_key


@task
def load(silver_key: str) -> int:
    from nyc311.jobs.load import load as _load
    logger.info(f"Starting load | silver_key={silver_key}")
    rows = _load(silver_key=silver_key)
    logger.info(f"Load complete | silver_key={silver_key}, rows={rows}")
    return rows
