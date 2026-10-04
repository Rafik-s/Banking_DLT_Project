"""
MODULE: SILVER LATE DATA QUARANTINE

Routes transactions that arrive AFTER the 24-hour watermark window into a
quarantine table. These are NOT silently dropped — they are:
  1. Persisted with a quarantine_reason
  2. Counted in DQ metrics
  3. Alerted on-call if volume exceeds threshold
  4. Available for manual replay once the source system is fixed

Design principle for banking: **no silent data loss**.
"""
import dlt
from pyspark.sql import functions as F

from schemas_and_security import CATALOG, BRONZE_SCHEMA, SILVER_SCHEMA


@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions_late",
    comment="Transactions arriving after the 24h watermark window. Requires manual triage.",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
    },
)
def silver_transactions_late():
    """
    Detect transactions whose transaction_timestamp is OLDER than the
    watermark window, meaning Spark's stream-stream watermark would drop them.

    These are captured from Bronze directly (not from Silver) so nothing
    is lost. A separate replay job can push them into Silver once the
    source system is caught up.
    """
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_transactions")
            # Anything with a timestamp older than 'now - 24h' at the time of ingest
            .filter(
                F.col("transaction_timestamp").isNotNull()
                & (F.col("transaction_timestamp")
                   < F.col("_ingestion_timestamp") - F.expr("INTERVAL 24 HOURS"))
            )
            .withColumn("quarantine_reason", F.lit("LATE_ARRIVAL_BEYOND_WATERMARK"))
            .withColumn("quarantine_ts", F.current_timestamp())
            .withColumn("late_by_hours",
                F.round(
                    (F.unix_timestamp("_ingestion_timestamp")
                     - F.unix_timestamp("transaction_timestamp")) / 3600.0,
                    2,
                ))
            .select(
                "transaction_id",
                "account_id",
                "customer_id",
                "amount",
                "transaction_timestamp",
                "_ingestion_timestamp",
                "_source_file_path",
                "late_by_hours",
                "quarantine_reason",
                "quarantine_ts",
            )
    )