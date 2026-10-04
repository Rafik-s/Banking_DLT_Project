"""
MODULE: SILVER TRANSFORMATION

Cleansing, watermarking, PII masking, referential integrity.

PII masking strategy (see docs/SECURITY_BOUNDARY.md):
  - Email    : HMAC-SHA256 for deterministic matching + display mask
  - Phone    : display mask only (last 5 digits) + HMAC for matching
  - Aadhaar  : HMAC-SHA256 + display mask (last 4)
  - PAN      : HMAC-SHA256 + display mask (first 5, last 1)
  - Card     : PCI-DSS-ALIGNED first-6 + last-4 (NOT a PCI compliance claim)
  - Raw PII  : dropped from schema after transformation
"""

import dlt
from pyspark.sql import functions as F

from schemas_and_security import CATALOG, BRONZE_SCHEMA, SILVER_SCHEMA


SILVER_PROPS = {
    "quality": "silver",
    "delta.enableChangeDataFeed": "true",
}


# ===========================================================================
# HELPER: display-mask functions (pure, deterministic, no secrets)
# ===========================================================================
def _mask_email(email_col):
    """
    Display mask for email. Preserves first char + domain for readability.
    Example: john.smith@gmail.com -> j*********@gmail.com
    """
    return F.when(
        email_col.isNull() | (F.length(email_col) < 3),
        F.lit("***@***"),
    ).otherwise(
        F.concat(
            F.substring(email_col, 1, 1),
            F.lit("*********"),
            F.lit("@"),
            F.regexp_extract(email_col, "@(.+)$", 1),
        )
    )


def _mask_phone(phone_col):
    """
    Display mask for phone. Preserves last 5 digits.
    Example: +919876543210 -> +91-XXXXX-43210
    """
    return F.when(
        phone_col.isNull() | (F.length(phone_col) < 5),
        F.lit("+91-XXXXX-00000"),
    ).otherwise(
        F.concat(
            F.lit("+91-XXXXX-"),
            F.substring(phone_col, -5, 5),
        )
    )


def _mask_aadhaar(aadhaar_col):
    """
    Display mask for Aadhaar. Preserves last 4.
    Example: 123456789012 -> XXXX-XXXX-9012
    """
    return F.when(
        F.length(aadhaar_col) == 12,
        F.concat(F.lit("XXXX-XXXX-"), F.substring(aadhaar_col, -4, 4)),
    ).otherwise(F.lit("XXXX-XXXX-0000"))


def _mask_pan(pan_col):
    """
    Display mask for PAN. Preserves first 5 + last 1.
    Example: ABCDE1234F -> ABCDE****F
    """
    return F.when(
        F.length(pan_col) == 10,
        F.concat(
            F.substring(pan_col, 1, 5),
            F.lit("****"),
            F.substring(pan_col, -1, 1),
        ),
    ).otherwise(F.lit("ABCDE****F"))


def _mask_card_number(card_col):
    """
    Display mask for card number: first 6 (BIN) + last 4.
    NOTE: This is PCI-DSS-ALIGNED masking, not a PCI-DSS compliance claim.
    Full PCI compliance requires the complete control environment —
    see docs/SECURITY_BOUNDARY.md.
    """
    return F.when(
        F.length(card_col) >= 10,
        F.concat(
            F.substring(card_col, 1, 6),
            F.lit("******"),
            F.substring(card_col, -4, 4),
        ),
    ).otherwise(F.lit("XXXXXX******XXXX"))


