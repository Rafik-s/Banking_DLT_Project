### Fixed
- **Critical:** `email_masked` in `silver_customers` and `silver_employees` now uses real masking (`j*********@gmail.com`) instead of `lower(trim(email))` which was not a mask
- **Critical:** `silver_employees.phone_masked` now uses real masking — was previously unmasked
- `card_number_masked` README wording changed from "PCI-DSS compliant" to "PCI-DSS-aligned" (accurate classification)
- `_ingestion_file_hash` renamed to `_source_file_path_hash` (it hashes path, not content)
- `silver_transactions_quarantine` and `silver_transactions_validated` now use proper stream-stream joins with time bounds

### Added
- `email_sha256`, `phone_sha256`, `card_number_sha256` for deterministic PII matching without exposing raw values
- `docs/SECURITY_BOUNDARY.md` — formal documentation of Bronze PII security boundary
- `expect_or_fail("valid_record_updated_at", "_record_updated_at IS NOT NULL")` on Silver tables with watermarks
- Explicit `REVOKE EXECUTE ON FUNCTION pii_hmac FROM account users` in Terraform
- `REVOKE SELECT ON SCHEMA raw_bronze FROM account users` in Terraform
- PII column tags now include `tier='bronze-pii'` for audit automation

### Changed
- README framing: "production-grade Tier-1 bank" → "enterprise-grade reference implementation"
- Added `## ⚠️ Disclaimer` section to README
- `_record_updated_at` added to `silver_branches`, `silver_credit_cards`, `silver_loans`, `silver_kyc_documents`, `silver_fraud_alerts`, `silver_atm_transactions` (Workstream 2 prep)


---

## 📄 File 7 (PATCH): `CHANGELOG.md`

Add under `## [Unreleased]`:

```markdown
### Fixed
- **Critical:** Late-arriving transactions are no longer silently dropped by watermark — routed to `silver_transactions_late`
- **Critical:** `fact_transactions` now joins to dimension version valid at transaction time (BCBS 239 as-of-date correctness)
- **Critical:** SCD2 sequencing now consistent across all dimensions via `_record_updated_at` (source-event time)

### Added
- `source_system` and `event_version` columns in `TRANSACTIONS_SCHEMA`
- Business idempotency key: `(transaction_id, source_system, event_version)`
- `_ingest_sequence` in Bronze — deterministic replacement for `uuid()`
- `_source_file_path` column in Bronze for debugging
- `silver_transactions_late` quarantine table
- `docs/IDEMPOTENCY.md` — pattern documentation

### Changed
- Renamed `_ingestion_file_hash` → `_source_file_path_hash` (accurate naming)
- `cloudFiles.schemaEvolutionMode` set to `failOnNewColumns` (fail loudly on drift)
- `rescuedDataColumn` enabled — captures schema-mismatched rows
- `cloudFiles.backfillInterval` set to `1 day` for late file detection





---

## 📄 File 7 (NEW): `tests/unit/test_reconciliation.py`

```python
"""Unit tests for reconciliation classification logic."""
import pytest
from decimal import Decimal

from src.reconciliation import _classify


def test_classify_exact_match_passes():
    status, reason = _classify(0, Decimal("0.00"), 0.0001)
    assert status == "PASS"
    assert reason is None


def test_classify_count_mismatch_fails():
    status, reason = _classify(5, Decimal("0.00"), 0.0001)
    assert status == "FAIL"
    assert "row count difference" in reason


def test_classify_count_mismatch_negative_fails():
    status, reason = _classify(-3, Decimal("0.00"), 0.0001)
    assert status == "FAIL"
    assert "row count difference of -3" in reason


def test_classify_count_ok_amount_mismatch_fails():
    status, reason = _classify(0, Decimal("100.00"), 0.0001)
    assert status == "FAIL"
    assert "amount differs" in reason


def test_classify_no_discrepancy_returns_pass():
    status, reason = _classify(0, Decimal("0.00"), 0.0001)
    assert status == "PASS"

