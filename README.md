# 🏦 Enterprise Banking Core Data Platform

> **Enterprise-grade reference implementation** · Medallion Architecture on Azure Databricks · Delta Live Tables · Unity Catalog · Databricks Asset Bundles

[![CI](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/ci.yml/badge.svg)](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/codeql.yml/badge.svg)](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/codeql.yml)
[![Secret Scan](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/Rafik-s/Banking_DLT_Project/actions/workflows/secret-scan.yml)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

⚠️ **This is a portfolio / reference implementation**, not a deployed production system.
See [Disclaimer](#️-disclaimer) below.

---

## 📖 Table of Contents

1. [Overview](#-overview)
2. [Disclaimer](#️-disclaimer)
3. [What Is Not Included](#-what-is-not-included)
4. [Architecture](#-architecture)
5. [Domain Scope](#-domain-scope)
6. [Repository Structure](#-repository-structure)
7. [Data Flow — Medallion Layers](#-data-flow--medallion-layers)
8. [Data Quality Framework](#-data-quality-framework)
9. [Reconciliation Framework](#-reconciliation-framework)
10. [Security & Governance](#-security--governance)
11. [Platform Operations](#-platform-operations)
12. [Prerequisites](#-prerequisites)
13. [Setup & Deployment](#-setup--deployment)
14. [Configuration Reference](#️-configuration-reference)
15. [Running the Pipeline](#️-running-the-pipeline)
16. [Monitoring & Observability](#-monitoring--observability)
17. [Maintenance & Operations](#-maintenance--operations)
18. [CI/CD Pipeline](#-cicd-pipeline)
19. [Testing](#-testing)
20. [Troubleshooting](#-troubleshooting)
21. [Regulatory Alignment](#️-regulatory-alignment)
22. [Architecture Decisions](#-architecture-decisions)
23. [Contributing](#-contributing)
24. [Glossary](#-glossary)

---

## 🎯 Overview

The **Enterprise Banking Core Data Platform** is an **enterprise-grade reference implementation**
of a Medallion Architecture on Azure Databricks. It demonstrates the patterns, governance model,
and security posture used in Tier-1 banking environments for ingesting, cleansing, governing,
and serving analytical data across **10 core banking datasets**.

### What This Repository Demonstrates

| Capability | Implementation |
|---|---|
| **Ingestion** | Spark Auto Loader (cloudFiles) with exactly-once semantics |
| **Transformation** | Delta Live Tables (DLT) with declarative expectations |
| **Historical Tracking** | SCD Type 2 dimensions via `APPLY CHANGES INTO` |
| **Data Quality** | DLT expectations (`expect`, `expect_or_drop`, `expect_or_fail`) |
| **Reconciliation** | Count + amount + double-entry checks (BCBS 239 aligned) |
| **Idempotency** | Business idempotency keys + deterministic ingestion |
| **Late-data Handling** | Quarantine routing (no silent drops) |
| **Data Contracts** | YAML contracts, semver-versioned, validated in CI |
| **Governance** | Unity Catalog — column masks, row filters, PII tags |
| **PII Protection** | HMAC-SHA256 via UC SQL functions backed by Databricks Secrets |
| **Platform Ops** | DR plan, VNet architecture, environment separation |
| **Orchestration** | Databricks Workflows + DLT Pipelines |
| **CI/CD** | Databricks Asset Bundles + Azure Pipelines |
| **Infrastructure** | Terraform (Unity Catalog, secret scopes, networking) |
| **Optimization** | Liquid Clustering on Gold fact tables |
| **Observability** | DLT event log → materialized DQ metrics → alerting |

### Non-Functional Properties (by Design)

- **Idempotent** — retries never duplicate or corrupt data
- **Deterministic** — same input → same output, regardless of run count
- **Auditable** — Bronze is append-only, 30-day time-travel on Gold
- **Recoverable** — RPO ≤ 15 min, RTO ≤ 60 min (see [`docs/DR_PLAN.md`](docs/DR_PLAN.md))
- **Observable** — DLT event log + reconciliation + DQ metrics
- **Secure** — Private Endpoints, WIF, no secrets in code

### Documentation Index

| Topic | Document |
|---|---|
| Architecture Decisions | [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) |
| Reconciliation Framework | [`docs/RECONCILIATION.md`](docs/RECONCILIATION.md) |
| Idempotency & Late Data | [`docs/IDEMPOTENCY.md`](docs/IDEMPOTENCY.md) |
| Security Boundary | [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md) |
| Disaster Recovery | [`docs/DR_PLAN.md`](docs/DR_PLAN.md) |
| Network Architecture | [`docs/NETWORK_ARCHITECTURE.md`](docs/NETWORK_ARCHITECTURE.md) |
| Key Vault Integration | [`docs/KEY_VAULT_INTEGRATION.md`](docs/KEY_VAULT_INTEGRATION.md) |
| Environment Separation | [`docs/ENVIRONMENT_SEPARATION.md`](docs/ENVIRONMENT_SEPARATION.md) |
| Terraform State Security | [`docs/TERRAFORM_STATE.md`](docs/TERRAFORM_STATE.md) |
| Secret Management | [`docs/SECRET_MANAGEMENT.md`](docs/SECRET_MANAGEMENT.md) |
| Schema Evolution | [`docs/SCHEMA_EVOLUTION.md`](docs/SCHEMA_EVOLUTION.md) |
| Operational Runbook | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| Incident Response | [`docs/INCIDENT_RESPONSE.md`](docs/INCIDENT_RESPONSE.md) |
| What's Not Included | [`docs/WHAT_IS_NOT_INCLUDED.md`](docs/WHAT_IS_NOT_INCLUDED.md) |
| Portfolio Guide | [`docs/PORTFOLIO_GUIDE.md`](docs/PORTFOLIO_GUIDE.md) |

---

## ⚠️ Disclaimer

**This repository is an enterprise-grade reference implementation**, not a deployed production system inside a Tier-1 bank.

**It demonstrates:**
- ✅ The architectural patterns (Medallion, DLT, SCD2, star schema)
- ✅ The governance model (Unity Catalog, column masks, row filters, PII tags)
- ✅ The security posture (HMAC via secret scope, restricted Bronze PII boundary)
- ✅ The deployment model (DAB, Terraform, CI/CD)
- ✅ The operational maturity (reconciliation, DR, runbook, incident response)

**It does not claim:**
- ❌ PCI-DSS **certification** — masking is *aligned with* PCI-DSS principles, not certified
- ❌ DPDP **certification** — data protection controls are implemented, not audited by DPB
- ❌ RBI **compliance sign-off** — retention and localization are configured per RBI guidance, not inspected
- ❌ Deployment in any specific bank

**Honest framing for interviews or reviews:**

> *"This is a reference implementation demonstrating the patterns used in Tier-1 banking. Here's how I'd extend it for actual production deployment in your environment."*

That framing is **more credible** than overselling — and it demonstrates engineering maturity.

---

## ❌ What Is Not Included

For transparency, this repository does **not** include:

| Category | What's Missing | Why |
|---|---|---|
| **Real data** | No customer, account, or transaction data | Compliance |
| **Real infrastructure** | No Azure subscription, ADLS, or Databricks workspace | Cost |
| **Production secrets** | No PATs, SAS tokens, or passwords | Security |
| **Complete PCI-DSS controls** | Network segmentation, FIM, log integrity, key management HSM | Out of scope |
| **Full DPDP audit trail** | Consent management, DPIA, data subject portal | Out of scope |
| **Multi-region active-active** | Only active-passive DR | Complexity |
| **Real-time streaming** | Only micro-batch (Auto Loader) | Scope |
| **ML/AI workloads** | No feature store, model serving | Not this repo's focus |
| **BI dashboards** | No Power BI / Tableau artefacts | Downstream |
| **Unit + integration + e2e tests** | Only unit tests (26) | Iteration 2 |

For the full list, see [`docs/WHAT_IS_NOT_INCLUDED.md`](docs/WHAT_IS_NOT_INCLUDED.md).

---

## 🏛 Architecture
┌──────────────────────────────────────────────────────────────────────────┐
│ AZURE DATA LAKE STORAGE GEN2 │
│ abfss://raw@stbanking{env}001.dfs.core.windows.net/{dataset}/*.csv │
│ ── Private Endpoint only ── No public access ── │
└──────────────────────────────────┬───────────────────────────────────────┘
│ Auto Loader (cloudFiles)
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 🥉 BRONZE LAYER · raw_bronze · Append-only, immutable, PII-tagged │
│ ────────────────────────────────────────────────────────────────────── │
│ bronze_customers bronze_accounts bronze_transactions │
│ bronze_branches bronze_employees bronze_credit_cards │
│ bronze_loans bronze_kyc_documents bronze_fraud_alerts │
│ bronze_atm_transactions │
│ ── REVOKE SELECT FROM account users (PII boundary) ── │
└──────────────────────────────────┬───────────────────────────────────────┘
│ DLT Expectations · Watermark · HMAC
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 🥈 SILVER LAYER · clean_silver · Cleaned, masked, validated │
│ ────────────────────────────────────────────────────────────────────── │
│ silver_customers silver_accounts silver_transactions │
│ silver_branches silver_employees silver_credit_cards │
│ silver_loans silver_kyc_documents silver_fraud_alerts │
│ silver_atm_transactions │
│ ── Referential Integrity Isolation ── │
│ silver_transactions_validated | silver_transactions_quarantine │
│ silver_transactions_late | (no silent drops) │
└──────────────────────────────────┬───────────────────────────────────────┘
│ APPLY CHANGES (SCD2) · As-of joins
▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 🥇 GOLD LAYER · cur_gold · Star Schema, Liquid Clustered │
│ ────────────────────────────────────────────────────────────────────── │
│ Dimensions (SCD2): dim_customers dim_accounts dim_branches │
│ dim_credit_cards dim_date │
│ Facts: fact_transactions fact_loans fact_fraud_alerts │
│ Observability: dq_metrics_history dq_alerts (view) │
│ Reconciliation: reconciliation_results reconciliation_failures │
└──────────────────────────────────┬───────────────────────────────────────┘
│
▼
┌──────────────────────────────┐
│ BI · Risk · Fraud · BI tools│
│ (Power BI, Tableau, Genie) │
└──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ UNITY CATALOG — Cross-cutting Governance │
│ Column masks · Row filters · Tags · Lineage · Secret scopes │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ AZURE PLATFORM — Networking · Secrets · DR │
│ VNet · Private Endpoints · Key Vault · GRS · PIM │
└─────────────────────────────────────────────────────────────────────┘

text

**Full architecture documentation:**
- [`docs/NETWORK_ARCHITECTURE.md`](docs/NETWORK_ARCHITECTURE.md)
- [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md)
- [`docs/DR_PLAN.md`](docs/DR_PLAN.md)

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

Each dataset has a **formal data contract** in [`contracts/`](contracts/).

---

## 📁 Repository Structure
banking_dlt_project/
│
├── README.md # This file
├── SUPPORT_README.md # Badge/security notes
├── SECURITY.md # Responsible disclosure
├── CONTRIBUTING.md # Contribution guide
├── CODEOWNERS # Review requirements
├── CHANGELOG.md # Version history
├── LICENSE # Proprietary license
├── VERSION # Current version
├── databricks.yml # DAB bundle config
├── requirements.txt # Python dev deps
├── pyproject.toml # Ruff / pytest config
│
├── .azure-pipelines/ # CI/CD (Azure DevOps)
│ ├── azure-pipelines.yml
│ ├── dr-drill.yml
│ └── templates/
│ └── security-scan.yml
│
├── .github/ # GitHub-native
│ ├── workflows/
│ │ ├── codeql.yml
│ │ ├── secret-scan.yml
│ │ ├── markdown-lint.yml
│ │ └── link-check.yml
│ ├── ISSUE_TEMPLATE/
│ ├── PULL_REQUEST_TEMPLATE.md
│ └── dependabot.yml
│
├── contracts/ # Data contracts
│ ├── _schema.yaml
│ ├── README.md
│ └── {10 dataset contracts}.yaml
│
├── resources/ # DAB resources
│ └── banking_dlt_pipeline.yml
│
├── src/ # DLT notebooks
│ ├── schemas_and_security.py
│ ├── bronze_ingestion.py
│ ├── silver_transformation.py
│ ├── silver_late_data.py
│ ├── gold_dimensional.py
│ ├── contract_validation.py
│ ├── reconciliation.py
│ ├── dq_observability.py
│ └── maintenance.py
│
├── scripts/ # Operational scripts
│ ├── validate_contracts.py
│ ├── dr_drill.sh
│ └── verify_key_vault.sh
│
├── sql/ # Ad-hoc SQL
│ ├── dq_alerts.sql
│ └── reconciliation_queries.sql
│
├── terraform/ # IaC
│ ├── backend.tf
│ ├── networking.tf
│ ├── key_vault.tf
│ ├── environments.tf
│ ├── uc_security_policies.tf
│ ├── reconciliation_alerts.tf
│ └── dr_replication.tf
│
├── tests/
│ └── unit/
│ ├── test_masking.py
│ ├── test_idempotency.py
│ ├── test_late_data.py
│ ├── test_reconciliation.py
│ └── test_contract_validation.py
│
└── docs/ # Documentation
├── ARCHITECTURE_DECISIONS.md
├── DR_PLAN.md
├── ENVIRONMENT_SEPARATION.md
├── GITHUB_SETUP.md
├── GLOSSARY.md
├── IDEMPOTENCY.md
├── INCIDENT_RESPONSE.md
├── KEY_VAULT_INTEGRATION.md
├── NETWORK_ARCHITECTURE.md
├── PORTFOLIO_GUIDE.md
├── RECONCILIATION.md
├── RUNBOOK.md
├── SCHEMA_EVOLUTION.md
├── SECRET_MANAGEMENT.md
├── SECURITY_BOUNDARY.md
├── TERRAFORM_STATE.md
└── WHAT_IS_NOT_INCLUDED.md

text

---

## 🔄 Data Flow — Medallion Layers

### 🥉 Bronze Layer — Raw Ingestion

- **Source:** CSV files dropped into `abfss://raw@{storage}.dfs.core.windows.net/{dataset}/`
- **Method:** Spark Auto Loader — exactly-once via checkpointing
- **Schema:** Explicit `StructType` per dataset — **never `inferSchema`** in production
- **Metadata columns:** `_source_file_path`, `_source_file_path_hash`, `_ingestion_timestamp`, `_ingest_sequence`
- **Table properties:** `delta.appendOnly=true`, `delta.enableChangeDataFeed=true`, `pipelines.reset.allowed=false`
- **PII:** Raw PII lands here by design (audit trail of last resort), restricted via `REVOKE SELECT FROM account users`
- **Drift protection:** `cloudFiles.schemaEvolutionMode = failOnNewColumns`

### 🥈 Silver Layer — Cleansing & Validation

Every Silver table applies:
- **Normalization:** `F.upper(F.trim(...))`, `F.initcap(...)`
- **Type enforcement:** `cast("decimal(18,2)")`, `to_timestamp(...)`
- **DLT expectations:** fail / drop / warn — one per contract field
- **PII transformation:** HMAC + display masks; raw PII dropped from schema
- **Watermarking:** `silver_transactions` uses 24-hour watermark
- **Business idempotency:** `dropDuplicatesWithinWatermark(["transaction_id", "source_system", "event_version"])`
- **Late-data routing:** rows older than watermark → `silver_transactions_late`
- **FK validation:** `silver_transactions_validated` / `silver_transactions_quarantine`

### 🥇 Gold Layer — Dimensional Model

**Dimensions (SCD Type 2 via `APPLY CHANGES`):**

| Table | Key | Sequence By | Cluster By |
|---|---|---|---|
| `dim_customers` | `customer_id` | `_record_updated_at` | `customer_id` |
| `dim_accounts` | `account_id` | `_record_updated_at` | `account_id, customer_id` |
| `dim_branches` | `branch_id` | `_record_updated_at` | `branch_id` |
| `dim_credit_cards` | `card_id` | `_record_updated_at` | `card_id, customer_id` |
| `dim_date` | `date_key` | *(static)* | *(none)* |

**Facts (Liquid Clustered):**

| Table | Cluster By | Grain |
|---|---|---|
| `fact_transactions` | `account_id, date_key` | One row per transaction (as-of dimension join) |
| `fact_loans` | `disbursement_date_key, loan_type, loan_status` | One row per loan |
| `fact_fraud_alerts` | `alert_date_key, risk_level, alert_type` | One row per alert |

---

## ✅ Data Quality Framework

### Expectation Strategy

| Severity | DLT API | Use Case |
|---|---|---|
| **Fail pipeline** | `@dlt.expect_or_fail` | PK nulls, critical FKs, invalid amounts |
| **Drop + metric** | `@dlt.expect_or_drop` | Business rule violations |
| **Warn only** | `@dlt.expect` | Format advisories |

### DQ Metrics & Alerting

- **Materialized** to `cur_gold.dq_metrics_history` (from DLT event log)
- **Alert view** `cur_gold.dq_alerts` returns any expectation with pass-rate < 99%
- **CI-enforced**: unit tests verify masking, idempotency, reconciliation logic

---

## 🧾 Reconciliation Framework

See [`docs/RECONCILIATION.md`](docs/RECONCILIATION.md) for full details.

| Layer | Check | Tolerance |
|---|---|---|
| **COUNT_LAYER** | `bronze_count == silver_count + quarantine + late` | Zero |
| **COUNT_LAYER** | `silver_count == gold_count` | Zero |
| **DOUBLE_ENTRY** | `SUM(credits) == SUM(debits)` | Zero (zero tolerance) |
| **AMOUNT** | `SUM(bronze.amount) == SUM(silver.amount) == SUM(gold.amount)` | 0.01% |

Runs daily at **02:45 IST** via `banking_reconciliation` Workflow. On FAIL, pages on-call.

---

## 🔐 Security & Governance

### Unity Catalog Configuration

| Control | Mechanism | Scope |
|---|---|---|
| **Secret management** | Databricks Secret Scope backed by Key Vault | PII HMAC salt |
| **PII hashing** | UC function `security.pii_hmac()` — HMAC-SHA256 | Silver customers, KYC |
| **Column masking** | UC function + `SET MASK` | Email, card number |
| **Row-level security** | `security.branch_row_filter()` + mapping table | Accounts, transactions |
| **PII classification** | `SET TAGS` | Bronze Aadhaar/PAN/email/phone |
| **Bronze PII boundary** | `REVOKE SELECT FROM account users` | raw_bronze schema |
| **Access control** | Databricks groups | `fraud_investigators`, `card_ops_level2`, etc. |
| **CI/CD auth** | Workload Identity Federation (Entra ID) | No PATs |

Full details: [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md), [`docs/KEY_VAULT_INTEGRATION.md`](docs/KEY_VAULT_INTEGRATION.md).

### Compliance Posture

| Regulation | Posture |
|---|---|
| **DPDP Act 2023** | Designed for compliance — purpose limitation, minimization, erasure via HMAC salt |
| **PCI-DSS 3.2.1** | Aligned — PAN masking, need-to-know access, audit logs (not certified) |
| **RBI IT Governance** | Configured — 8-year retention, data localization, access control |
| **BCBS 239** | SCD2 with source-event sequencing; reconciliation framework |

---

## 🏗️ Platform Operations

| Topic | Document |
|---|---|
| **Disaster Recovery** | [`docs/DR_PLAN.md`](docs/DR_PLAN.md) — RPO/RTO, failover procedures, quarterly drills |
| **Network Architecture** | [`docs/NETWORK_ARCHITECTURE.md`](docs/NETWORK_ARCHITECTURE.md) — VNet, Private Link, egress firewall |
| **Key Vault Integration** | [`docs/KEY_VAULT_INTEGRATION.md`](docs/KEY_VAULT_INTEGRATION.md) — secret scopes, rotation, RBAC |
| **Environment Separation** | [`docs/ENVIRONMENT_SEPARATION.md`](docs/ENVIRONMENT_SEPARATION.md) — Dev/QA/Prod isolation |
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

---

## 📋 Prerequisites

### Azure / Databricks

- [ ] Azure Databricks workspace — Premium or Enterprise (Unity Catalog required)
- [ ] Databricks Runtime 14.3+ or serverless DLT with `channel: CURRENT`
- [ ] Unity Catalog metastore attached
- [ ] Serverless compute enabled
- [ ] Azure Data Lake Storage Gen2 with containers: `raw`, `checkpoints`, `metastore`
- [ ] Databricks Access Connector with `Storage Blob Data Contributor`
- [ ] Azure Key Vault with `Key Vault Secrets User` RBAC
- [ ] (Optional) VNet with Private Endpoints configured

### Local Tooling

- [ ] Databricks CLI v0.231+ — [install](https://docs.databricks.com/dev-tools/cli/install.html)
- [ ] Terraform ≥ 1.5
- [ ] Python 3.10+
- [ ] (Optional) Docker for local testing

### Required Databricks Groups

Create in Unity Catalog **before** first deployment:

```sql
CREATE GROUP IF NOT EXISTS fraud_investigators;
CREATE GROUP IF NOT EXISTS card_ops_level2;
CREATE GROUP IF NOT EXISTS compliance_auditors;
CREATE GROUP IF NOT EXISTS executive_board;
CREATE GROUP IF NOT EXISTS data_admins;
🚀 Setup & Deployment
1. Clone the Repository
bash
git clone https://github.com/Rafik-s/Banking_DLT_Project.git
cd Banking_DLT_Project
2. Configure Databricks CLI (WIF, not PAT)
bash
# In CI, WIF is configured via Azure Pipelines service connection.
# Locally:
az login
databricks configure --host https://adb-dev-instance.azuredatabricks.net
# Choose "Azure CLI" auth — do NOT use a PAT
3. Provision Unity Catalog Infrastructure (Terraform)
bash
cd terraform
terraform init -backend-config=backend.tfvars

# Create dev.tfvars (never commit):
cat > dev.tfvars <<EOF
env                          = "dev"
primary_region               = "centralindia"
secondary_region             = "southindia"
vnet_cidr                    = "10.20.0.0/16"
pii_salt                     = "$(openssl rand -base64 32)"
databricks_workspace_host    = "adb-dev-instance.azuredatabricks.net"
databricks_workspace_resource_id = "/subscriptions/.../adb-dev-instance"
EOF

terraform workspace select dev || terraform workspace new dev
terraform plan  -var-file=dev.tfvars -out=tfplan
terraform apply tfplan
This provisions:

Secret scope banking-pii-dev with key salt

UC functions: pii_hmac, mask_email, mask_card, branch_row_filter

PII column tags on Bronze tables

Network (VNet, Private Endpoints, DNS zones)

Key Vault + RBAC

DR resources (for prod)

4. Bootstrap the Branch Mapping Table
sql
CREATE TABLE IF NOT EXISTS banking_dev_catalog.security.user_branch_mapping (
    user_email       STRING,
    mapped_branch_id STRING
);

INSERT INTO banking_dev_catalog.security.user_branch_mapping VALUES
    ('alice@bank.example', 'BR-MUM-001'),
    ('bob@bank.example',   'BR-DEL-007');
5. Verify Catalog Managed Location
sql
DESCRIBE CATALOG banking_dev_catalog;
-- Location column MUST be non-null for serverless DLT
-- If null:
ALTER CATALOG banking_dev_catalog
  SET MANAGED LOCATION 'abfss://metastore@stbankingdev001.dfs.core.windows.net/';
6. Validate & Deploy the Bundle
bash
databricks bundle validate -t dev
databricks bundle deploy   -t dev
7. Trigger the Pipeline
bash
databricks bundle run -t dev banking_medallion_dlt_pipeline
8. Post-Run: Attach Column Masks
bash
cd terraform
terraform apply -var-file=dev.tfvars -target=databricks_sql_exec.uc_mask_attachments
9. Verify
bash
# Run the verification script
bash scripts/verify_key_vault.sh dev

# Check reconciliation
databricks sql --warehouse-id <id> \
  "SELECT * FROM banking_dev_catalog.cur_gold.reconciliation_results ORDER BY reconciled_at DESC LIMIT 10"
⚙️ Configuration Reference
DAB Variables (databricks.yml)
Variable	Dev	Prod
catalog	banking_dev_catalog	banking_prod_catalog
raw_path	abfss://raw@stbankingdev001...	abfss://raw@stbankingprod001...
checkpoint_path	abfss://checkpoints@stbankingdev001...	abfss://checkpoints@stbankingprod001...
pii_secret_scope	banking-pii-dev	banking-pii-prod
DLT Pipeline Configuration
Config Key	Purpose
vars.catalog	Base catalog
vars.bronze_schema	raw_bronze
vars.silver_schema	clean_silver
vars.gold_schema	cur_gold
vars.raw_base_path	Auto Loader source
vars.checkpoint_dir	Schema + checkpoint location
⚠️ All config keys are validated at pipeline start. If any is missing, the pipeline fails immediately — there are no defaults.

▶️ Running the Pipeline
Via Databricks CLI
bash
databricks bundle run -t dev banking_medallion_dlt_pipeline
databricks bundle run -t dev banking_maintenance_workflow
databricks bundle run -t dev banking_reconciliation
Via Databricks UI
Workflows → Delta Live Tables

Select dev-banking-medallion-pipeline

Click Start

Modes
Mode	Command
Incremental	Default
Full Refresh	databricks bundle run -t dev banking_medallion_dlt_pipeline --full-refresh
Single table refresh	UI → select table → "Full refresh selected tables"
📊 Monitoring & Observability
DLT Event Log
sql
-- Recent pipeline updates
SELECT
    timestamp,
    event_type,
    details:update_progress.state AS state,
    details:update_progress.metrics.num_output_rows AS rows_written
FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers))
WHERE event_type = 'update_progress'
ORDER BY timestamp DESCLIMIT 20;
DQ Alerts
sql
SELECT * FROM banking_dev_catalog.cur_gold.dq_alerts;
Reconciliation Dashboard
sql
SELECT * FROM banking_dev_catalog.cur_gold.reconciliation_failures;
SELECT * FROM banking_dev_catalog.cur_gold.reconciliation_sla;
Key Metrics
Metric	Threshold	Alert
Pipeline update duration	> 2 hours	Teams
expect_or_drop pass rate	< 99%	PagerDuty
Quarantine row count	> 1000/day	Teams
Late-arriving data	> 0.5% of volume	Teams
Reconciliation FAIL	Any	PagerDuty — page
🔧 Maintenance & Operations
Scheduled Workflows
Time (IST)	Job	Purpose
02:00	banking_maintenance_workflow	OPTIMIZE / ANALYZE / VACUUM
02:30	banking_dq_observability	Materialize DQ metrics
02:45	banking_reconciliation	Reconciliation checks (pages on FAIL)
Full Refresh Procedure
bash
# Deploy new code
databricks bundle deploy -t prod

# Full refresh Silver + Gold (Bronze remains immutable)
databricks bundle run -t prod banking_medallion_dlt_pipeline --full-refresh

# Re-apply UC masks
cd terraform && terraform apply -var-file=prod.tfvars -target=databricks_sql_exec.uc_mask_attachments
Rollback Procedure
See docs/RUNBOOK.md §4.

🔁 CI/CD Pipeline
Azure Pipelines Stages
text
1. Security Scans    (gitleaks, bandit, pip-audit, checkov, trivy)
2. Contract Validation (contracts vs Python schemas, backward compat)
3. Validate          (DAB validate, Terraform fmt/validate)
4. Deploy            (WIF auth, DAB deploy, pipeline run)
GitHub Actions
Workflow	Trigger	Purpose
codeql.yml	push, PR, weekly	Static analysis
secret-scan.yml	push, PR, daily	Gitleaks
markdown-lint.yml	push, PR	Markdown quality
link-check.yml	push, PR, weekly	Dead link detection
Environment Promotion
text
Feature Branch → PR → develop → Deploy Dev → QA branch → Deploy QA → main → CAB approval → Deploy Prod
🧪 Testing
Run Locally
bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing
Test Suite (26 tests)
Test File	Tests	Coverage
test_masking.py	5	Email, phone, Aadhaar, PAN, card masking
test_idempotency.py	3	Business idempotency key behavior
test_late_data.py	1	Late-arrival detection
test_reconciliation.py	5	PASS/FAIL/WARNING classification
test_contract_validation.py	12	Schema + backward-compat rules
CI
Unit tests run on every PR — blocking

Coverage target: 70% on src/*.py

🐛 Troubleshooting
Symptom	Cause	Fix
Cannot create managed table — no managed location	Catalog lacks managed location	ALTER CATALOG ... SET MANAGED LOCATION ...
dropDuplicatesWithinWatermark undefined	DBR < 14.3	Use channel: CURRENT on serverless
secret('banking-pii-dev', 'salt') not found	Secret scope not provisioned	terraform apply for secrets.tf
Pipeline hangs at "Initializing"	Permissions or VNet	Verify Access Connector + Private Endpoint
expect_or_fail triggers on valid rows	Expression typo	Inspect DLT event log
Reconciliation FAIL	Count or amount mismatch	See docs/RUNBOOK.md §4
Late data spike	Source delivery delay	Check silver_transactions_late; contact source team
Debugging Queries
sql
-- Pipeline state
SELECT * FROM event_log(TABLE(banking_dev_catalog.raw_bronze.bronze_customers))
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC LIMIT 10;

-- SCD2 history
SELECT * FROM banking_dev_catalog.cur_gold.dim_customers
WHERE customer_id = 'CUST-12345'
ORDER BY __START_AT DESC;

-- Orphaned transactions
SELECT COUNT(*) FROM banking_dev_catalog.clean_silver.silver_transactions_quarantine;

-- Late data
SELECT * FROM banking_dev_catalog.clean_silver.silver_transactions_late
ORDER BY late_by_hours DESC LIMIT 20;
⚖️ Regulatory Alignment
Regulation	Posture	Evidence
DPDP Act 2023	Designed for compliance	Purpose limitation, minimization, HMAC-based erasure
PCI-DSS 3.2.1	Aligned (not certified)	PAN masking, RLS, audit logs
RBI IT Governance	Configured	8-year retention, localization, access control
BCBS 239	SCD2 + reconciliation	Source-event sequencing, count + amount tie-out
ISO 27001	Aligned	Network isolation, secret management, audit logging
Full mapping: see docs/RECONCILIATION.md §6, docs/DR_PLAN.md §9.

📐 Architecture Decisions
Key decisions and their rationale are documented as ADRs in docs/ARCHITECTURE_DECISIONS.md.

Highlights:

#	Decision	Rationale
1	Auto Loader over spark.read.csv	Exactly-once, checkpointing, schema evolution
2	DLT over notebooks	Lineage, expectations, managed orchestration
3	SCD2 via APPLY CHANGES	Auto-maintained history, BCBS 239 compliance
4	Business idempotency key (composite)	transaction_id alone is not globally unique
5	Late data → quarantine	No silent data loss (banking principle)
6	HMAC via UC function	Salt never in code; audit logging
7	Reconciliation framework	Count + amount + double-entry tie-out
8	YAML data contracts	Source-of-truth for schema; CI enforcement
🤝 Contributing
See CONTRIBUTING.md for full guidelines.

Quick Start
Branch from develop: git checkout -b feature/your-feature

Make changes; run pytest tests/unit/

Validate: databricks bundle validate -t dev

Commit (Conventional Commits): feat(scope): description

Open PR against develop

Code Review Checklist
□ All new tables have @dlt.expect_or_fail on PKs
□ New PII columns are tagged and masked
□ No hardcoded catalogs, paths, or secrets
□ Config uses dlt.config.get() with no defaults
□ SCD2 sequence_by uses source-event time
□ Watermarks added for streaming tables with event-time semantics
□ cluster_by set for new fact tables
□ Data contract updated if schema changed
□ Tests added or updated
□ CHANGELOG.md updated
📎 Glossary
See docs/GLOSSARY.md for full glossary.

Key terms:

Term	Definition
Bronze	Raw, append-only ingestion layer — audit source of truth
Silver	Cleansed, deduplicated, PII-masked operational layer
Gold	Business-ready star schema for BI
SCD2	Slowly Changing Dimension Type 2 — full history
CDF	Change Data Feed — Delta feature for downstream CDC
Watermark	Time bound for late-arriving streaming data
HMAC	Hash-based Message Authentication Code
Liquid Clustering	Modern Delta clustering (replaces Z-Order)
DAB	Databricks Asset Bundle
DLT	Delta Live Tables
WIF	Workload Identity Federation
📄 License
Copyright © 2026 Rafik-s. All rights reserved.

Proprietary and confidential. See LICENSE for details.

📞 Contact
Role	Channel
Repository Owner	@Rafik-s
Issues	GitHub Issues
Security	See SECURITY.md
Last updated: 2026-10-04
Maintainer: Rafik-s
Status: ✅ Reference implementation