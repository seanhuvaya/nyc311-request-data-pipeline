import logging
import random
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

random.seed(42)


def perform_spark_validation_sample(
    df,
    stage_name: str,
    sample_size: int = 10_000,
) -> None:
    """Run the same EDA checks on a sampled subset without collecting the full DataFrame."""
    from pyspark.sql import DataFrame as SparkDataFrame

    if not isinstance(df, SparkDataFrame):
        raise TypeError("perform_spark_validation_sample expects a PySpark DataFrame")

    n = df.count()
    if n == 0:
        logger.info("Skipping Spark validation for %s: empty DataFrame", stage_name)
        return
    fraction = min(1.0, sample_size / max(n, 1))
    pdf = df.sample(False, fraction, seed=42).limit(sample_size).toPandas()
    perform_validation(pdf, stage_name, sample_size=len(pdf))


def perform_validation(df: pd.DataFrame, stage_name: str, sample_size: int = 10_000):
    start = datetime.now()
    logger.info(f"Starting EDA for stage: {stage_name} | Shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")

    df_sample = df.sample(min(sample_size, len(df))) if len(df) > sample_size else df

    logger.info(f"Rows: {len(df)} | Columns: {len(df.columns)}")

    null_pct = (df_sample.isnull().mean() * 100).round(2)
    logger.info(f"Missing values (%):")

    for col, pct in null_pct.items():
        logger.info(f'\t{col}: {pct}% missing')

    duration = (datetime.now() - start).total_seconds()
    logger.info(f"EDA completed in {duration:.2f}s for {stage_name}")