### Added
- **Banking Reconciliation Engine** (`src/reconciliation.py`)
  - COUNT_LAYER reconciliation: Bronze ↔ Silver ↔ Gold
  - DOUBLE_ENTRY reconciliation: SUM(credits) == SUM(debits)
  - AMOUNT reconciliation: financial tie-out across layers
  - Tolerance-aware classification (PASS / WARNING / FAIL / SKIPPED)
  - Idempotent append-only results table
- `cur_gold.reconciliation_results` — one row per check per day
- `cur_gold.reconciliation_failures` view — on-call triage
- `cur_gold.reconciliation_sla` view — 30-day pass-rate trend
- `banking_reconciliation` Workflow job (02:45 IST daily)
- `sql/reconciliation_queries.sql` — ad-hoc reference queries
- `docs/RECONCILIATION.md` — framework documentation
- `terraform/reconciliation_alerts.tf` — Terraform-provisioned views
- Unit tests in `tests/unit/test_reconciliation.py`






---

## 📄 File 6 (NEW): `.gitleaks.toml`

```toml
# ============================================================================
# GITLEAKS CONFIGURATION — Banking DLT Platform
# Scans for accidentally committed secrets.
# ============================================================================

title = "Banking DLT Project — Secret Detection"

[extend]
# Extend the default gitleaks rules (which cover AWS, GCP, generic, etc.)
useDefault = true

[[rules]]
id = "databricks-pat"
description = "Databricks Personal Access Token"
regex = '''dapi[a-f0-9]{32}'''
tags = ["databricks", "token", "pat"]

[[rules]]
id = "databricks-oauth-secret"
description = "Databricks OAuth client secret"
regex = '''dose[a-f0-9]{32}'''
tags = ["databricks", "oauth", "secret"]

[[rules]]
id = "azure-storage-key"
description = "Azure Storage Account Key"
regex = '''AccountKey=[A-Za-z0-9+/=]{88}'''
tags = ["azure", "storage", "key"]

[[rules]]
id = "azure-sas-token"
description = "Azure SAS token"
regex = '''sig=[A-Za-z0-9%]+&se=\d{4}-\d{2}-\d{2}'''
tags = ["azure", "sas"]

[[rules]]
id = "azure-connection-string"
description = "Azure Storage connection string"
regex = '''DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}'''
tags = ["azure", "storage", "connection-string"]

[[rules]]
id = "aadhaar-number"
description = "Aadhaar-like number (12 digits, PII leak)"
regex = '''\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b'''
tags = ["pii", "aadhaar", "dpdp"]
# Note: this rule is aggressive; enable in a separate "PII scan" job if false positives occur

[[rules]]
id = "pan-number"
description = "PAN card number (Indian tax ID)"
regex = '''\b[A-Z]{5}[0-9]{4}[A-Z]\b'''
tags = ["pii", "pan"]

[[rules]]
id = "generic-api-key"
description = "Generic API key pattern"
regex = '''(?i)(api[_-]?key|apikey|secret[_-]?key)['"\s:=]+['"]?([A-Za-z0-9_\-]{24,})'''
tags = ["generic", "api-key"]
entropy = 4.0

[[rules]]
id = "private-key"
description = "Private key file contents"
regex = '''-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY'''
tags = ["key", "private"]

# ============================================================================
# ALLOWLIST — safe patterns that look like secrets but aren't
# ============================================================================
[allowlist]
description = "Global allowlist for known false positives"
paths = [
  '''.*\.md$''',                     # Documentation often contains examples
  '''docs/.*''',                     # Docs folder
  '''tests/.*\.py$''',               # Test files with dummy values
  '''.*\.example$''',                # Template files
  '''.*\.example\.tfvars$''',
  '''backend\.tfvars\.example''',
]

# Specific false-positive strings
regexTarget = "match"
regexes = [
  '''REPLACE_WITH.*''',
  '''<your-.*>''',
  '''xxxxx+''',
  '''dummy[-_]?token''',
  '''example\.com''',
  '''test@example\.com''',
  '''AKIAIOSFODNN7EXAMPLE''',        # AWS documentation example
  '''wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY''',
]




---

## 📄 File 14 (PATCH): `CHANGELOG.md`

Add under `## [Unreleased]`:

