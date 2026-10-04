# ============================================================================
# UNITY CATALOG SECURITY BOOTSTRAP
# Uses databricks_sql_exec so the SQL runs on `terraform apply`.
# ============================================================================

resource "databricks_sql_exec" "uc_security_functions" {
  warehouse_id = var.sql_warehouse_id

  sql = <<SQL
    -- 1. Security schema
    CREATE SCHEMA IF NOT EXISTS ${var.catalog_name}.security;

    -- 2. HMAC function for PII hashing (salt via secret scope)
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.pii_hmac(input STRING)
    RETURNS STRING
    RETURN encode(
      hmac(input, secret('banking-pii-${var.env}', 'salt'), 'SHA256'),
      'hex'
    );

    -- 3. Dynamic email masking
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.mask_email(email STRING)
    RETURNS STRING
    RETURN CASE
      WHEN is_account_group_member('fraud_investigators')
        OR is_account_group_member('data_admins') THEN email
      ELSE regexp_replace(email, '(?<=.).(?=.*@)', '*')
    END;

    -- 4. Dynamic card-number masking
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.mask_card(card_number STRING)
    RETURNS STRING
    RETURN CASE
      WHEN is_account_group_member('card_ops_level2') THEN card_number
      ELSE concat('XXXX-XXXX-XXXX-', right(card_number, 4))
    END;

    -- 5. Branch row-level filter — joins a mapping table, not equality
    CREATE OR REPLACE FUNCTION ${var.catalog_name}.security.branch_row_filter(branch_id STRING)
    RETURNS BOOLEAN
    RETURN
      is_account_group_member('executive_board')
      OR is_account_group_member('compliance_auditors')
      OR is_account_group_member('data_admins')
      OR branch_id IN (
          SELECT mapped_branch_id
          FROM ${var.catalog_name}.security.user_branch_mapping
          WHERE user_email = current_user()
      );

    -- 6. PII column tags on Bronze (DPDP / PCI evidence)
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN aadhaar_number SET TAGS ('pii'='aadhaar', 'dpdp'='restricted');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN pan_number SET TAGS ('pii'='pan', 'dpdp'='restricted');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN email SET TAGS ('pii'='email');
    ALTER TABLE ${var.catalog_name}.raw_bronze.bronze_customers
      ALTER COLUMN phone SET TAGS ('pii'='phone');
  SQL
}

# ============================================================================
# MASK ATTACHMENTS — must run AFTER tables exist.
# Kept as a separate resource so DLT can create the tables first.
# Re-run `terraform apply` after the first DLT pipeline run.
# ============================================================================
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