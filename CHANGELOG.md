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