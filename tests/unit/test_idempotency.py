"""Verify business idempotency key behavior."""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DecimalType, TimestampType
)


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[2]").appName("test").getOrCreate()


def test_idempotency_key_deduplicates_same_source(spark):
    """Same (transaction_id, source_system, event_version) → one row."""
    schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("source_system",  StringType()),
        StructField("event_version",  IntegerType()),
        StructField("amount",         DecimalType(18, 2)),
    ])
    data = [
        ("TXN-001", "CORE_BANKING", 1, 1000),
        ("TXN-001", "CORE_BANKING", 1, 1000),  # duplicate
    ]
    df = spark.createDataFrame(data, schema)
    deduped = df.dropDuplicates(["transaction_id", "source_system", "event_version"])
    assert deduped.count() == 1


def test_idempotency_key_allows_different_sources(spark):
    """Same transaction_id in different sources → two rows."""
    schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("source_system",  StringType()),
        StructField("event_version",  IntegerType()),
        StructField("amount",         DecimalType(18, 2)),
    ])
    data = [
        ("TXN-001", "CORE_BANKING", 1, 1000),
        ("TXN-001", "UPI",          1, 2000),
        ("TXN-001", "NEFT",         1, 3000),
    ]
    df = spark.createDataFrame(data, schema)
    deduped = df.dropDuplicates(["transaction_id", "source_system", "event_version"])
    assert deduped.count() == 3


def test_idempotency_key_allows_event_version_bump(spark):
    """Same transaction with new event_version → two rows (correction)."""
    schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("source_system",  StringType()),
        StructField("event_version",  IntegerType()),
        StructField("amount",         DecimalType(18, 2)),
    ])
    data = [
        ("TXN-001", "CORE_BANKING", 1, 1000),
        ("TXN-001", "CORE_BANKING", 2, 950),   # correction
    ]
    df = spark.createDataFrame(data, schema)
    deduped = df.dropDuplicates(["transaction_id", "source_system", "event_version"])
    assert deduped.count() == 2