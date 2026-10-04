"""
MODULE: GOLD DIMENSIONAL LAYER

Star schema with SCD Type 2 dimensions (via APPLY CHANGES) and
Liquid-Clustered fact tables.
"""

import dlt
from pyspark.sql import functions as F

from schemas_and_security import CATALOG, SILVER_SCHEMA, GOLD_SCHEMA


GOLD_PROPS_CDF = {
    "quality": "gold",
    "delta.enableChangeDataFeed": "true",
}
GOLD_PROPS = {"quality": "gold"}


# ===========================================================================
# DIM CUSTOMERS — SCD Type 2
# ===========================================================================
dlt.create_streaming_table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.dim_customers",
    comment="Customer dimension — SCD Type 2 with full regulatory lineage.",
    table_properties=GOLD_PROPS_CDF,
    cluster_by=["customer_id"],
)

dlt.apply_changes(
    target=f"{CATALOG}.{GOLD_SCHEMA}.dim_customers",
    source=f"{CATALOG}.{SILVER_SCHEMA}.silver_customers",
    keys=["customer_id"],
    sequence_by=F.col("_record_updated_at"),
    stored_as_scd_type=2,
    except_column_list=["_updated_timestamp", "_record_updated_at"],
)


# ===========================================================================
# DIM ACCOUNTS — SCD Type 2
# ===========================================================================
dlt.create_streaming_table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.dim_accounts",
    comment="Account dimension — SCD Type 2.",
    table_properties=GOLD_PROPS_CDF,
    cluster_by=["account_id", "customer_id"],
)

dlt.apply_changes(
    target=f"{CATALOG}.{GOLD_SCHEMA}.dim_accounts",
    source=f"{CATALOG}.{SILVER_SCHEMA}.silver_accounts",
    keys=["account_id"],
    sequence_by=F.col("_record_updated_at"),
    stored_as_scd_type=2,
    except_column_list=["_updated_timestamp", "_record_updated_at"],
)


# ===========================================================================
# DIM BRANCHES — SCD Type 2
# ===========================================================================
dlt.create_streaming_table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.dim_branches",
    comment="Branch dimension — SCD Type 2.",
    table_properties=GOLD_PROPS,
    cluster_by=["branch_id"],
)

dlt.apply_changes(
    target=f"{CATALOG}.{GOLD_SCHEMA}.dim_branches",
    source=f"{CATALOG}.{SILVER_SCHEMA}.silver_branches",
    keys=["branch_id"],
    sequence_by=F.col("_updated_timestamp"),
    stored_as_scd_type=2,
    except_column_list=["_updated_timestamp"],
)


# ===========================================================================
# DIM CREDIT CARDS — SCD Type 2
# ===========================================================================
dlt.create_streaming_table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.dim_credit_cards",
    comment="Credit card dimension — SCD Type 2.",
    table_properties=GOLD_PROPS,
    cluster_by=["card_id", "customer_id"],
)

dlt.apply_changes(
    target=f"{CATALOG}.{GOLD_SCHEMA}.dim_credit_cards",
    source=f"{CATALOG}.{SILVER_SCHEMA}.silver_credit_cards",
    keys=["card_id"],
    sequence_by=F.col("_updated_timestamp"),
    stored_as_scd_type=2,
    except_column_list=["_updated_timestamp"],
)


# ===========================================================================
# DIM DATE — Static calendar (2018–2030)
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.dim_date",
    comment="Calendar dimension for temporal rollups.",
    table_properties=GOLD_PROPS,
)
def dim_date():
    return (
        spark.range(0, 4748)  # 2018-01-01 .. 2030-12-31 inclusive
            .select(
                F.date_add(F.lit("2018-01-01"), F.col("id").cast("int"))
                 .alias("calendar_date")
            )
            .select(
                F.date_format("calendar_date", "yyyyMMdd").alias("date_key"),
                F.col("calendar_date"),
                F.year("calendar_date").alias("year"),
                F.quarter("calendar_date").alias("quarter"),
                F.month("calendar_date").alias("month"),
                F.date_format("calendar_date", "MMMM").alias("month_name"),
                F.dayofmonth("calendar_date").alias("day_of_month"),
                F.date_format("calendar_date", "EEEE").alias("day_name"),
                F.when(F.dayofweek("calendar_date").isin(1, 7), True)
                 .otherwise(False).alias("is_weekend"),
            )
    )


