#!/usr/bin/env python3
"""Nightly warehouse sync: dump three source tables to S3 as Parquet, refresh views."""
import datetime as dt
import os

import boto3
import pandas as pd
from sqlalchemy import create_engine, text

TABLES = ["orders", "shipments", "customers"]
BUCKET = os.environ["WAREHOUSE_BUCKET"]
PREFIX = "raw"

def engine():
    return create_engine(os.environ["APP_DATABASE_URL"])

def dump_table(eng, s3, name, stamp):
    df = pd.read_sql_table(name, eng)
    key = f"{PREFIX}/{name}/{stamp}.parquet"
    path = f"/tmp/{name}.parquet"
    df.to_parquet(path, index=False)
    s3.upload_file(path, BUCKET, key)
    return len(df), key

def refresh_views(eng):
    with eng.begin() as conn:
        conn.execute(text("REFRESH MATERIALIZED VIEW daily_order_summary"))
        conn.execute(text("REFRESH MATERIALIZED VIEW active_customer_rollup"))

def main():
    stamp = dt.date.today().isoformat()
    eng = engine()
    s3 = boto3.client("s3")
    for name in TABLES:
        rows, key = dump_table(eng, s3, name, stamp)
        print(f"wrote {rows} rows -> s3://{BUCKET}/{key}")
    refresh_views(eng)
    print("views refreshed; sync complete")

if __name__ == "__main__":
    main()
