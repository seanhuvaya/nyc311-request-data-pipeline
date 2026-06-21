import logging
from io import BytesIO, StringIO

import pandas as pd

from nyc311.transforms.clean import clean_nyc311_requests
from nyc311.transforms.enrich import enrich_nyc311_requests
from nyc311.utils.config import settings
from nyc311.utils.s3 import make_s3_client

logger = logging.getLogger(__name__)


def transform(s3_key: str) -> str:
    s3 = make_s3_client()
    dfs = []

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix=s3_key):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".csv"):
                continue
            logger.info(f"Reading chunk | key={key}")
            body = s3.get_object(Bucket=settings.s3_bucket_name, Key=key)["Body"].read().decode()
            df = pd.read_csv(StringIO(body))
            df = clean_nyc311_requests(df)
            df = enrich_nyc311_requests(df)
            dfs.append(df)

    if not dfs:
        raise ValueError(f"No CSV files found under s3_key={s3_key}")

    combined = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["unique_key"])
    logger.info(f"Combined {len(dfs)} chunks | total_rows={len(combined)}")

    silver_key = s3_key.replace("bronze/", "silver/", 1) + "/nyc311_requests.parquet"
    buffer = BytesIO()
    combined.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)
    s3.put_object(Bucket=settings.s3_bucket_name, Key=silver_key, Body=buffer.getvalue())

    logger.info(f"Saved Parquet to silver | silver_key={silver_key}")
    return silver_key
