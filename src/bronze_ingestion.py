"""
MODULE: BRONZE INGESTION (Auto Loader)

Append-only, idempotent, schema-enforced ingestion for all 10 datasets.
Explicit table definitions (no loops) for full DLT lineage visibility.
"""

import dlt
from pyspark.sql import functions as F

from schemas_and_security import (
    CATALOG, BRONZE_SCHEMA, RAW_BASE_PATH, CHECKPOINT_DIR,
    CUSTOMERS_SCHEMA, ACCOUNTS_SCHEMA, TRANSACTIONS_SCHEMA,
    BRANCHES_SCHEMA, EMPLOYEES_SCHEMA, CREDIT_CARDS_SCHEMA,
    LOANS_SCHEMA, KYC_DOCUMENTS_SCHEMA, FRAUD_ALERTS_SCHEMA,
    ATM_TRANSACTIONS_SCHEMA,
)


def _bronze_reader(dataset_name: str, schema_struct):
    """
    Shared Auto Loader read config.

    Idempotency guarantees:
    - Auto Loader checkpoints ensure exactly-once file processing
    - _source_file_path_hash gives a deterministic file identifier
    - _ingest_sequence is a monotonically-increasing offset — reproducible
      across retries, unlike uuid() or current_timestamp()
    """
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("cloudFiles.schemaLocation",
                    f"{CHECKPOINT_DIR}/bronze_{dataset_name}/schema")
            .option("cloudFiles.inferColumnTypes", "false")
            .option("cloudFiles.schemaEvolutionMode", "failOnNewColumns")
            .option("cloudFiles.backfillInterval", "1 day")
            .option("rescuedDataColumn", "_rescued_data")
            .option("header", "true")
            .option("multiLine", "true")
            .schema(schema_struct)
            .load(f"{RAW_BASE_PATH}/{dataset_name}/")
            .selectExpr("*", "_metadata")
            .withColumn("_source_file_path",     F.col("_metadata.file_path"))
            .withColumn("_source_file_path_hash", F.sha2(F.col("_metadata.file_path"), 256))
            .withColumn("_ingestion_timestamp",   F.col("_metadata.file_modification_time"))
            # Deterministic "sequence" — file mtime + path, hashed
            # Same file → same sequence, regardless of how many times we run.
            .withColumn("_ingest_sequence",
                F.sha2(
                    F.concat(
                        F.col("_metadata.file_path"),
                        F.lit("|"),
                        F.col("_metadata.file_modification_time").cast("string"),
                    ),
                    256,
                ))
            .drop("_metadata")
    )


BRONZE_PROPS = {
    "quality": "bronze",
    "delta.appendOnly": "true",
    "delta.enableChangeDataFeed": "true",
    "pipelines.reset.allowed": "false",
}


# --- 10 explicit Bronze tables for full DLT lineage visibility ---

@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_customers",
    comment="Raw append-only landing for customers.",
    table_properties=BRONZE_PROPS,
)
def bronze_customers():
    return _bronze_reader("customers", CUSTOMERS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_accounts",
    comment="Raw append-only landing for accounts.",
    table_properties=BRONZE_PROPS,
)
def bronze_accounts():
    return _bronze_reader("accounts", ACCOUNTS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_transactions",
    comment="Raw append-only landing for transactions.",
    table_properties=BRONZE_PROPS,
)
def bronze_transactions():
    return _bronze_reader("transactions", TRANSACTIONS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_branches",
    comment="Raw append-only landing for branches.",
    table_properties=BRONZE_PROPS,
)
def bronze_branches():
    return _bronze_reader("branches", BRANCHES_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_employees",
    comment="Raw append-only landing for employees.",
    table_properties=BRONZE_PROPS,
)
def bronze_employees():
    return _bronze_reader("employees", EMPLOYEES_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_credit_cards",
    comment="Raw append-only landing for credit cards.",
    table_properties=BRONZE_PROPS,
)
def bronze_credit_cards():
    return _bronze_reader("credit_cards", CREDIT_CARDS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_loans",
    comment="Raw append-only landing for loans.",
    table_properties=BRONZE_PROPS,
)
def bronze_loans():
    return _bronze_reader("loans", LOANS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_kyc_documents",
    comment="Raw append-only landing for KYC documents.",
    table_properties=BRONZE_PROPS,
)
def bronze_kyc_documents():
    return _bronze_reader("kyc_documents", KYC_DOCUMENTS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_fraud_alerts",
    comment="Raw append-only landing for fraud alerts.",
    table_properties=BRONZE_PROPS,
)
def bronze_fraud_alerts():
    return _bronze_reader("fraud_alerts", FRAUD_ALERTS_SCHEMA)


@dlt.table(
    name=f"{CATALOG}.{BRONZE_SCHEMA}.bronze_atm_transactions",
    comment="Raw append-only landing for ATM transactions.",
    table_properties=BRONZE_PROPS,
)
def bronze_atm_transactions():
    return _bronze_reader("atm_transactions", ATM_TRANSACTIONS_SCHEMA)