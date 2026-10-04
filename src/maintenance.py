"""
MODULE: MAINTENANCE
Runs OPTIMIZE / ANALYZE / VACUUM on Gold tables.
Executed as a Workflow task (NOT inside the DLT pipeline).
"""
import logging

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("banking.maintenance")


CATALOG     = spark.conf.get("catalog", "banking_prod_catalog")
GOLD_SCHEMA = spark.conf.get("gold_schema", "cur_gold")

TABLES = [
    "dim_customers",
    "dim_accounts",
    "dim_branches",
    "dim_credit_cards",
    "fact_transactions",
    "fact_loans",
    "fact_fraud_alerts",
]

VACUUM_RETAIN_HOURS = 720   # 30 days — regulatory retention window


def optimize_and_analyze(fqn: str) -> None:
    logger.info(f"OPTIMIZE {fqn}")
    spark.sql(f"OPTIMIZE {fqn}")
    logger.info(f"ANALYZE {fqn}")
    spark.sql(f"ANALYZE TABLE {fqn} COMPUTE STATISTICS FOR ALL COLUMNS")
    logger.info(f"Completed OPTIMIZE + ANALYZE for {fqn}")


def vacuum(fqn: str) -> None:
    # Set retention property BEFORE vacuum — must be >= VACUUM RETAIN
    spark.sql(
        f"ALTER TABLE {fqn} SET TBLPROPERTIES "
        f"('delta.deletedFileRetentionDuration' = '30 days')"
    )
    logger.info(f"VACUUM {fqn} RETAIN {VACUUM_RETAIN_HOURS} HOURS")
    spark.sql(f"VACUUM {fqn} RETAIN {VACUUM_RETAIN_HOURS} HOURS")
    logger.info(f"Completed VACUUM for {fqn}")


def main() -> None:
    for tbl in TABLES:
        fqn = f"{CATALOG}.{GOLD_SCHEMA}.{tbl}"
        try:
            optimize_and_analyze(fqn)
        except Exception:
            logger.exception(f"OPTIMIZE/ANALYZE failed for {fqn}")
            raise

    for tbl in TABLES:
        fqn = f"{CATALOG}.{GOLD_SCHEMA}.{tbl}"
        try:
            vacuum(fqn)
        except Exception:
            logger.exception(f"VACUUM failed for {fqn}")
            raise

    logger.info("Maintenance run completed successfully.")


if __name__ == "__main__":
    main()