```markdown
### Security
- **Breaking:** CI/CD now uses Workload Identity Federation (WIF) — PATs removed
- Databricks CLI pinned to `v0.231.0` with SHA256 verification (was `curl | sh`)
- Terraform backend moved to Azure Storage with encryption, locking, and RBAC
- Added gitleaks secret scanning (pre-commit + CI)
- Added bandit Python SAST
- Added pip-audit dependency scanning
- Added checkov + trivy IaC scanning
- Added GitHub CodeQL weekly scan
- Added Dependabot for pip / actions / terraform
- Added CODEOWNERS requiring review for security-sensitive paths
- Added `.pre-commit-config.yaml` for local enforcement
- `SECURITY.md` — responsible disclosure policy
- `docs/TERRAFORM_STATE.md` — state security documentation
- `docs/SECRET_MANAGEMENT.md` — secret lifecycle and rotation

### Changed
- `.azure-pipelines/azure-pipelines.yml` — full rewrite for WIF + supply chain security
- Databricks auth: `azure-cli` (OIDC) instead of PAT






# Changelog

All notable changes to the **Enterprise Banking Core Data Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Workstream 5 — Data Contracts & Schema Evolution

#### Added
- **Data Contracts framework** (`contracts/`)
  - One YAML contract per dataset, versioned with semver
  - Meta-schema in `contracts/_schema.yaml` (JSON Schema)
  - 10 dataset contracts: customers, accounts, transactions, branches, employees, credit_cards, loans, kyc_documents, fraud_alerts, atm_transactions
  - Contract registry documented in `contracts/README.md`
- `src/contract_validation.py` — programmatic contract validation
  - Meta-schema validation
  - Python `StructType` ↔ contract match (name, type, precision, scale, nullability, order)
  - Backward-compatibility enforcement (semver rules)
- `scripts/validate_contracts.py` — CI entry point
  - `--all` validates every contract
  - `--dataset <name>` validates one
  - `--git-diff` compares against `HEAD` for backward-compat check
- `tests/unit/test_contract_validation.py` — 12 unit tests
- CI stage `ContractValidation` (runs after `SecurityScans`)
- `docs/SCHEMA_EVOLUTION.md` — evolution policy + approval workflow
- `requirements.txt` — pinned dev + CI dependencies
- `pyproject.toml` — ruff, black, bandit, pytest, coverage configuration

#### Changed
- `.azure-pipelines/azure-pipelines.yml` — added `ContractValidation` stage
- `src/bronze_ingestion.py` — contract validation integrated into reader
- `cloudFiles.schemaEvolutionMode = failOnNewColumns` — pipeline fails loudly on unauthorized source drift

---

### Workstream 4 — Security & Secrets Modernization

#### Security
- **BREAKING:** CI/CD now uses Workload Identity Federation (WIF) — PATs removed
- Databricks CLI pinned to `v0.231.0` with SHA256 verification (was `curl | sh`)
- Terraform backend moved to Azure Storage with encryption, versioning, soft delete, and RBAC
- Added gitleaks secret scanning (pre-commit + CI + daily full-history)
- Added bandit Python SAST
- Added pip-audit dependency scanning
- Added checkov + trivy IaC scanning
- Added GitHub CodeQL weekly scan
- Added Dependabot for pip / github-actions / terraform
- Added `CODEOWNERS` requiring review for security-sensitive paths
- Added `.pre-commit-config.yaml` for local enforcement

#### Added
- `SECURITY.md` — responsible disclosure policy
- `docs/TERRAFORM_STATE.md` — state security documentation
- `docs/SECRET_MANAGEMENT.md` — secret lifecycle + rotation procedure
- `.github/workflows/codeql.yml`
- `.github/workflows/secret-scan.yml`
- `.github/dependabot.yml`
- `.gitleaks.toml` — custom rules for Databricks PATs, Azure keys, PII leakage
- `.azure-pipelines/templates/security-scan.yml` — reusable scan template
- `terraform/backend.tf` — remote state backend
- `terraform/backend.tfvars.example` — backend config template

#### Changed
- `.azure-pipelines/azure-pipelines.yml` — full rewrite for WIF + supply chain security
- Databricks auth: `azure-cli` (OIDC) instead of PAT

---

### Workstream 3 — Banking Reconciliation Engine

#### Added
- **Banking Reconciliation Engine** (`src/reconciliation.py`)
  - `COUNT_LAYER` — Bronze ↔ Silver ↔ Gold row count tie-out
  - `DOUBLE_ENTRY` — `SUM(credits) == SUM(debits)` zero-tolerance check
  - `AMOUNT` — financial tie-out across layers
  - Tolerance-aware classification: `PASS` / `WARNING` / `FAIL` / `SKIPPED`
  - Idempotent append-only results table
- `cur_gold.reconciliation_results` — one row per check per day
- `cur_gold.reconciliation_failures` view — on-call triage
- `cur_gold.reconciliation_sla` view — 30-day pass-rate trend
- `banking_reconciliation` Workflow job (daily 02:45 IST)
- `sql/reconciliation_queries.sql` — ad-hoc reference queries
- `docs/RECONCILIATION.md` — framework + regulatory mapping
- `terraform/reconciliation_alerts.tf` — Terraform-provisioned views
- `tests/unit/test_reconciliation.py` — 5 unit tests

#### Changed
- `resources/banking_dlt_pipeline.yml` — added reconciliation job + rescheduled DQ observability to 02:30

---

### Workstream 2 — Idempotency & Late Data

#### Fixed
- **Critical:** Late-arriving transactions are no longer silently dropped by watermark — routed to `silver_transactions_late`
- **Critical:** `fact_transactions` now joins to dimension version valid at transaction time (BCBS 239 as-of-date correctness)
- **Critical:** SCD2 sequencing now consistent across all dimensions via `_record_updated_at` (source-event time)
- **Critical:** Removed `uuid()` semantics — replaced with deterministic `_ingest_sequence`

#### Added
- `source_system` and `event_version` columns in `TRANSACTIONS_SCHEMA`
- Business idempotency key: `(transaction_id, source_system, event_version)`
- `_ingest_sequence` in Bronze — deterministic replacement for `uuid()`
- `_source_file_path` column in Bronze for debugging
- `silver_transactions_late` quarantine table
- `docs/IDEMPOTENCY.md` — pattern documentation
- `tests/unit/test_idempotency.py` — 3 unit tests
- `tests/unit/test_late_data.py` — 1 unit test

#### Changed
- Renamed `_ingestion_file_hash` → `_source_file_path_hash` (accurate naming)
- `cloudFiles.schemaEvolutionMode` set to `failOnNewColumns` (fail loudly on drift)
- `rescuedDataColumn` enabled — captures schema-mismatched rows
- `cloudFiles.backfillInterval` set to `1 day` for late file detection
- `silver_transactions_quarantine` and `silver_transactions_validated` use proper stream-stream joins with time bounds

---

### Workstream 1 — PII & Masking Correctness

#### Fixed
- **Critical:** `email_masked` in `silver_customers` and `silver_employees` now uses real masking (`j*********@gmail.com`) instead of `lower(trim(email))` which was not a mask
- **Critical:** `silver_employees.phone_masked` now uses real masking — was previously unmasked
- `card_number_masked` README wording changed from "PCI-DSS compliant" to "PCI-DSS-aligned" (accurate classification)
- `_ingestion_file_hash` renamed to `_source_file_path_hash` (it hashes path, not content)

#### Added
- `email_sha256`, `phone_sha256`, `card_number_sha256` for deterministic PII matching without exposing raw values
- `docs/SECURITY_BOUNDARY.md` — formal documentation of Bronze PII security boundary
- `expect_or_fail("valid_record_updated_at", "_record_updated_at IS NOT NULL")` on Silver tables with watermarks
- Explicit `REVOKE EXECUTE ON FUNCTION pii_hmac FROM account users` in Terraform
- `REVOKE SELECT ON SCHEMA raw_bronze FROM account users` in Terraform
- PII column tags now include `tier='bronze-pii'` for audit automation
- `tests/unit/test_masking.py` — 5 unit tests

#### Changed
- README framing: "production-grade Tier-1 bank" → "enterprise-grade reference implementation"
- Added `## ⚠️ Disclaimer` section to README
- `_record_updated_at` added to `silver_branches`, `silver_credit_cards`, `silver_loans`, `silver_kyc_documents`, `silver_fraud_alerts`, `silver_atm_transactions` (SCD2 prep)

