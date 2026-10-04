# 🏦 Enterprise Banking Core Data Platform

> **Medallion Architecture on Azure Databricks · Delta Live Tables · Unity Catalog · Databricks Asset Bundles**

[![Platform](https://img.shields.io/badge/Platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white)](https://databricks.com)
[![Engine](https://img.shields.io/badge/Engine-Apache%20Spark%203.5+-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Storage](https://img.shields.io/badge/Storage-Delta%20Lake-00ADD8)](https://delta.io)
[![Governance](https://img.shields.io/badge/Governance-Unity%20Catalog-1E88E5)](https://docs.databricks.com/data-governance/unity-catalog/)
[![Compliance](https://img.shields.io/badge/Compliance-DPDP%20%7C%20PCI--DSS%20%7C%20RBI-success)]()
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Azure%20DevOps-0078D7?logo=azuredevops)](https://azure.microsoft.com/en-us/products/devops)

---

## 📖 Table of Contents

1. [Overview](#-overview)
2. [Architecture](#-architecture)
3. [Domain Scope](#-domain-scope)
4. [Repository Structure](#-repository-structure)
5. [Data Flow — Medallion Layers](#-data-flow--medallion-layers)
6. [Data Quality Framework](#-data-quality-framework)
7. [Security & Governance](#-security--governance)
8. [Prerequisites](#-prerequisites)
9. [Setup & Deployment](#-setup--deployment)
10. [Configuration Reference](#-configuration-reference)
11. [Running the Pipeline](#-running-the-pipeline)
12. [Monitoring & Observability](#-monitoring--observability)
13. [Maintenance & Operations](#-maintenance--operations)
13A  [Platform Operations](#-platform-operations)
14. [CI/CD Pipeline](#-cicd-pipeline)
15. [Testing](#-testing)
16. [Troubleshooting](#-troubleshooting)
17. [Regulatory Compliance](#-regulatory-compliance)
18. [Contributing](#-contributing)
19. [License](#-license)

---

## 🎯 Overview

The **Enterprise Banking Core Data Platform** is a production-grade Medallion Architecture built on Azure Databricks for a Tier-1 bank. It ingests, cleanses, governs, and serves analytical data across **10 core banking datasets** — from raw customer records to business-ready KPIs consumed by BI, risk, compliance, and fraud teams.

### Key Capabilities

| Capability | Implementation |
|---|---|
| **Ingestion** | Spark Auto Loader (cloudFiles) with exactly-once semantics |
| **Transformation** | Delta Live Tables (DLT) with declarative expectations |
| **Historical Tracking** | SCD Type 2 dimensions via `APPLY CHANGES INTO` |
| **Data Quality** | DLT expectations (`expect`, `expect_or_drop`, `expect_or_fail`) |
| **Governance** | Unity Catalog — column masks, row filters, PII tags |
| **PII Protection** | HMAC-SHA256 via UC SQL functions backed by Databricks Secrets |
| **Orchestration** | Databricks Workflows + DLT Pipelines |
| **CI/CD** | Databricks Asset Bundles (DAB) + Azure Pipelines |
| **Infrastructure** | Terraform (Unity Catalog, secret scopes, security functions) |
| **Optimization** | Liquid Clustering on Gold fact tables |
| **Observability** | DLT event log → materialized DQ metrics table → alerting view |

### Non-Functional Requirements

- **Idempotent** — retries never duplicate or corrupt data
- **Deterministic** — same input → same output, regardless of run count
- **Auditable** — Bronze is append-only, 30-day time-travel on Gold
- **Compliant** — DPDP Act 2023, PCI-DSS 3.2.1, RBI IT Governance
- **Incremental** — stream-stream joins, watermarks, `APPLY CHANGES`
- **Serverless-first** — cold-start < 30 seconds on serverless DLT

---

## 🏛 Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AZURE DATA LAKE STORAGE GEN2                      │
│   abfss://raw@stbanking{env}001.dfs.core.windows.net/{dataset}/*.csv     │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ Auto Loader (cloudFiles)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  🥉 BRONZE LAYER  ·  raw_bronze  ·  Append-only, immutable, PII-tagged    │
│  ──────────────────────────────────────────────────────────────────────  │
│  bronze_customers     bronze_accounts        bronze_transactions         │
│  bronze_branches      bronze_employees       bronze_credit_cards         │
│  bronze_loans         bronze_kyc_documents   bronze_fraud_alerts         │
│  bronze_atm_transactions                                                 │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ DLT Expectations · Watermark · HMAC
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  🥈 SILVER LAYER  ·  clean_silver  ·  Cleaned, masked, validated          │
│  ──────────────────────────────────────────────────────────────────────  │
│  silver_customers     silver_accounts        silver_transactions         │
│  silver_branches      silver_employees       silver_credit_cards         │
│  silver_loans         silver_kyc_documents   silver_fraud_alerts         │
│  silver_atm_transactions                                                 │
│  ── Referential Integrity Isolation ──                                    │
│  silver_transactions_validated   |   silver_transactions_quarantine      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ APPLY CHANGES (SCD2) · Joins
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  🥇 GOLD LAYER  ·  cur_gold  ·  Star Schema, Liquid Clustered            │
│  ──────────────────────────────────────────────────────────────────────  │
│  Dimensions (SCD2):  dim_customers  dim_accounts  dim_branches           │
│                      dim_credit_cards  dim_date                          │
│  Facts:              fact_transactions   fact_loans   fact_fraud_alerts  │
│  Observability:      dq_metrics_history  dq_alerts (view)                │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  BI · Risk · Fraud · BI tools│
                    │  (Power BI, Tableau, Genie)  │
                    └──────────────────────────────┘

        ┌─────────────────────────────────────────────────┐
        │  UNITY CATALOG — Cross-cutting Governance       │
        │  Column masks · Row filters · Tags · Lineage    │
        └─────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| **Compute** | Databricks Serverless DLT, Photon-enabled |
| **Storage** | Azure Data Lake Storage Gen2 + Delta Lake |
| **Catalog** | Unity Catalog (3-level namespace: `catalog.schema.table`) |
| **Config** | Databricks Asset Bundles (DAB) |
| **Secrets** | Databricks Secret Scopes + Azure Key Vault |
| **IaC** | Terraform (Databricks provider ≥ 1.50) |
| **CI/CD** | Azure DevOps Pipelines |
| **Orchestration** | Databricks Workflows |
| **Runtime** | DBR 14.3+ / CURRENT channel (needs `dropDuplicatesWithinWatermark`) |

---

## 📊 Domain Scope

The platform covers **10 core banking datasets**:

| # | Dataset | Description | PII? | PCI? | Records/Day (est.) |
|---|---|---|---|---|---|
| 1 | **customers** | Customer master data (KYC, contact, demographics) | ✅ | ❌ | 10K |
| 2 | **accounts** | Savings, current, FD, RD, NRI accounts | ❌ | ❌ | 25K |
| 3 | **transactions** | Core banking transaction journal | ❌ | ❌ | 5M |
| 4 | **branches** | Branch master with IFSC, region, vault limits | ❌ | ❌ | 10 |
| 5 | **employees** | Employee master with role, department, salary | ✅ | ❌ | 100 |
| 6 | **credit_cards** | Card portfolio (limits, balances, status) | ❌ | ✅ | 50K |
| 7 | **loans** | Loan accounts (amounts, DPD, status) | ❌ | ❌ | 100K |
| 8 | **kyc_documents** | KYC document registry (Aadhaar, PAN, etc.) | ✅ | ❌ | 15K |
| 9 | **fraud_alerts** | Fraud detection alerts and case management | ❌ | ❌ | 1K |
| 10 | **atm_transactions** | ATM terminal transaction log | ❌ | ✅ | 500K |

---

## 📁 Repository Structure

```
banking_dlt_project/
│
├── README.md                                # This file
├── databricks.yml                           # DAB bundle root config
├── .gitignore
│
├── .azure-pipelines/
│   └── azure-pipelines.yml                  # CI/CD pipeline definition
│
├── resources/
│   └── banking_dlt_pipeline.yml             # DLT pipeline + Workflows resource defs
│
├── src/
│   ├── schemas_and_security.py              # Explicit schemas + fail-fast config
│   ├── bronze_ingestion.py                  # Auto Loader ingestion for 10 datasets
│   ├── silver_transformation.py             # Cleaning, masking, watermarking, quarantine
│   ├── gold_dimensional.py                  # SCD2 dims + Liquid-clustered facts
│   └── maintenance.py                       # OPTIMIZE / ANALYZE / VACUUM notebook
│
├── sql/
│   └── dq_alerts.sql                        # Data quality alerting view
│
└── terraform/
    ├── variables.tf                         # Terraform input variables
    ├── secrets.tf                           # Secret scopes for PII salt
    └── uc_security_policies.tf              # UC functions, masks, row filters, tags
```

---

## 🔄 Data Flow — Medallion Layers

### 🥉 Bronze Layer — Raw Ingestion

- **Source:** CSV files dropped into `abfss://raw@{storage}.dfs.core.windows.net/{dataset}/`
- **Method:** Spark Auto Loader (`cloudFiles` format) — exactly-once via checkpointing
- **Schema:** Explicit `StructType` per dataset — **never `inferSchema`** in production
- **Metadata columns added:**
  - `_source_file` — ADLS path via `_metadata.file_path`
  - `_ingestion_timestamp` — file modification time
  - `_ingestion_file_hash` — SHA-256 of file path (deterministic batch ID)
- **Table properties:**
  - `delta.appendOnly=true` — immutable audit trail
  - `delta.enableChangeDataFeed=true` — CDC-ready for downstream
  - `pipelines.reset.allowed=false` — prevents accidental full-refresh data loss
- **PII handling:** Raw Aadhaar/PAN/email/phone **are present** in Bronze but tagged with `dpdp=restricted` and protected by UC column masks. See [Security & Governance](#-security--governance).

### 🥈 Silver Layer — Cleansing & Validation

Every Silver table applies:
- **String normalization:** `F.upper(F.trim(...))`, `F.initcap(...)`
- **Type enforcement:** `cast("decimal(18,2)")`, `to_timestamp(...)`
- **DLT expectations:** `expect_or_fail` (PK/NOT NULL), `expect_or_drop` (range/enum checks), `expect` (format warnings)
- **PII transformation:**
  - `aadhaar_number` → `aadhaar_sha256` (HMAC via UC function) + `aadhaar_masked` (XXXX-XXXX-last4)
  - `pan_number` → `pan_sha256` + `pan_masked`
  - `card_number_raw` → `card_number_masked` (first 6 + `******` + last 4, PCI-DSS compliant)
  - Raw PII columns are **dropped** after transformation
- **Watermarking:** `silver_transactions` uses `withWatermark("transaction_timestamp", "24 hours")` + `dropDuplicatesWithinWatermark(["transaction_id"])`
- **Referential integrity:** `silver_transactions_validated` performs a stream-stream join against `silver_accounts`; orphans are routed to `silver_transactions_quarantine`.

### 🥇 Gold Layer — Dimensional Model

**Dimensions (SCD Type 2 via `APPLY CHANGES`):**

| Table | Key | Sequence By | Cluster By |
|---|---|---|---|
| `dim_customers` | `customer_id` | `_record_updated_at` | `customer_id` |
| `dim_accounts` | `account_id` | `_record_updated_at` | `account_id, customer_id` |
| `dim_branches` | `branch_id` | `_updated_timestamp` | `branch_id` |
| `dim_credit_cards` | `card_id` | `_updated_timestamp` | `card_id, customer_id` |
| `dim_date` | `date_key` | *(static)* | *(none)* |

**Facts (Liquid Clustered):**

| Table | Cluster By | Row Grain |
|---|---|---|
| `fact_transactions` | `account_id, date_key` | One row per transaction |
| `fact_loans` | `disbursement_date_key, loan_type, loan_status` | One row per loan |
| `fact_fraud_alerts` | `alert_date_key, risk_level, alert_type` | One row per alert |

> **SCD Type 2 sequencing note:** `sequence_by` uses **source-event time** (`_record_updated_at`), not pipeline-execution time. This guarantees that Workflow retries never create spurious history rows. For sources that lack a `last_modified_date`, we fall back to Auto Loader's `_metadata.file_modification_time` — acceptable for retry-safety but **not** for logical ordering.

---

## ✅ Data Quality Framework

### Expectation Strategy

| Severity | DLT API | Use Case | Example |
|---|---|---|---|
| **Fail pipeline** | `@dlt.expect_or_fail` | PK nulls, critical FKs, invalid amounts | `customer_id IS NOT NULL` |
| **Drop + metric** | `@dlt.expect_or_drop` | Business rule violations | `amount > 0 AND amount <= 10000000` |
| **Warn only** | `@dlt.expect` | Format advisories | `email RLIKE '^[A-Za-z0-9._%+-]+@...'` |

### Expectations by Table

| Table | Fail-fast | Drop | Warn |
|---|---|---|---|
| `silver_customers` | `customer_id NOT NULL` | `kyc_status`, `customer_status` enums | `email` format |
| `silver_accounts` | `account_id`, `customer_id` | `current_balance >= 0`, `account_type` enum | — |
| `silver_transactions` | `transaction_id`, `account_id`, `transaction_timestamp` | `amount` range, `db_cr_indicator` enum | — |
| `silver_branches` | `branch_id` | `ifsc_code` regex | — |
| `silver_employees` | `employee_id` | `department` enum | — |
| `silver_credit_cards` | `card_id` | `credit_limit >= outstanding_balance` | — |
| `silver_loans` | `loan_id` | `dpd` range (0–3600) | — |
| `silver_kyc_documents` | `kyc_id` | `document_type` enum | — |
| `silver_fraud_alerts` | `alert_id` | `risk_level` enum, `risk_score` 0–100 | — |
| `silver_atm_transactions` | `atm_tx_id` | `amount` range (0–100000) | — |

### Quarantine & Observability

- **Orphaned transactions** — routed to `silver_transactions_quarantine` (batch snapshot against accounts).
- **Late data** — dropped silently by watermark; visible in DLT event log.
- **DQ metrics** — materialized to `cur_gold.dq_metrics_history` from the DLT event log.
- **Alerting view** — `cur_gold.dq_alerts` returns rows where pass-rate < 99%.

---

## 🔐 Security & Governance

### Unity Catalog Configuration

| Control | Mechanism | Scope |
|---|---|---|
| **Secret management** | Databricks Secret Scope (`banking-pii-{env}`) | PII HMAC salt |
| **PII hashing** | UC SQL function `security.pii_hmac()` | Silver customers, KYC |
| **Column masking** | UC function + `ALTER COLUMN ... SET MASK` | Email, card number |
| **Row-level security** | `security.branch_row_filter()` + mapping table | Accounts, transactions |
| **PII classification** | `ALTER COLUMN ... SET TAGS` | Bronze Aadhaar/PAN/email/phone |
| **Access control** | Databricks groups | `fraud_investigators`, `card_ops_level2`, `compliance_auditors`, `executive_board` |

### PII Handling Rules

1. **Raw PII never leaves Bronze without transformation.** In Silver, `aadhaar_number`, `pan_number`, `phone`, `email`, and `card_number_raw` are either HMAC-hashed or masked, then **dropped from the schema**.
2. **HMAC is salted from a secret scope** — the salt is never in source code, never in Git, and rotated via Terraform.
3. **Bronze PII columns are tagged** — `pii=aadhaar`, `dpdp=restricted`, etc. — enabling automated audits via `information_schema.column_tags`.
4. **Break-glass access** is granted via `data_admins` group and is fully audit-logged by Unity Catalog.

### Compliance Mapping

| Regulation | Requirement | Implementation |
|---|---|---|
| **DPDP Act 2023** | Purpose limitation, data minimization | Raw PII dropped in Silver; hashing in place |
| **DPDP Act 2023** | Right to erasure | Vault-style HMAC enables token-based deletion |
| **PCI-DSS 3.2.1** | Cardholder data protection | First 6 + last 4 only (`card_number_masked`) |
| **RBI KYC Master Direction** | Aadhaar/PAN masking in general-purpose stores | UC column masks + HMAC |
| **BCBS 239** | Risk data lineage & as-of-date reporting | SCD Type 2 with source-event sequencing |
| **RBI IT Governance** | 8+ years retention | Bronze append-only; 30-day VACUUM window on Gold |

---

## 📋 Prerequisites

### Azure / Databricks

- [ ] Azure Databricks workspace — **Premium or Enterprise** tier (Unity Catalog required)
- [ ] Databricks Runtime **14.3+** or serverless DLT with `channel: CURRENT`
- [ ] Unity Catalog **metastore** attached to the workspace
- [ ] **Serverless compute** enabled for the workspace
- [ ] Azure Data Lake Storage Gen2 with three containers: `raw`, `checkpoints`, `metastore`
- [ ] Databricks Access Connector with `Storage Blob Data Contributor` on the ADLS account

### Local Tooling (for deployment)

- [ ] Databricks CLI **v0.205+** ([install](https://docs.databricks.com/dev-tools/cli/install.html))
- [ ] Terraform **≥ 1.5**
- [ ] Python **3.10+**
- [ ] Azure DevOps service connection to the Databricks workspace

### Required Databricks Groups

Create in Unity Catalog **before** first deployment:

```sql
CREATE GROUP IF NOT EXISTS fraud_investigators;
CREATE GROUP IF NOT EXISTS card_ops_level2;
CREATE GROUP IF NOT EXISTS compliance_auditors;
CREATE GROUP IF NOT EXISTS executive_board;
CREATE GROUP IF NOT EXISTS data_admins;
```

---

## 🚀 Setup & Deployment

### 1. Clone the Repository

```bash
git clone https://dev.azure.com/your-org/banking-data-platform/_git/banking_dlt_project
cd banking_dlt_project
```

### 2. Configure Databricks CLI

```bash
databricks configure --host https://adb-dev-instance.azuredatabricks.net
# Paste your PAT or use Azure AD service principal
```

### 3. Provision Unity Catalog Infrastructure (Terraform)

```bash
cd terraform
terraform init

# Create a dev.tfvars file (never commit this):
cat > dev.tfvars <<EOF
env              = "dev"
catalog_name     = "banking_dev_catalog"
sql_warehouse_id = "abc123def456"
pii_salt         = "REPLACE_WITH_RANDOM_32_BYTE_BASE64"
EOF

terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

This provisions:
- Secret scope `banking-pii-dev` with key `salt`
- UC function `security.pii_hmac()`
- UC function `security.mask_email()`
- UC function `security.mask_card()`
- UC function `security.branch_row_filter()`
- PII column tags on `raw_bronze.bronze_customers`

### 4. Bootstrap the Branch Mapping Table

```sql
CREATE TABLE IF NOT EXISTS banking_dev_catalog.security.user_branch_mapping (
    user_email       STRING,
    mapped_branch_id STRING
);

-- Populate from your HR / AD system
INSERT INTO banking_dev_catalog.security.user_branch_mapping VALUES
    ('alice@bank.com', 'BR-MUM-001'),
    ('bob@bank.com',   'BR-DEL-007');
```

### 5. Verify Catalog Managed Location

```sql
DESCRIBE CATALOG banking_dev_catalog;
-- Location column MUST be non-null for serverless DLT
-- If null:
ALTER CATALOG banking_dev_catalog
  SET MANAGED LOCATION 'abfss://metastore@stbankingdev001.dfs.core.windows.net/';
```

### 6. Validate & Deploy the Bundle

```bash
# From repo root
databricks bundle validate -t dev
databricks bundle deploy   -t dev
```

### 7. Trigger the Pipeline

```bash
databricks bundle run -t dev banking_medallion_dlt_pipeline
```

### 8. Post-Run: Attach Column Masks

Masks can only be attached to existing tables. After the first successful run:

```bash
cd terraform
terraform apply -var-file=dev.tfvars -target=databricks_sql_exec.uc_mask_attachments
```

---

## ⚙️ Configuration Reference

### DAB Variables (`databricks.yml`)

| Variable | Dev | Prod | Description |
|---|---|---|---|
| `catalog` | `banking_dev_catalog` | `banking_prod_catalog` | Unity Catalog catalog |
| `raw_path` | `abfss://raw@stbankingdev001...` | `abfss://raw@stbankingprod001...` | Raw CSV landing zone |
| `checkpoint_path` | `abfss://checkpoints@stbankingdev001...` | `abfss://checkpoints@stbankingprod001...` | Auto Loader checkpoints |
| `pii_secret_scope` | `banking-pii-dev` | `banking-pii-prod` | Secret scope for HMAC salt |

### DLT Pipeline Configuration (`resources/banking_dlt_pipeline.yml`)

| Config Key | Source | Purpose |
|---|---|---|
| `vars.catalog` | `${var.catalog}` | Base catalog |
| `vars.bronze_schema` | `raw_bronze` | Bronze schema |
| `vars.silver_schema` | `clean_silver` | Silver schema |
| `vars.gold_schema` | `cur_gold` | Gold schema |
| `vars.raw_base_path` | `${var.raw_path}` | Auto Loader source |
| `vars.checkpoint_dir` | `${var.checkpoint_path}` | Schema + checkpoint location |
| `vars.pii_secret_scope` | `${var.pii_secret_scope}` | Secret scope name |
| `vars.pii_secret_key` | `salt` | Secret key within scope |

> **⚠️ All config keys are validated at pipeline start.** If any is missing, the pipeline fails immediately — there are no defaults.

---

## ▶️ Running the Pipeline

### Via Databricks CLI (recommended)

```bash
# Trigger a full pipeline run
databricks bundle run -t dev banking_medallion_dlt_pipeline

# Trigger the maintenance workflow (runs nightly at 02:00 IST automatically)
databricks bundle run -t dev banking_maintenance_workflow
```

### Via Databricks UI

1. Navigate to **Workflows → Delta Live Tables**
2. Select `dev-banking-medallion-pipeline`
3. Click **Start**

### Via REST API

```bash
curl -X POST https://adb-dev-instance.azuredatabricks.net/api/2.0/pipelines/{pipeline_id}/updates \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_refresh": false}'
```

### Modes

| Mode | Command | When to Use |
|---|---|---|
| **Incremental** | Default | Daily runs, new data only |
| **Full Refresh** | `databricks bundle run -t dev banking_medallion_dlt_pipeline --full-refresh` | After schema changes |
| **Full Refresh (single table)** | UI → select table → "Full refresh selected tables" | Rebuild one table |

> **⚠️ `pipelines.reset.allowed=false` on Bronze tables** means you cannot full-refresh Bronze. This is intentional — Bronze is the audit trail. To rebuild Bronze, drop the table and re-run.

---

## 📊 Monitoring & Observability

### DLT Event Log

```sql
-- Recent pipeline updates
SELECT
    timestamp,
    event_type,
    details:update_progress.state AS state,
    details:update_progress.metrics.num_output_rows AS rows_written
FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers))
WHERE event_type = 'update_progress'
ORDER BY timestamp DESC
LIMIT 20;

-- Data quality metrics per expectation
SELECT
    details:flow_progress.name AS flow_name,
    explode(details:flow_progress.data_quality.expectations) AS dq
FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers))
WHERE event_type = 'flow_progress'
  AND details:flow_progress.data_quality.expectations IS NOT NULL;
```

### DQ Alerts View

```sql
SELECT * FROM banking_dev_catalog.cur_gold.dq_alerts;
```

Returns rows for any expectation with pass-rate < 99% on the current day. Wire this to your on-call channel (Teams, PagerDuty).

### Key Metrics to Monitor

| Metric | Threshold | Alert Channel |
|---|---|---|
| Pipeline update duration | > 2 hours | Teams: `#data-platform-alerts` |
| `expect_or_drop` pass rate | < 99% | PagerDuty: `data-oncall` |
| Quarantine table row count | > 1000/day | Teams: `#data-ops` |
| Late-arriving data (watermark drops) | > 0.5% of volume | Teams: `#data-platform` |
| Bronze ingestion latency | > 30 min behind source | PagerDuty: `data-oncall` |
| Table file count (small files) | > 5000 per partition | Auto-triggered OPTIMIZE |

### Lineage

Unity Catalog automatically captures lineage. View in **Catalog Explorer → [table] → Lineage** for:
- Upstream source (Bronze ← Silver ← Gold)
- Downstream consumers (Dashboards, Notebooks, SQL queries)

---
## 🏗️ Platform Operations

| Topic | Document |
|---|---|
| **Disaster Recovery** | [`docs/DR_PLAN.md`](docs/DR_PLAN.md) — RPO/RTO, failover procedures, quarterly drills |
| **Network Architecture** | [`docs/NETWORK_ARCHITECTURE.md`](docs/NETWORK_ARCHITECTURE.md) — VNet, Private Link, egress firewall |
| **Key Vault Integration** | [`docs/KEY_VAULT_INTEGRATION.md`](docs/KEY_VAULT_INTEGRATION.md) — secret scopes, rotation, RBAC |
| **Environment Separation** | [`docs/ENVIRONMENT_SEPARATION.md`](docs/ENVIRONMENT_SEPARATION.md) — Dev/QA/Prod isolation model |
| **Terraform State Security** | [`docs/TERRAFORM_STATE.md`](docs/TERRAFORM_STATE.md) — remote backend, recovery |
| **Secret Management** | [`docs/SECRET_MANAGEMENT.md`](docs/SECRET_MANAGEMENT.md) — lifecycle, WIF, emergency rotation |
| **Operational Runbook** | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — on-call procedures |
| **Incident Response** | [`docs/INCIDENT_RESPONSE.md`](docs/INCIDENT_RESPONSE.md) — severity levels, playbooks |

### Resilience Targets

| Metric | Target |
|---|---|
| **RPO** (Recovery Point Objective) | ≤ 15 minutes |
| **RTO** (Recovery Time Objective) | ≤ 60 minutes |
| **Data Durability** | 99.999999999% (11 nines) |
| **DR Drill Frequency** | Quarterly (automated) |
| **Last DR Drill** | See `docs/dr-reports/` |


## 🔧 Maintenance & Operations

### Scheduled Maintenance Workflow

The `banking_maintenance_workflow` runs **daily at 02:00 IST** and performs:

1. **OPTIMIZE** on all Gold tables (compacts small files)
2. **ANALYZE TABLE ... COMPUTE STATISTICS** (refreshes query optimizer stats)
3. **VACUUM ... RETAIN 720 HOURS** (30-day time-travel window)

### Manual Maintenance

```bash
databricks bundle run -t prod banking_maintenance_workflow
```

### Time-Travel Retention

| Layer | Retention | Rationale |
|---|---|---|
| **Bronze** | 90 days (time-travel), 8+ years (archive) | Regulatory audit trail |
| **Silver** | 30 days | Operational recovery |
| **Gold** | 30 days | BI rollback |

### Full Refresh Procedure (schema evolution)

```bash
# 1. Deploy new code
databricks bundle deploy -t prod

# 2. Full refresh Silver + Gold (Bronze remains immutable)
databricks bundle run -t prod banking_medallion_dlt_pipeline --full-refresh

# 3. Re-apply UC masks (they survive table drops only if re-run)
cd terraform && terraform apply -var-file=prod.tfvars \
  -target=databricks_sql_exec.uc_mask_attachments
```

### Rollback Procedure

If a pipeline run produces bad data:

1. **Stop the pipeline** immediately.
2. **Identify the last good version** via `DESCRIBE HISTORY`:
   ```sql
   DESCRIBE HISTORY banking_prod_catalog.cur_gold.fact_transactions;
   ```
3. **Restore the table** to the last good version:
   ```sql
   RESTORE TABLE banking_prod_catalog.cur_gold.fact_transactions
   TO VERSION AS OF 42;
   ```
4. **Fix the root cause** in code.
5. **Re-deploy** and run incrementally.

---

## 🔁 CI/CD Pipeline

The pipeline is defined in `.azure-pipelines/azure-pipelines.yml`.

### Stages

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   VALIDATE    │───▶│    DEPLOY     │───▶│   SMOKE TEST  │
│  (any branch) │    │ (dev on PR,   │    │  (post-deploy)│
│               │    │  prod on main)│    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Environment Promotion Flow

```
Feature Branch  →  PR to main  →  main  →  Release tag
       │                │            │          │
       ▼                ▼            ▼          ▼
    Validate         Deploy Dev   Deploy QA   Deploy Prod
```

### Sample CI Pipeline

```yaml
trigger:
  branches:
    include: [ main ]

parameters:
  - name: environment
    default: dev
    values: [ dev, qa, prod ]

variables:
  - group: databricks-$(environment)-secrets

stages:
  - stage: Validate
    jobs:
      - job: BundleValidate
        steps:
          - script: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
            displayName: Install Databricks CLI
          - script: databricks bundle validate -t $(environment)
            env:
              DATABRICKS_HOST:  $(DATABRICKS_HOST)
              DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)

  - stage: Deploy
    dependsOn: Validate
    jobs:
      - job: BundleDeploy
        steps:
          - script: databricks bundle deploy -t $(environment)
          - script: databricks bundle run -t $(environment) banking_medallion_dlt_pipeline
```

---

## 🧪 Testing

### Unit Tests (PySpark)

```bash
pytest tests/unit/ -v
```

Unit tests cover:
- Masking functions (email, card, Aadhaar)
- Date dimension generation
- Expectation predicate logic (SQL expressions)
- Schema validation

### Integration Tests

Run against a dedicated `banking_test_catalog`:

```bash
pytest tests/integration/ -v --catalog=banking_test_catalog
```

Integration tests verify:
- End-to-end pipeline on sample data
- SCD2 history correctness (insert → update → verify two versions)
- Quarantine routing for orphaned transactions
- Column mask enforcement (as different personas)

### DLT Expectation Validation

Run the pipeline against a synthetic dataset with known bad rows and assert:
- `expect_or_fail` rows → pipeline fails
- `expect_or_drop` rows → count matches expectation
- `expect` rows → present in metrics but not dropped

---

## 🐛 Troubleshooting

### Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot create managed table — no managed location` | Catalog lacks managed location | `ALTER CATALOG ... SET MANAGED LOCATION ...` |
| `dropDuplicatesWithinWatermark` undefined | DBR < 14.3 | Use `channel: CURRENT` on serverless, or upgrade DBR |
| `secret('banking-pii-dev', 'salt')` not found | Secret scope not provisioned | Run `terraform apply` for `secrets.tf` |
| `photon` / `edition` warnings on serverless | Redundant settings | Comment them out (see `banking_dlt_pipeline.yml`) |
| Pipeline hangs at "Initializing" | Metastore/workspace permissions | Verify `databricks_access_connector` has `Storage Blob Data Contributor` |
| `expect_or_fail` triggers on valid rows | Expression typo or nullability mismatch | Inspect DLT event log for the failing expectation name |
| Full-refresh fails on Bronze | `pipelines.reset.allowed=false` | Drop + re-create the table (Bronze is immutable by design) |
| Mask not applied after table re-created | `ALTER TABLE ... SET MASK` is dropped with the table | Re-run `terraform apply -target=databricks_sql_exec.uc_mask_attachments` |

### Debugging Tips

```sql
-- 1. What's the pipeline doing right now?
SELECT * FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers))
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC LIMIT 10;

-- 2. Why did a row get dropped?
SELECT * FROM event_log(TABLE(banking_dev_catalog.clean_silver.silver_transactions))
WHERE event_type = 'flow_progress'
  AND details:flow_progress.data_quality.expectations IS NOT NULL;

-- 3. What's the current SCD2 state of a customer?
SELECT * FROM banking_dev_catalog.cur_gold.dim_customers
WHERE customer_id = 'CUST-12345'
ORDER BY __START_AT DESC;

-- 4. Are there orphaned transactions?
SELECT COUNT(*) FROM banking_dev_catalog.clean_silver.silver_transactions_quarantine;
```

### Getting Help

1. Check the **DLT event log** — 90% of issues are visible there.
2. Search existing [GitHub issues](https://github.com/your-org/banking-data-platform/issues).
3. Post in **#data-platform-help** on Teams.
4. Page on-call via PagerDuty (`data-oncall`) for Prod incidents.

---

## ⚖️ Regulatory Compliance

### DPDP Act 2023 (Digital Personal Data Protection)

| Obligation | Implementation |
|---|---|
| Purpose limitation | Data used only for banking operations; documented in RoPA |
| Data minimization | Raw PII dropped from Silver onwards |
| Storage limitation | Bronze archived after 90 days; PII-only files purged after KYC expiry |
| Right to erasure | HMAC tokens allow vault-style deletion (delete salt entry = break hash linkage) |
| Consent tracking | `kyc_status` and `customer_status` flags gate processing |

### PCI-DSS 3.2.1

| Requirement | Implementation |
|---|---|
| 3.4 — Render PAN unreadable | `card_number_masked` (first 6 + `******` + last 4) |
| 7.1 — Need-to-know access | UC column mask on `card_number_masked`; only `card_ops_level2` sees full |
| 10.2 — Audit trails | Unity Catalog audit logs; Bronze append-only |

### RBI IT Governance

| Requirement | Implementation |
|---|---|
| Data retention | 8+ years Bronze archive; 30-day time-travel on Gold |
| Data localization | All storage in India Central region ADLS |
| Access control | UC grants + group-based RLS/CLS |
| Audit logging | UC audit logs shipped to Azure Monitor |

### BCBS 239

| Principle | Implementation |
|---|---|
| Accuracy & integrity | DLT expectations + FK quarantine |
| Completeness | `expect_or_fail` on PKs; orphan detection |
| Timeliness | Auto Loader streaming with 24-hour watermark |
| Adaptability | Config-driven; no hardcoded values |

---

## 🤝 Contributing

### Branching Strategy

```
main            ← Production-ready
  ↑
develop         ← Integration branch
  ↑
feature/*       ← Developer branches
hotfix/*        ← Emergency fixes (branch from main, merge to main + develop)
```

### Development Workflow

1. Fork / create a feature branch from `develop`.
2. Make changes, run local tests (`pytest tests/unit/`).
3. Ensure `databricks bundle validate -t dev` passes.
4. Open a PR against `develop`.
5. CI runs automated validation.
6. Request review from 2 code owners.
7. Merge → auto-deploy to Dev.

### Code Review Checklist

- [ ] All new tables have `@dlt.expect_or_fail` on PKs
- [ ] New PII columns tagged and masked
- [ ] No hardcoded catalogs, paths, or secrets
- [ ] Config uses `dlt.config.get()` (no defaults)
- [ ] SCD2 `sequence_by` uses source-event time, not `current_timestamp()`
- [ ] Watermarks added for any new streaming table with event-time semantics
- [ ] `cluster_by` set for new fact tables
- [ ] Tests added/updated
- [ ] README updated if user-facing behavior changed

### Commit Message Convention

```
feat: add dim_credit_cards SCD2
fix: correct watermark on silver_atm_transactions
docs: update compliance mapping table
chore: bump databricks-cli to 0.210
refactor: extract masking logic to UC functions
```

---

## 📄 License

Copyright © 2025 [Your Bank Name]. All rights reserved.

**Internal use only.** This software is proprietary and confidential. Unauthorized distribution, modification, or use outside the organization is strictly prohibited.

---

## 📞 Contact & Support

| Role | Team | Channel |
|---|---|---|
| Data Platform Owner | Data Engineering | `#data-platform` |
| On-call Engineer | Data Engineering | PagerDuty: `data-oncall` |
| Compliance Officer | Risk & Compliance | `#risk-compliance` |
| Security Architect | InfoSec | `#infosec-review` |
| Product Owner | Business Intelligence | `#bi-community` |

---

## 📎 Appendix

### A. Glossary

| Term | Definition |
|---|---|
| **Bronze** | Raw, append-only ingestion layer — the audit source of truth |
| **Silver** | Cleansed, deduplicated, PII-masked operational layer |
| **Gold** | Business-ready star schema consumed by BI |
| **SCD2** | Slowly Changing Dimension Type 2 — full history preservation |
| **CDF** | Change Data Feed — Delta feature for downstream CDC consumers |
| **Watermark** | Time bound for late-arriving streaming data |
| **HMAC** | Hash-based Message Authentication Code — keyed cryptographic hash |
| **Liquid Clustering** | Modern Delta clustering that replaces Z-Order |
| **DAB** | Databricks Asset Bundle — declarative project definition |
| **DLT** | Delta Live Tables — declarative pipeline framework |

### B. Reference Documentation

- [Databricks DLT Programming Guide](https://docs.databricks.com/delta-live-tables/index.html)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Unity Catalog Security](https://docs.databricks.com/data-governance/unity-catalog/security.html)
- [Delta Lake Best Practices](https://docs.delta.io/latest/best-practices.html)
- [Auto Loader](https://docs.databricks.com/ingestion/auto-loader/index.html)
- [DLT Expectations](https://docs.databricks.com/delta-live-tables/expectations.html)
- [Terraform Databricks Provider](https://registry.terraform.io/providers/databricks/databricks/latest/docs)

### C. Change Log

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2025-Q1 | Initial production release — 10 datasets, 20+ tables, UC governance |

---

**Last updated:** 2025-01-15
**Maintainers:** Data Platform Engineering Team
**Status:** ✅ Production
