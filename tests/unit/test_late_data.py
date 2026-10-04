"""Verify late-arrival detection logic."""
from datetime import datetime, timedelta
import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[2]").appName("test").getOrCreate()


def test_late_by_hours_computation(spark):
    """late_by_hours = ingestion_ts - txn_ts, in hours."""
    schema = StructType([
        StructField("transaction_id",        StringType()),
        StructField("transaction_timestamp", TimestampType()),
        StructField("_ingestion_timestamp",  TimestampType()),
    ])
    base = datetime(2026, 10, 1, 22, 0, 0)
    data = [
        ("TXN-LATE",   base,                   base + timedelta(hours=30)),
        ("TXN-ONTIME", base,                   base + timedelta(hours=1)),
    ]
    df = spark.createDataFrame(data, schema)
    df = df.withColumn("late_by_hours",
        F.round(
            (F.unix_timestamp("_ingestion_timestamp")
             - F.unix_timestamp("transaction_timestamp")) / 3600.0,
            2,
        ))

    rows = {r["transaction_id"]: r["late_by_hours"] for r in df.collect()}
    assert rows["TXN-LATE"]   == 30.0
    assert rows["TXN-ONTIME"] == 1.0