---

## [1.0.0] — 2026-10-04

### Added
- Medallion Architecture (Bronze / Silver / Gold) on Azure Databricks DLT
- Auto Loader ingestion for 10 core banking datasets
- DLT expectations (`expect`, `expect_or_drop`, `expect_or_fail`) on all Silver tables
- SCD Type 2 dimensions via `APPLY CHANGES INTO`
- Liquid Clustered fact tables (`fact_transactions`, `fact_loans`, `fact_fraud_alerts`)
- HMAC-SHA256 PII hashing via Unity Catalog SQL function backed by Databricks Secrets
- Column masking + row-level security on Silver tables
- PII column tagging (`pii`, `dpdp`) on Bronze for compliance auditing
- Quarantine table for orphaned transactions (`silver_transactions_quarantine`)
- Terraform provisioning for Unity Catalog security functions and secret scopes
- Databricks Asset Bundle (DAB) with Dev / QA / Prod targets
- Azure Pipelines CI/CD definition for `bundle validate` and `bundle deploy`
- Nightly maintenance workflow (OPTIMIZE / ANALYZE / VACUUM)
- DQ alerting view (`cur_gold.dq_alerts`) for on-call paging
- Comprehensive `README.md` and `SUPPORT_README.md`

---

## Legend

### Change Categories
- **Added** — new features, files, or capabilities
- **Changed** — changes to existing functionality
- **Deprecated** — features that will be removed in a future release
- **Removed** — features removed in this release
- **Fixed** — bug fixes
- **Security** — security-related changes (CVE fixes, credential handling, etc.)

