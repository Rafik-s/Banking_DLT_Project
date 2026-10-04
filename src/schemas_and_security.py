"""
MODULE: SCHEMAS & ENVIRONMENT CONFIGURATION (DLT-Native)

Strict, fail-fast config parsing via dlt.config.get().
Explicit schemas for all 10 banking domain datasets.
"""

import dlt
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType,
    TimestampType, DateType, IntegerType
)

# ---------------------------------------------------------------------------
# STRICT CONFIG PARSING — NO DEFAULTS, FAIL FAST
# ---------------------------------------------------------------------------
REQUIRED_KEYS = [
    "vars.catalog",
    "vars.bronze_schema",
    "vars.silver_schema",
    "vars.gold_schema",
    "vars.raw_base_path",
    "vars.checkpoint_dir",
    "vars.pii_secret_scope",
    "vars.pii_secret_key",
]

CONFIG = {k: dlt.config.get(k) for k in REQUIRED_KEYS}
missing_keys = [k for k, v in CONFIG.items() if not v]
if missing_keys:
    raise ValueError(
        f"CRITICAL: Missing required DLT configuration parameters: {missing_keys}. "
        f"Set these in the DAB pipeline resource under `configuration:`."
    )

CATALOG          = CONFIG["vars.catalog"]
BRONZE_SCHEMA    = CONFIG["vars.bronze_schema"]
SILVER_SCHEMA    = CONFIG["vars.silver_schema"]
GOLD_SCHEMA      = CONFIG["vars.gold_schema"]
RAW_BASE_PATH    = CONFIG["vars.raw_base_path"]
CHECKPOINT_DIR   = CONFIG["vars.checkpoint_dir"]
PII_SECRET_SCOPE = CONFIG["vars.pii_secret_scope"]
PII_SECRET_KEY   = CONFIG["vars.pii_secret_key"]


# ---------------------------------------------------------------------------
# EXPLICIT SCHEMAS — 10 CORE BANKING DATASETS
# ---------------------------------------------------------------------------

CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id",        StringType(),  False),
    StructField("full_name",          StringType(),  True),
    StructField("customer_type",      StringType(),  True),
    StructField("customer_segment",   StringType(),  True),
    StructField("aadhaar_number",     StringType(),  True),
    StructField("pan_number",         StringType(),  True),
    StructField("phone",              StringType(),  True),
    StructField("email",              StringType(),  True),
    StructField("city",               StringType(),  True),
    StructField("state",              StringType(),  True),
    StructField("pincode",            StringType(),  True),
    StructField("kyc_status",         StringType(),  True),
    StructField("customer_status",    StringType(),  True),
    StructField("last_modified_date", TimestampType(), True),
])

ACCOUNTS_SCHEMA = StructType([
    StructField("account_id",         StringType(),   False),
    StructField("customer_id",        StringType(),   False),
    StructField("branch_id",          StringType(),   True),
    StructField("account_type",       StringType(),   True),
    StructField("currency",           StringType(),   True),
    StructField("balance",            DecimalType(18, 2), True),
    StructField("account_status",     StringType(),   True),
    StructField("opening_date",       DateType(),     True),
    StructField("last_modified_date", TimestampType(), True),
])

TRANSACTIONS_SCHEMA = StructType([
    StructField("transaction_id",          StringType(),   False),
    StructField("account_id",              StringType(),   False),
    StructField("customer_id",             StringType(),   False),
    StructField("transaction_type",        StringType(),   True),
    StructField("channel",                 StringType(),   True),
    StructField("amount",                  DecimalType(18, 2), True),
    StructField("db_cr_indicator",         StringType(),   True),
    StructField("transaction_status",      StringType(),   True),
    StructField("iso_8583_response_code",  StringType(),   True),
    StructField("transaction_timestamp",   TimestampType(), True),
    # Idempotency columns (Workstream 2)
    StructField("source_system",           StringType(),   True),   # e.g. CORE_BANKING, UPI, NEFT
    StructField("event_version",           IntegerType(),  True),   # CDC sequence; default 1

])