# ===========================================================================
# FACT TRANSACTIONS — Liquid Clustered
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.fact_transactions",
    comment="Core banking transaction fact table.",
    table_properties=GOLD_PROPS_CDF,
    cluster_by=["account_id", "date_key"],
)
def fact_transactions():
    txn  = dlt.read_stream(f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions_validated")
    acc  = dlt.read(f"{CATALOG}.{GOLD_SCHEMA}.dim_accounts").filter("__END_AT IS NULL")
    cust = dlt.read(f"{CATALOG}.{GOLD_SCHEMA}.dim_customers").filter("__END_AT IS NULL")

    return (
        txn.alias("t")
            .join(acc.alias("a"),  F.col("t.account_id")  == F.col("a.account_id"),  "left")
            .join(cust.alias("c"), F.col("t.customer_id") == F.col("c.customer_id"), "left")
            .select(
                F.col("t.transaction_id"),
                F.col("a.account_id"),
                F.col("c.customer_id"),
                F.col("a.__START_AT").alias("account_sk"),
                F.col("c.__START_AT").alias("customer_sk"),
                F.date_format(F.col("t.transaction_timestamp"), "yyyyMMdd")
                    .alias("date_key"),
                F.col("t.transaction_type"),
                F.col("t.channel"),
                F.col("t.amount"),
                F.col("t.db_cr_indicator"),
                F.col("t.transaction_status"),
                F.col("t.iso_8583_response_code"),
                F.col("t.transaction_timestamp"),
            )
    )


# ===========================================================================
# FACT LOANS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.fact_loans",
    comment="Loan portfolio fact table.",
    table_properties=GOLD_PROPS,
    cluster_by=["disbursement_date_key", "loan_type", "loan_status"],
)
def fact_loans():
    loans = dlt.read(f"{CATALOG}.{SILVER_SCHEMA}.silver_loans")
    cust  = dlt.read(f"{CATALOG}.{GOLD_SCHEMA}.dim_customers").filter("__END_AT IS NULL")

    return (
        loans.alias("l")
            .join(cust.alias("c"),
                  F.col("l.customer_id") == F.col("c.customer_id"), "left")
            .select(
                F.col("l.loan_id"),
                F.col("c.__START_AT").alias("customer_sk"),
                F.col("l.customer_id"),
                F.col("l.branch_id"),
                F.date_format(F.col("l.disbursement_date"), "yyyyMMdd")
                    .alias("disbursement_date_key"),
                F.col("l.loan_type"),
                F.col("l.sanctioned_amount"),
                F.col("l.emi_amount"),
                F.col("l.outstanding_principal"),
                F.col("l.dpd"),
                F.col("l.loan_status"),
            )
    )


# ===========================================================================
# FACT FRAUD ALERTS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{GOLD_SCHEMA}.fact_fraud_alerts",
    comment="Fraud alerts fact table.",
    table_properties=GOLD_PROPS,
    cluster_by=["alert_date_key", "risk_level", "alert_type"],
)
def fact_fraud_alerts():
    return (
        dlt.read(f"{CATALOG}.{SILVER_SCHEMA}.silver_fraud_alerts")
            .withColumn("alert_date_key",
                F.date_format(F.col("alert_timestamp"), "yyyyMMdd"))
            .select(
                "alert_id", "transaction_id", "customer_id", "card_id",
                "alert_date_key", "alert_type", "risk_score", "risk_level",
                "resolution_status", "action_taken",
                "investigator_employee_id", "alert_timestamp",
            )
    )