# ===========================================================================
# SILVER CUSTOMERS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_customers",
    comment="Cleansed customers with UC-HMAC hashed and display-masked PII.",
    table_properties=SILVER_PROPS,
)
@dlt.expect_or_fail("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_fail("valid_record_updated_at", "_record_updated_at IS NOT NULL")
@dlt.expect_or_drop("valid_kyc_status",
    "kyc_status IN ('VERIFIED', 'PENDING_REKYC', 'REJECTED', 'IN_PROGRESS')")
@dlt.expect_or_drop("valid_customer_status",
    "customer_status IN ('ACTIVE', 'DORMANT', 'CLOSED')")
def silver_customers():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_customers")
            .withColumn("full_name", F.initcap(F.trim("full_name")))
            .withColumn("city",  F.upper(F.trim("city")))
            .withColumn("state", F.upper(F.trim("state")))

            # HMAC (deterministic matching key — not reversible)
            .withColumn("aadhaar_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(aadhaar_number)"))
            .withColumn("pan_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(pan_number)"))
            .withColumn("email_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(lower(trim(email)))"))
            .withColumn("phone_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(regexp_replace(phone, '[^0-9]', ''))"))

            # Display masks (for human readability)
            .withColumn("aadhaar_masked", _mask_aadhaar(F.col("aadhaar_number")))
            .withColumn("pan_masked",     _mask_pan(F.col("pan_number")))
            .withColumn("email_masked",   _mask_email(F.lower(F.trim("email"))))
            .withColumn("phone_masked",   _mask_phone(F.col("phone")))

            # Drop raw PII — never persisted past Silver
            .drop("aadhaar_number", "pan_number", "phone", "email")

            .withColumn("_record_updated_at",
                F.coalesce(F.col("last_modified_date"),
                           F.col("_ingestion_timestamp")))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER ACCOUNTS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_accounts",
    comment="Cleansed accounts — source for SCD2 account dimension.",
    table_properties=SILVER_PROPS,
)
@dlt.expect_or_fail("valid_account_id", "account_id IS NOT NULL")
@dlt.expect_or_fail("valid_customer_fk", "customer_id IS NOT NULL")
@dlt.expect_or_fail("valid_record_updated_at", "_record_updated_at IS NOT NULL")
@dlt.expect_or_drop("non_negative_balance", "current_balance >= 0.00")
@dlt.expect_or_drop("valid_account_type",
    "account_type IN ('SAVINGS', 'CURRENT', 'FD', 'RD', 'NRI')")
def silver_accounts():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_accounts")
            .withColumnRenamed("balance", "current_balance")
            .withColumn("current_balance",
                F.col("current_balance").cast("decimal(18,2)"))
            .withColumn("account_type",   F.upper(F.trim("account_type")))
            .withColumn("account_status",
                F.coalesce(F.upper(F.trim("account_status")), F.lit("ACTIVE")))
            .withColumn("currency",
                F.coalesce(F.upper(F.trim("currency")), F.lit("INR")))
            .withColumn("_record_updated_at",
                F.coalesce(F.col("last_modified_date"),
                           F.col("_ingestion_timestamp")))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER TRANSACTIONS (Watermarked, deduplicated)
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions",
    comment="Cleansed transactions — 24h event-time watermark, deduped within window.",
    table_properties=SILVER_PROPS,
)
@dlt.expect_or_fail("valid_transaction_id",        "transaction_id IS NOT NULL")
@dlt.expect_or_fail("valid_account_fk",            "account_id IS NOT NULL")
@dlt.expect_or_fail("valid_transaction_timestamp", "transaction_timestamp IS NOT NULL")
@dlt.expect_or_drop("valid_amount_range",
    "amount > 0.00 AND amount <= 10000000.00")
@dlt.expect_or_drop("valid_db_cr_indicator",
    "db_cr_indicator IN ('CR', 'DR')")
def silver_transactions():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_transactions")
            .withWatermark("transaction_timestamp", "24 hours")
            .dropDuplicatesWithinWatermark(["transaction_id"])
            .withColumn("transaction_type", F.upper(F.trim("transaction_type")))
            .withColumn("channel",          F.upper(F.trim("channel")))
            .withColumn("iso_8583_response_code",
                F.coalesce(F.col("iso_8583_response_code"), F.lit("00")))
            .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
            .withColumn("transaction_timestamp",
                F.to_timestamp("transaction_timestamp"))
            .withColumn("_record_updated_at",
                F.coalesce(F.col("_ingestion_timestamp"),
                           F.col("transaction_timestamp")))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER BRANCHES
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_branches",
    comment="Cleansed branch master data.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_branch_id", "branch_id IS NOT NULL")
@dlt.expect_or_drop("valid_ifsc_format",
    "ifsc_code RLIKE '^[A-Z]{4}0[A-Z0-9]{6}$'")