BRANCHES_SCHEMA = StructType([
    StructField("branch_id",        StringType(),   False),
    StructField("ifsc_code",        StringType(),   False),
    StructField("branch_name",      StringType(),   True),
    StructField("branch_category",  StringType(),   True),
    StructField("region",           StringType(),   True),
    StructField("city",             StringType(),   True),
    StructField("state",            StringType(),   True),
    StructField("pincode",          StringType(),   True),
    StructField("cash_vault_limit", DecimalType(18, 2), True),
    StructField("branch_status",    StringType(),   True),
    StructField("opening_date",     DateType(),     True),
])

EMPLOYEES_SCHEMA = StructType([
    StructField("employee_id",     StringType(),   False),
    StructField("branch_id",       StringType(),   True),
    StructField("full_name",       StringType(),   True),
    StructField("department",      StringType(),   True),
    StructField("role",            StringType(),   True),
    StructField("salary_annual",   DecimalType(18, 2), True),
    StructField("email",           StringType(),   True),
    StructField("phone",           StringType(),   True),
    StructField("hire_date",       DateType(),     True),
    StructField("employee_status", StringType(),   True),
])

CREDIT_CARDS_SCHEMA = StructType([
    StructField("card_id",             StringType(),   False),
    StructField("customer_id",         StringType(),   False),
    StructField("account_id",          StringType(),   True),
    StructField("card_number_raw",     StringType(),   True),
    StructField("card_variant",        StringType(),   True),
    StructField("credit_limit",        DecimalType(18, 2), True),
    StructField("outstanding_balance", DecimalType(18, 2), True),
    StructField("available_limit",     DecimalType(18, 2), True),
    StructField("card_status",         StringType(),   True),
    StructField("issue_date",          DateType(),     True),
    StructField("expiry_date",         DateType(),     True),
])

LOANS_SCHEMA = StructType([
    StructField("loan_id",                StringType(),   False),
    StructField("customer_id",            StringType(),   False),
    StructField("branch_id",              StringType(),   True),
    StructField("loan_type",              StringType(),   True),
    StructField("sanctioned_amount",      DecimalType(18, 2), True),
    StructField("emi_amount",             DecimalType(18, 2), True),
    StructField("outstanding_principal",  DecimalType(18, 2), True),
    StructField("interest_rate",          DecimalType(5, 2),  True),
    StructField("tenure_months",          IntegerType(),  True),
    StructField("dpd",                    IntegerType(),  True),
    StructField("loan_status",            StringType(),   True),
    StructField("disbursement_date",      DateType(),     True),
])

KYC_DOCUMENTS_SCHEMA = StructType([
    StructField("kyc_id",                  StringType(), False),
    StructField("customer_id",             StringType(), False),
    StructField("document_type",           StringType(), True),
    StructField("document_number_raw",     StringType(), True),
    StructField("verification_status",     StringType(), True),
    StructField("verified_by_employee_id", StringType(), True),
    StructField("submission_date",         DateType(),   True),
    StructField("expiry_date",             DateType(),   True),
])

FRAUD_ALERTS_SCHEMA = StructType([
    StructField("alert_id",                  StringType(),  False),
    StructField("transaction_id",            StringType(),  True),
    StructField("customer_id",               StringType(),  True),
    StructField("card_id",                   StringType(),  True),
    StructField("alert_type",                StringType(),  True),
    StructField("risk_score",                IntegerType(), True),
    StructField("risk_level",                StringType(),  True),
    StructField("resolution_status",         StringType(),  True),
    StructField("action_taken",              StringType(),  True),
    StructField("investigator_employee_id",  StringType(),  True),
    StructField("alert_timestamp",           TimestampType(), True),
])

ATM_TRANSACTIONS_SCHEMA = StructType([
    StructField("atm_tx_id",             StringType(),   False),
    StructField("atm_id",                StringType(),   True),
    StructField("card_id",               StringType(),   True),
    StructField("account_id",            StringType(),   True),
    StructField("transaction_type",      StringType(),   True),
    StructField("amount",                DecimalType(18, 2), True),
    StructField("surcharge_fee",         DecimalType(18, 2), True),
    StructField("response_code",         StringType(),   True),
    StructField("location_city",         StringType(),   True),
    StructField("transaction_timestamp", TimestampType(), True),
])