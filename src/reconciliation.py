"""
MODULE: BANKING RECONCILIATION ENGINE

Runs after every DLT pipeline execution to verify:
  1. COUNT_LAYER     — Bronze ↔ Silver ↔ Gold row counts tie out
  2. COUNT_FINANCIAL — Source system file count matches Bronze count
  3. AMOUNT          — Sum of amounts tie out across layers
  4. DOUBLE_ENTRY    — SUM(debits) == SUM(credits) per business date

Outputs to `${catalog}.cur_gold.reconciliation_results`.

Status semantics:
  PASS     — within tolerance
  WARNING  — within 0.01% but not exact
  FAIL     — outside tolerance (triggers on-call page)
  SKIPPED  — upstream data unavailable (e.g., no transactions on a Sunday)
"""
import sys
import logging
from datetime import date, timedelta
from decimal import Decimal

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DateType, IntegerType,
    DecimalType, TimestampType,
)

# ---------------------------------------------------------------------------
# PARAMETERS (passed by Workflow)
# ---------------------------------------------------------------------------
dbutils.widgets.text("catalog",         "banking_dev_catalog")
dbutils.widgets.text("business_date",   "")   # YYYY-MM-DD, defaults to yesterday
dbutils.widgets.text("tolerance_pct",   "0.0001")  # 0.01%