### Severity Markers
- **Critical:** — regulatory impact, PII exposure, data loss risk
- **BREAKING CHANGE:** — requires coordinated migration for consumers
- No marker — non-breaking improvement

### Versioning
- **MAJOR** (X.0.0) — breaking change, coordinated release required
- **MINOR** (x.Y.0) — additive change, backward compatible
- **PATCH** (x.y.Z) — documentation, comments, or minor fix

---

## How to Update This File

### For every PR

Add a new entry at the top of `## [Unreleased]` under the appropriate category
(`Added`, `Changed`, `Fixed`, `Security`). Group by workstream if applicable.

### Template

```markdown
### Workstream N — <Title>

#### Added
- <New feature>

#### Fixed
- **Critical:** <regulatory or PII issue>

#### Changed
- <Modification to existing behavior>


### Workstream 6 — DR, Networking, Key Vault & Environment Separation

#### Added
- **Disaster Recovery plan** (`docs/DR_PLAN.md`)
  - RPO ≤ 15 minutes, RTO ≤ 60 minutes
  - GRS/RA-GRS replication for ADLS
  - DR region workspace (Terraform-provisioned)
  - Quarterly automated drills (`scripts/dr_drill.sh`)
  - DR drill CI pipeline (`.azure-pipelines/dr-drill.yml`)
- **Network architecture** (`docs/NETWORK_ARCHITECTURE.md`)
  - VNet-injected Databricks (Secure Cluster Connectivity, no public IPs)
  - Private Endpoints for ADLS, Key Vault, Databricks UI
  - Private DNS zones
  - NAT gateway + egress firewall allowlist
  - NSGs per subnet
- **Key Vault integration** (`docs/KEY_VAULT_INTEGRATION.md`)
  - Terraform: `terraform/key_vault.tf`
  - RBAC + Private Endpoint + audit logging
  - Rotation policy + emergency access procedure
- **Environment separation** (`docs/ENVIRONMENT_SEPARATION.md`)
  - Per-environment Azure subscriptions, VNets, storage, Key Vaults
  - No VNet peering; no shared secrets
  - Dedicated service principals per environment
  - CAB approval workflow for Prod
- **Operational runbook** (`docs/RUNBOOK.md`)
  - On-call procedures for common incidents
  - Escalation matrix
  - Useful CLI commands
- **Incident response** (`docs/INCIDENT_RESPONSE.md`)
  - Severity levels (SEV-1 to SEV-4)
  - Post-mortem template
  - Regulatory notification requirements
- **Terraform**: `networking.tf`, `key_vault.tf`, `environments.tf`, `dr_replication.tf`
- **Scripts**: `dr_drill.sh`, `verify_key_vault.sh`
- **CI**: `.azure-pipelines/dr-drill.yml` — quarterly scheduled drill

#### Changed
- `terraform/README.md` — comprehensive Terraform guide

---

#### Fixed
- Late-arriving transactions are no longer silently dropped by watermark — routed to `silver_transactions_late`
- `fact_transactions` now joins to dimension version valid at transaction time (BCBS 239)
- SCD2 sequencing now consistent across all dimensions via `_record_updated_at`
- Removed `uuid()` — replaced with deterministic `_ingest_sequence`

#### Added (Workstream 2)
- `source_system` and `event_version` columns in `TRANSACTIONS_SCHEMA`
- Business idempotency key: `(transaction_id, source_system, event_version)`
- `silver_transactions_late` quarantine table
- `docs/IDEMPOTENCY.md`
- `tests/unit/test_idempotency.py` (3 tests)
- `tests/unit/test_late_data.py` (1 test)

#### Added (Workstream 1)
- Real email/phone masking in `silver_customers` and `silver_employees`
- `email_sha256`, `phone_sha256`, `card_number_sha256` for deterministic matching
- `docs/SECURITY_BOUNDARY.md`
- `tests/unit/test_masking.py` (5 tests)

#### Changed (Workstream 1)
- `card_number_masked` — PCI-DSS wording corrected to "aligned"
- README rebranded to "enterprise-grade reference implementation"
- `_ingestion_file_hash` → `_source_file_path_hash`

#### Added (Workstream 3)
- **Banking Reconciliation Engine** (`src/reconciliation.py`)
- `cur_gold.reconciliation_results` + failure + SLA views
- `docs/RECONCILIATION.md`
- `sql/reconciliation_queries.sql`
- `tests/unit/test_reconciliation.py` (5 tests)

#### Added (Workstream 4)
- WIF for CI/CD (no PATs)
- Pinned Databricks CLI + checksums
- Terraform remote state backend
- gitleaks, bandit, pip-audit, checkov, trivy, CodeQL, Dependabot
- `SECURITY.md`, `docs/TERRAFORM_STATE.md`, `docs/SECRET_MANAGEMENT.md`
- `CODEOWNERS`, `.pre-commit-config.yaml`, `.gitleaks.toml`

#### Added (Workstream 5)
- **Data Contracts** (`contracts/*.yaml` — 10 datasets)
- `src/contract_validation.py`, `scripts/validate_contracts.py`
- `docs/SCHEMA_EVOLUTION.md`
- CI stage `ContractValidation`
- `tests/unit/test_contract_validation.py` (12 tests)
- `requirements.txt`, `pyproject.toml`

