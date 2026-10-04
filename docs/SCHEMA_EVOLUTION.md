# 🔄 Schema Evolution Policy

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04
> **Approval authority:** Source system owner + Data Platform lead

---

## 1. Principle

**Schema evolution must be intentional, versioned, and reviewed.**

No source system may change the schema it publishes without a corresponding
contract version bump and a coordinated release. Bronze is append-only —
schema drift that isn't caught at ingest becomes a permanent data quality issue.

---

## 2. What Counts as Schema Evolution?

| Change | Breaking? | Contract Version |
|---|---|---|
| Add nullable column at the end | ❌ No | MINOR |
| Add NOT NULL column | ✅ Yes | MAJOR |
| Rename a column | ✅ Yes | MAJOR |
| Change a column type (string → int) | ✅ Yes | MAJOR |
| Widen decimal (18,2 → 20,2) | ❌ No | MINOR |
| Narrow decimal (18,2 → 16,2) | ✅ Yes | MAJOR |
| Reorder columns | ✅ Yes (positional CSV) | MAJOR |
| Drop a column | ✅ Yes | MAJOR |
| Change nullability (nullable → NOT NULL) | ✅ Yes | MAJOR |
| Change nullability (NOT NULL → nullable) | ❌ No | MINOR |
| Add new enum value | ❌ No | MINOR |

---

## 3. The Process

### 3.1 Source team notifies Data Platform

**SLA:** 5 business days before the change goes live.

Notification includes:
- Dataset name
- Proposed change
- New contract version
- Effective date
- Reason

### 3.2 Data Platform opens a PR


contracts/{dataset}.yaml ← version bump + change_log
src/schemas_and_security.py ← updated StructType
src/bronze_ingestion.py ← if applicable
CHANGELOG.md ← document the change



### 3.3 CI validates

- Contract schema valid
- Python schema matches
- Backward-compatibility check passes (or MAJOR bump approved)

### 3.4 Review and approval

| Change type | Required approvals |
|---|---|
| PATCH | Data Platform (1) |
| MINOR | Data Platform (1) + Source owner (1) |
| MAJOR | Data Platform (1) + Source owner (1) + Compliance (1) |

### 3.5 Coordinated release

For MINOR and MAJOR changes:
- Source team deploys on Day X
- Data Platform deploys on Day X
- Validation window: 24 hours (rollback if issues)

---

## 4. Bronze Ingestion Behavior

### 4.1 On Valid Change

If the pipeline's `StructType` matches the new schema and the contract is updated:

```python
cloudFiles.schemaEvolutionMode = "failOnNewColumns"


4.2 On Unauthorized Drift
If the source adds a column without a contract update:

text
Exception: A file was added, but the schema doesn't match the expected schema.
New column: merchant_category
→ Pipeline fails. On-call is paged. Response:

Stop the pipeline (it's already stopped by the failure).

Compare source CSV columns to contract.

Contact source team — either revert or open a contract PR.

Backfill any files that arrived during the outage.

4.3 On Rescued Data
If a row's column count or position is off but the header matches:

text
_rescued_data = '{"merchant_category": "GROCERY"}'
→ Row lands in Bronze with _rescued_data populated. Silver fails on
_rescued_data IS NOT NULL (Workstream 2 pattern).

5. Downstream Impact
Every schema change affects:

Layer	Impact
Bronze	Additive only (append-only, never rewritten)
Silver	Transformations may need updates (e.g., new enum in expect_or_drop)
Gold	Dimensions/facts may need new columns
BI / Dashboards	Consumer notification required
Reconciliation	Amount columns must not change type
Consumers must be notified for any MINOR or MAJOR change. The consumers:
list in each contract is the source of truth.

6. Rollback
If a schema change causes issues in Prod:

Revert the contract — git revert <commit>

Redeploy — databricks bundle deploy -t prod

Pipeline reprocesses with the old schema

Source team reverts on their side

Note: Bronze is append-only. Any rows ingested during the change window
remain in Bronze with the new schema. A backfill (or a rescue process) may
be needed to align them.

7. Future: Schema Registry
This repo uses YAML contracts in Git as the schema registry. For larger
organizations, consider:

Confluent Schema Registry (if Kafka is used)

Unity Catalog schemas as source of truth

Protobuf / Avro with .proto / .avsc files

The contract structure in contracts/ is designed to migrate cleanly to any
of these.

8. Change Log
Date	Change	Author
2026-10-04	Initial policy	Data Platform Engineering


---

## 📄 File 19 (PATCH): `CHANGELOG.md`

Add under `## [Unreleased]`:

```markdown
### Added
- **Data Contracts framework** (`contracts/`)
  - One YAML contract per dataset, versioned with semver
  - Meta-schema in `contracts/_schema.yaml`
  - Enforced in CI via `scripts/validate_contracts.py`
  - Runtime validation in `src/contract_validation.py`
- Contract versioning policy documented in `contracts/README.md`
- `docs/SCHEMA_EVOLUTION.md` — evolution policy + approval workflow
- `tests/unit/test_contract_validation.py` — 12 unit tests
- CI stage `ContractValidation` (runs after SecurityScans)
- `requirements.txt` and `pyproject.toml` for dev dependencies

### Changed
- `src/bronze_ingestion.py` — contract validation integrated into reader
- `.azure-pipelines/azure-pipelines.yml` — added contract validation stage
- `cloudFiles.schemaEvolutionMode = failOnNewColumns` — pipeline fails loudly on drift

### Fixed
- Schema drift now detected in CI, not in Prod
- Documented approval workflow for schema changes