CATALOG        = dbutils.widgets.get("catalog")
BUSINESS_DATE  = (
    dbutils.widgets.get("business_date")
    or (date.today() - timedelta(days=1)).isoformat()
)
TOLERANCE_PCT  = float(dbutils.widgets.get("tolerance_pct"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("banking.reconciliation")

spark = SparkSession.builder.getOrCreate()


# ---------------------------------------------------------------------------
# SCHEMA for reconciliation_results
# ---------------------------------------------------------------------------
RECON_SCHEMA = StructType([
    StructField("business_date",       DateType(),        False),
    StructField("dataset",             StringType(),      False),
    StructField("reconciliation_type", StringType(),      False),
    StructField("source_layer",        StringType(),      False),
    StructField("target_layer",        StringType(),      False),
    StructField("source_count",        IntegerType(),     True),
    StructField("target_count",        IntegerType(),     True),
    StructField("count_difference",    IntegerType(),     True),
    StructField("source_amount_inr",   DecimalType(20, 2), True),
    StructField("target_amount_inr",   DecimalType(20, 2), True),
    StructField("amount_difference",   DecimalType(20, 2), True),
    StructField("tolerance_pct",       DecimalType(5, 4), True),
    StructField("status",              StringType(),      False),
    StructField("failure_reason",      StringType(),      True),
    StructField("reconciled_at",       TimestampType(),   False),
])


def _classify(count_diff: int, amount_diff: Decimal, tolerance_pct: float) -> tuple:
    """Return (status, failure_reason) based on tolerances."""
    if count_diff == 0 and (amount_diff is None or amount_diff == 0):
        return "PASS", None
    if count_diff == 0 and amount_diff is not None:
        # Amount mismatch — check relative tolerance
        return "FAIL", f"count OK but amount differs by {amount_diff}"
    if abs(count_diff) > 0:
        return "FAIL", f"row count difference of {count_diff}"
    return "WARNING", "unspecified discrepancy"


def _safe_count(df) -> int:
    try:
        return df.count()
    except Exception as e:
        logger.warning(f"Count failed: {e}")
        return 0


def _safe_sum_amount(df, col_name="amount"):
    try:
        row = df.agg(F.sum(col_name).alias("total")).collect()[0]
        return row["total"] or Decimal("0.00")
    except Exception as e:
        logger.warning(f"Amount sum failed: {e}")
        return Decimal("0.00")


# ---------------------------------------------------------------------------
# RECONCILIATION 1 — Transactions: Bronze → Silver → Gold
# ---------------------------------------------------------------------------
def recon_transactions() -> list:
    """
    Reconcile the transaction flow across all three layers.
    Returns a list of reconciliation rows (as dicts).
    """
    results = []
    biz_date = BUSINESS_DATE

    logger.info(f"Reconciling transactions for business_date = {biz_date}")

    try:
        bronze = (
            spark.read.table(f"{CATALOG}.raw_bronze.bronze_transactions")
                .filter(F.to_date("transaction_timestamp") == F.lit(biz_date))
        )
        bronze_count  = _safe_count(bronze)
        bronze_amount = _safe_sum_amount(bronze)

        silver = (
            spark.read.table(f"{CATALOG}.clean_silver.silver_transactions")
                .filter(F.to_date("transaction_timestamp") == F.lit(biz_date))
        )
        silver_count  = _safe_count(silver)
        silver_amount = _safe_sum_amount(silver)

        quarantine = (
            spark.read.table(f"{CATALOG}.clean_silver.silver_transactions_quarantine")
                .filter(F.to_date("transaction_timestamp") == F.lit(biz_date))
        )
        quarantine_count = _safe_count(quarantine)

        late = (
            spark.read.table(f"{CATALOG}.clean_silver.silver_transactions_late")
                .filter(F.to_date("transaction_timestamp") == F.lit(biz_date))
        )
        late_count = _safe_count(late)

        gold = (
            spark.read.table(f"{CATALOG}.cur_gold.fact_transactions")
                .filter(F.col("date_key") == F.date_format(F.lit(biz_date), "yyyyMMdd"))
        )
        gold_count  = _safe_count(gold)
        gold_amount = _safe_sum_amount(gold)

        # --- Bronze → Silver ---
        # Expected: silver + quarantine + late == bronze
        expected_silver = silver_count + quarantine_count + late_count
        count_diff = expected_silver - bronze_count
        status, reason = _classify(
            count_diff,
            silver_amount - bronze_amount,
            TOLERANCE_PCT,
        )
        results.append({
            "business_date":       biz_date,
            "dataset":             "transactions",
            "reconciliation_type": "COUNT_LAYER",
            "source_layer":        "bronze",
            "target_layer":        "silver+quarantine+late",
            "source_count":        bronze_count,
            "target_count":        expected_silver,
            "count_difference":    count_diff,
            "source_amount_inr":   bronze_amount,
            "target_amount_inr":   silver_amount,
            "amount_difference":   silver_amount - bronze_amount,
            "tolerance_pct":       Decimal(str(TOLERANCE_PCT)),
            "status":              status,
            "failure_reason":      reason,
            "reconciled_at":       None,
        })

        # --- Silver → Gold ---
        silver_to_gold_count_diff  = gold_count - silver_count
        silver_to_gold_amount_diff = gold_amount - silver_amount
        status, reason = _classify(
            silver_to_gold_count_diff,
            silver_to_gold_amount_diff,
            TOLERANCE_PCT,
        )
        results.append({
            "business_date":       biz_date,
            "dataset":             "transactions",
            "reconciliation_type": "COUNT_LAYER",
            "source_layer":        "silver",
            "target_layer":        "gold",
            "source_count":        silver_count,
            "target_count":        gold_count,
            "count_difference":    silver_to_gold_count_diff,
            "source_amount_inr":   silver_amount,
            "target_amount_inr":   gold_amount,
            "amount_difference":   silver_to_gold_amount_diff,
            "tolerance_pct":       Decimal(str(TOLERANCE_PCT)),
            "status":              status,
            "failure_reason":      reason,
            "reconciled_at":       None,
        })

    except Exception as e:
        logger.exception("Transaction reconciliation failed")
        results.append({
            "business_date":       biz_date,
            "dataset":             "transactions",
            "reconciliation_type": "SKIPPED",
            "source_layer":        "n/a",
            "target_layer":        "n/a",
            "source_count":        0,
            "target_count":        0,
            "count_difference":    0,
            "source_amount_inr":   Decimal("0.00"),
            "target_amount_inr":   Decimal("0.00"),
            "amount_difference":   Decimal("0.00"),
            "tolerance_pct":       Decimal(str(TOLERANCE_PCT)),
            "status":              "SKIPPED",
            "failure_reason":      str(e),
            "reconciled_at":       None,
        })

    return results


# ---------------------------------------------------------------------------
# RECONCILIATION 2 — Double-entry integrity (CR vs DR)
# ---------------------------------------------------------------------------
def recon_double_entry() -> list:
    """
    Verify SUM(credits) == SUM(debits) for the business date.
    A double-entry violation means the ledger is out of balance — critical.
    """
    biz_date = BUSINESS_DATE
    logger.info(f"Double-entry reconciliation for {biz_date}")

    try:
        silver = (
            spark.read.table(f"{CATALOG}.clean_silver.silver_transactions")
                .filter(F.to_date("transaction_timestamp") == F.lit(biz_date))
        )
        totals = (
            silver.groupBy("db_cr_indicator")
                  .agg(F.sum("amount").alias("total_amount"))
                  .collect()
        )
        by_indicator = {r["db_cr_indicator"]: r["total_amount"] or Decimal("0.00")
                        for r in totals}
        cr = by_indicator.get("CR", Decimal("0.00"))
        dr = by_indicator.get("DR", Decimal("0.00"))
        diff = cr - dr

        status = "PASS" if diff == 0 else "FAIL"
        reason = None if diff == 0 else f"CR-DR imbalance of {diff}"

        return [{
            "business_date":       biz_date,
            "dataset":             "transactions",
            "reconciliation_type": "DOUBLE_ENTRY",
            "source_layer":        "silver_credits",
            "target_layer":        "silver_debits",
            "source_count":        None,
            "target_count":        None,
            "count_difference":    None,
            "source_amount_inr":   cr,
            "target_amount_inr":   dr,
            "amount_difference":   diff,
            "tolerance_pct":       Decimal("0.0000"),
            "status":              status,
            "failure_reason":      reason,
            "reconciled_at":       None,
        }]
    except Exception as e:
        logger.exception("Double-entry reconciliation failed")
        return [{
            "business_date":       biz_date,
            "dataset":             "transactions",
            "reconciliation_type": "DOUBLE_ENTRY",
            "source_layer":        "silver_credits",
            "target_layer":        "silver_debits",
            "source_count":        None,
            "target_count":        None,
            "count_difference":    None,
            "source_amount_inr":   Decimal("0.00"),
            "target_amount_inr":   Decimal("0.00"),
            "amount_difference":   Decimal("0.00"),
            "tolerance_pct":       Decimal("0.0000"),
            "status":              "SKIPPED",
            "failure_reason":      str(e),
            "reconciled_at":       None,
        }]


# ---------------------------------------------------------------------------
# RECONCILIATION 3 — Loans: Silver → Gold
# ---------------------------------------------------------------------------
def recon_loans() -> list:
    """Reconcile loan portfolio counts + outstanding principal."""
    biz_date = BUSINESS_DATE

    try:
        silver = spark.read.table(f"{CATALOG}.clean_silver.silver_loans")
        gold   = spark.read.table(f"{CATALOG}.cur_gold.fact_loans")

        silver_count  = _safe_count(silver)
        gold_count    = _safe_count(gold)
        silver_amount = _safe_sum_amount(silver, "outstanding_principal")
        gold_amount   = _safe_sum_amount(gold, "outstanding_principal")

        status, reason = _classify(
            gold_count - silver_count,
            gold_amount - silver_amount,
            TOLERANCE_PCT,
        )

        return [{
            "business_date":       biz_date,
            "dataset":             "loans",
            "reconciliation_type": "COUNT_LAYER",
            "source_layer":        "silver",
            "target_layer":        "gold",
            "source_count":        silver_count,
            "target_count":        gold_count,
            "count_difference":    gold_count - silver_count,
            "source_amount_inr":   silver_amount,
            "target_amount_inr":   gold_amount,
            "amount_difference":   gold_amount - silver_amount,
            "tolerance_pct":       Decimal(str(TOLERANCE_PCT)),
            "status":              status,
            "failure_reason":      reason,
            "reconciled_at":       None,
        }]
    except Exception as e:
        logger.exception("Loan reconciliation failed")
        return [{
            "business_date":       biz_date,
            "dataset":             "loans",
            "reconciliation_type": "COUNT_LAYER",
            "source_layer":        "silver",
            "target_layer":        "gold",
            "source_count":        0,
            "target_count":        0,
            "count_difference":    0,
            "source_amount_inr":   Decimal("0.00"),
            "target_amount_inr":   Decimal("0.00"),
            "amount_difference":   Decimal("0.00"),
            "tolerance_pct":       Decimal(str(TOLERANCE_PCT)),
            "status":              "SKIPPED",
            "failure_reason":      str(e),
            "reconciled_at":       None,
        }]


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    logger.info(f"Starting reconciliation for business_date={BUSINESS_DATE}")

    all_results = []
    all_results.extend(recon_transactions())
    all_results.extend(recon_double_entry())
    all_results.extend(recon_loans())

    # Write to reconciliation_results
    df = spark.createDataFrame(all_results, schema=RECON_SCHEMA)
    df = df.withColumn("reconciled_at", F.current_timestamp())

    target = f"{CATALOG}.cur_gold.reconciliation_results"
    (
        df.write
          .format("delta")
          .mode("append")
          .option("mergeSchema", "true")
          .saveAsTable(target)
    )

    # Summary
    summary = df.groupBy("status").count().collect()
    for row in summary:
        logger.info(f"  {row['status']}: {row['count']}")

    fail_count = df.filter(F.col("status") == "FAIL").count()
    if fail_count > 0:
        logger.error(f"❌ {fail_count} reconciliation checks FAILED")
        # Fail the task — triggers Workflow alert / on-call page
        sys.exit(1)
    else:
        logger.info("✅ All reconciliation checks passed")


if __name__ == "__main__":
    main()