def silver_branches():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_branches")
            .withColumn("branch_name", F.initcap(F.trim("branch_name")))
            .withColumn("city",        F.upper(F.trim("city")))
            .withColumn("state",       F.upper(F.trim("state")))
            .withColumn("region",      F.upper(F.trim("region")))
            .withColumn("ifsc_code",   F.upper(F.trim("ifsc_code")))
            .withColumn("cash_vault_limit",
                F.col("cash_vault_limit").cast("decimal(18,2)"))
            # Source-event time for SCD2 (fallback to ingestion time if missing)
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER EMPLOYEES  (PII masking corrected)
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_employees",
    comment="Cleansed employee master with masked PII.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_employee_id", "employee_id IS NOT NULL")
@dlt.expect_or_drop("valid_department",
    "department IN ('RETAIL_BANKING', 'LOANS', 'FRAUD_OPS', 'COMPLIANCE', 'IT')")
def silver_employees():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_employees")
            .withColumn("full_name",  F.initcap(F.trim("full_name")))
            .withColumn("department", F.upper(F.trim("department")))
            .withColumn("role",       F.upper(F.trim("role")))

            # HMAC for deterministic matching
            .withColumn("email_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(lower(trim(email)))"))
            .withColumn("phone_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(regexp_replace(phone, '[^0-9]', ''))"))

            # Display masks
            .withColumn("email_masked", _mask_email(F.lower(F.trim("email"))))
            .withColumn("phone_masked", _mask_phone(F.col("phone")))

            # Drop raw PII
            .drop("phone", "email")

            .withColumn("salary_annual",
                F.col("salary_annual").cast("decimal(18,2)"))
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER CREDIT CARDS  (PCI-DSS-ALIGNED masking wording)
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_credit_cards",
    comment="Cleansed credit card portfolio (PCI-DSS-ALIGNED PAN masking).",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_card_id", "card_id IS NOT NULL")
@dlt.expect_or_drop("valid_card_limits", "credit_limit >= outstanding_balance")
def silver_credit_cards():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_credit_cards")
            .withColumn("card_variant", F.upper(F.trim("card_variant")))
            .withColumn("card_status",  F.upper(F.trim("card_status")))

            # PAN masking (first 6 + last 4) — PCI-DSS-ALIGNED
            .withColumn("card_number_masked",
                _mask_card_number(F.col("card_number_raw")))
            # HMAC for deterministic matching without storing PAN
            .withColumn("card_number_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(card_number_raw)"))
            .drop("card_number_raw")

            .withColumn("credit_limit",
                F.col("credit_limit").cast("decimal(18,2)"))
            .withColumn("outstanding_balance",
                F.col("outstanding_balance").cast("decimal(18,2)"))
            .withColumn("available_limit",
                (F.col("credit_limit") - F.col("outstanding_balance"))
                    .cast("decimal(18,2)"))
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER LOANS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_loans",
    comment="Cleansed loan portfolio.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_loan_id", "loan_id IS NOT NULL")
@dlt.expect_or_drop("valid_dpd_range", "dpd >= 0 AND dpd <= 3600")
def silver_loans():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_loans")
            .withColumn("loan_type",   F.upper(F.trim("loan_type")))
            .withColumn("loan_status", F.upper(F.trim("loan_status")))
            .withColumn("sanctioned_amount",
                F.col("sanctioned_amount").cast("decimal(18,2)"))
            .withColumn("emi_amount",
                F.col("emi_amount").cast("decimal(18,2)"))
            .withColumn("outstanding_principal",
                F.col("outstanding_principal").cast("decimal(18,2)"))
            .withColumn("dpd", F.col("dpd").cast("integer"))
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER KYC DOCUMENTS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_kyc_documents",
    comment="Cleansed KYC documents — document numbers HMAC'd.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_kyc_id", "kyc_id IS NOT NULL")
@dlt.expect_or_drop("valid_document_type",
    "document_type IN ('AADHAAR', 'PAN', 'PASSPORT', 'VOTER_ID', 'DRIVING_LICENSE')")
