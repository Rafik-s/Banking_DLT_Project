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