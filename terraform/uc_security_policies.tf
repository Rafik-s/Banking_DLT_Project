# ============================================================================
# UNITY CATALOG SECURITY BOOTSTRAP
# Runs on `terraform apply` via databricks_sql_exec.
# ============================================================================

# ----------------------------------------------------------------------------
# 1. SECURITY SCHEMA + PII HMAC FUNCTION
# ----------------------------------------------------------------------------
resource "databricks_sql_exec" "uc_security_functions" {
  warehouse_id = var.sql_warehouse_id

  sql = <<SQL
    -- Security schema (holds all UC functions)
    CREATE SCHEMA IF NOT EXISTS ${var.catalog_name}.security
      COMMENT 'Security functions and access controls — do not drop.';

    -- HMAC function — salt comes from a Databricks Secret Scope backed by Azure Key Vault.
    -- The salt is NEVER exposed to end users. Only callers with EXECUTE grant can use it.
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.pii_hmac(input STRING)
    RETURNS STRING
    COMMENT 'HMAC-SHA256 of PII input using the environment salt. Deterministic, non-reversible.'
    RETURN
      CASE
        WHEN input IS NULL THEN NULL
        ELSE encode(
          hmac(input, secret('banking-pii-${var.env}', 'salt'), 'SHA256'),
          'hex'
        )
      END;

    -- Email display mask (readable partial)
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.mask_email(email STRING)
    RETURNS STRING
    COMMENT 'Display mask for email: preserves first char + domain.'
    RETURN CASE
      WHEN email IS NULL OR length(email) < 3 THEN '***@***'
      WHEN is_account_group_member('fraud_investigators')
        OR is_account_group_member('data_admins')
        OR is_account_group_member('compliance_auditors')
      THEN email
      ELSE concat(substring(email, 1, 1), '*********@', regexp_extract(email, '@(.+)$', 1))
    END;

    -- Card-number display mask (PCI-DSS-ALIGNED — first 6 + last 4)
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.mask_card(card_number STRING)
    RETURNS STRING
    COMMENT 'Display mask for PAN: first 6 (BIN) + last 4. NOT a PCI compliance claim.'
    RETURN CASE
      WHEN card_number IS NULL OR length(card_number) < 10 THEN 'XXXXXX******XXXX'
      WHEN is_account_group_member('card_ops_level2')
        OR is_account_group_member('data_admins')
      THEN card_number
      ELSE concat('XXXXXX******', right(card_number, 4))
    END;

    -- Branch row-level filter — joins a mapping table
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.branch_row_filter(branch_id STRING)
    RETURNS BOOLEAN
    COMMENT 'Restricts access to rows matching the user branch mapping.'
    RETURN
      is_account_group_member('executive_board')
      OR is_account_group_member('compliance_auditors')
      OR is_account_group_member('data_admins')
      OR branch_id IN (
          SELECT mapped_branch_id
          FROM ${var.catalog_name}.security.user_branch_mapping
          WHERE user_email = current_user()
      );

    -- ==========================================================================
    -- EXPLICIT EXECUTE GRANTS on security.pii_hmac
    -- By default, PUBLIC can EXECUTE functions in Unity Catalog.
    -- For PII, we REVOKE from PUBLIC and grant only to specific service principals.
    -- ==========================================================================
    REVOKE EXECUTE ON FUNCTION ${var.catalog_name}.security.pii_hmac FROM `account users`;

    GRANT EXECUTE ON FUNCTION ${var.catalog_name}.security.pii_hmac
      TO `data-platform-dlt-sp-${var.env}`;

    GRANT EXECUTE ON FUNCTION ${var.catalog_name}.security.pii_hmac
      TO `data-platform-admins`;

    -- ==========================================================================
    -- PII COLUMN TAGS ON BRONZE (evidence for DPDP / internal audit)
    -- ==========================================================================
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN aadhaar_number SET TAGS ('pii'='aadhaar', 'dpdp'='restricted', 'tier'='bronze-pii');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN pan_number SET TAGS ('pii'='pan', 'dpdp'='restricted', 'tier'='bronze-pii');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN email SET TAGS ('pii'='email', 'dpdp'='restricted', 'tier'='bronze-pii');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN phone SET TAGS ('pii'='phone', 'dpdp'='restricted', 'tier'='bronze-pii');

    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_credit_cards
      ALTER COLUMN card_number_raw SET TAGS ('pci'='pan', 'tier'='bronze-pci');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_kyc_documents
      ALTER COLUMN document_number_raw SET TAGS ('pii'='document', 'tier'='bronze-pii');

    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_employees
      ALTER COLUMN email SET TAGS ('pii'='email', 'tier'='bronze-pii');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_employees
      ALTER COLUMN phone SET TAGS ('pii'='phone', 'tier'='bronze-pii');
  SQL
}

# ----------------------------------------------------------------------------
# 2. DENY BROAD ACCESS TO BRONZE PII SCHEMA
# Bronze PII tables must only be readable by data_admins + the DLT SP.
# Everyone else (analysts, BI users, developers) must NOT have SELECT on raw_bronze.
# ----------------------------------------------------------------------------
resource "databricks_sql_exec" "bronze_pii_lockdown" {
  warehouse_id = var.sql_warehouse_id
  depends_on   = [databricks_sql_exec.uc_security_functions]

  sql = <<SQL
    -- Deny account users the ability to read raw_bronze
    REVOKE SELECT ON SCHEMA ${var.catalog_name}.raw_bronze FROM `account users`;

    -- Grant to the DLT service principal (writes Bronze) and platform admins
    GRANT USAGE  ON SCHEMA ${var.catalog_name}.raw_bronze TO `data-platform-dlt-sp-${var.env}`;
    GRANT SELECT ON SCHEMA ${var.catalog_name}.raw_bronze TO `data-platform-dlt-sp-${var.env}`;
    GRANT ALL PRIVILEGES ON SCHEMA ${var.catalog_name}.raw_bronze TO `data-platform-admins`;
  SQL
}

# ----------------------------------------------------------------------------
# 3. COLUMN MASKS ON SILVER PII (attach after tables exist)
# ----------------------------------------------------------------------------
resource "databricks_sql_exec" "uc_mask_attachments" {
  warehouse_id = var.sql_warehouse_id
  depends_on   = [databricks_sql_exec.uc_security_functions]

  sql = <<SQL
    ALTER TABLE IF EXISTS ${var.catalog_name}.clean_silver.silver_customers
      ALTER COLUMN email_masked SET MASK ${var.catalog_name}.security.mask_email;

    ALTER TABLE IF EXISTS ${var.catalog_name}.clean_silver.silver_credit_cards
      ALTER COLUMN card_number_masked SET MASK ${var.catalog_name}.security.mask_card;

    ALTER TABLE IF EXISTS ${var.catalog_name}.clean_silver.silver_accounts
      SET ROW FILTER ${var.catalog_name}.security.branch_row_filter ON (branch_id);
  SQL
}