def silver_kyc_documents():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_kyc_documents")
            .withColumn("document_type",
                F.upper(F.trim("document_type")))
            .withColumn("verification_status",
                F.upper(F.trim("verification_status")))
            .withColumn("doc_number_sha256",
                F.expr(f"{CATALOG}.security.pii_hmac(document_number_raw)"))
            .drop("document_number_raw")
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER FRAUD ALERTS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_fraud_alerts",
    comment="Cleansed fraud alerts.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_alert_id", "alert_id IS NOT NULL")
@dlt.expect_or_drop("valid_risk_level",
    "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
@dlt.expect_or_drop("valid_risk_score",
    "risk_score >= 0 AND risk_score <= 100")
def silver_fraud_alerts():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_fraud_alerts")
            .withColumn("alert_type",        F.upper(F.trim("alert_type")))
            .withColumn("risk_level",        F.upper(F.trim("risk_level")))
            .withColumn("resolution_status", F.upper(F.trim("resolution_status")))
            .withColumn("risk_score",        F.col("risk_score").cast("integer"))
            .withColumn("alert_timestamp",   F.to_timestamp("alert_timestamp"))
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# SILVER ATM TRANSACTIONS
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_atm_transactions",
    comment="Cleansed ATM terminal transactions.",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_fail("valid_atm_tx_id", "atm_tx_id IS NOT NULL")
@dlt.expect_or_drop("valid_atm_amount",
    "amount > 0.00 AND amount <= 100000.00")
def silver_atm_transactions():
    return (
        dlt.read_stream(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_atm_transactions")
            .withColumn("transaction_type", F.upper(F.trim("transaction_type")))
            .withColumn("location_city",    F.upper(F.trim("location_city")))
            .withColumn("amount",           F.col("amount").cast("decimal(18,2)"))
            .withColumn("surcharge_fee",    F.col("surcharge_fee").cast("decimal(18,2)"))
            .withColumn("transaction_timestamp",
                F.to_timestamp("transaction_timestamp"))
            .withColumn("_record_updated_at", F.col("_ingestion_timestamp"))
            .withColumn("_updated_timestamp", F.current_timestamp())
    )


# ===========================================================================
# REFERENTIAL INTEGRITY — QUARANTINE + VALIDATED
# ===========================================================================
@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions_quarantine",
    comment="Orphaned transactions — account_id not found within 30-day window.",
    table_properties={"quality": "silver"},
)
def silver_transactions_quarantine():
    txn = (
        dlt.read_stream(f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions")
            .withWatermark("transaction_timestamp", "24 hours")
            .alias("t")
    )
    acc = (
        dlt.read_stream(f"{CATALOG}.{SILVER_SCHEMA}.silver_accounts")
            .withWatermark("_record_updated_at", "30 days")
            .select("account_id", "_record_updated_at")
            .alias("a")
    )
    return (
        txn.join(
            acc,
            F.expr("""
                t.account_id = a.account_id
                AND a._record_updated_at BETWEEN
                    t.transaction_timestamp - INTERVAL 30 DAYS
                    AND t.transaction_timestamp + INTERVAL 30 DAYS
            """),
            "left_anti",
        ).select("t.*")
    )


@dlt.table(
    name=f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions_validated",
    comment="Transactions with referential integrity verified.",
    table_properties={"quality": "silver"},
)
def silver_transactions_validated():
    txn = (
        dlt.read_stream(f"{CATALOG}.{SILVER_SCHEMA}.silver_transactions")
            .withWatermark("transaction_timestamp", "24 hours")
            .alias("t")
    )
    acc = (
        dlt.read_stream(f"{CATALOG}.{SILVER_SCHEMA}.silver_accounts")
            .withWatermark("_record_updated_at", "7 days")
            .select("account_id", "_record_updated_at")
            .alias("a")
    )
    return (
        txn.join(
            acc,
            F.expr("""
                t.account_id = a.account_id
                AND a._record_updated_at BETWEEN
                    t.transaction_timestamp - INTERVAL 7 DAYS
                    AND t.transaction_timestamp + INTERVAL 7 DAYS
            """),
            "inner",
        ).select("t.*")
    )