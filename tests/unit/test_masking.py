"""Unit tests for PII masking helpers."""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

from src.silver_transformation import _mask_email, _mask_phone, _mask_aadhaar, _mask_pan, _mask_card_number


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("test").getOrCreate()


def test_mask_email(spark):
    df = spark.createDataFrame(
        [("john.smith@gmail.com",), (None,), ("a@b.co",)],
        ["email"],
    ).withColumn("masked", _mask_email(F.col("email")))
    rows = {r["email"]: r["masked"] for r in df.collect()}
    assert rows["john.smith@gmail.com"] == "j*********@gmail.com"
    assert rows[None] == "***@***"
    assert rows["a@b.co"] == "a*********@b.co"


def test_mask_phone(spark):
    df = spark.createDataFrame([("+919876543210",), (None,)], ["phone"]) \
              .withColumn("masked", _mask_phone(F.col("phone")))
    rows = {r["phone"]: r["masked"] for r in df.collect()}
    assert rows["+919876543210"] == "+91-XXXXX-43210"
    assert rows[None] == "+91-XXXXX-00000"


def test_mask_aadhaar(spark):
    df = spark.createDataFrame([("123456789012",), ("12345",), (None,)], ["a"]) \
              .withColumn("masked", _mask_aadhaar(F.col("a")))
    rows = {r["a"]: r["masked"] for r in df.collect()}
    assert rows["123456789012"] == "XXXX-XXXX-9012"
    assert rows["12345"] == "XXXX-XXXX-0000"


def test_mask_pan(spark):
    df = spark.createDataFrame([("ABCDE1234F",), ("BAD",), (None,)], ["p"]) \
              .withColumn("masked", _mask_pan(F.col("p")))
    rows = {r["p"]: r["masked"] for r in df.collect()}
    assert rows["ABCDE1234F"] == "ABCDE****F"
    assert rows["BAD"] == "ABCDE****F"


def test_mask_card(spark):
    df = spark.createDataFrame([("1234567890123456",), ("123",), (None,)], ["c"]) \
              .withColumn("masked", _mask_card_number(F.col("c")))
    rows = {r["c"]: r["masked"] for r in df.collect()}
    assert rows["1234567890123456"] == "123456******3456"
    assert rows["123"] == "XXXXXX******XXXX"