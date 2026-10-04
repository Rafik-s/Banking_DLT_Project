# 📋 Data Contracts

> **Owner:** Data Platform Engineering
> **Governance:** Every source dataset MUST have a contract before it can land in Bronze.

---

## What Is a Data Contract?

A **data contract** is a formal, versioned agreement between:

- The **source system** (e.g., Core Banking Platform)
- The **data platform** (this repo)

It specifies:
- The **schema** (columns, types, nullability)
- The **primary key** (for idempotency)
- The **event time** column (for watermarking / SCD2)
- The **SLA** (frequency, expected volume)
- The **classification** (public / internal / confidential / restricted)
- The **PII / PCI / DPDP** flags per column
- The **change log** (semver history)

---

## Why Contracts Matter

Without a contract:
- The source can add a column → pipeline silently ingests it → downstream breaks
- The source can change a type → casts silently succeed → data corruption
- The source can rename a field → pipeline fails at 2 AM → no documented agreement

With a contract:
- Every change is **versioned**, **reviewed**, and **approved**
- Schema drift is **detected in CI**, not in Prod
- Downstream consumers know exactly what to expect
- Auditors can point to a **single source of truth**

---

## Contract Lifecycle


│ 1. PROPOSE │
│ Source team + Data Platform agree on schema │
│ PR adds/modifies contracts/{dataset}.yaml │
│ Version bump: MAJOR (breaking) / MINOR (additive) / PATCH (docs)│
└──────────────────────────────┬──────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. VALIDATE (CI) │
│ - YAML syntax valid │
│ - Validates against contracts/_schema.yaml │
│ - Matches the actual Python StructType in src/schemas │
│ - Backward compatibility check against previous version │
└──────────────────────────────┬──────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. REVIEW │
│ - Data Platform Engineering │
│ - Source system owner │
│ - (If PII/PII changed) InfoSec + Compliance │
└──────────────────────────────┬──────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. MERGE + DEPLOY │
│ - Contract merged to main │
│ - Python schema in src/schemas_and_security.py updated │
│ - Bronze pipeline redeployed │
└──────────────────────────────┬──────────────────────────────────┘
▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. ENFORCE (runtime) │
│ - Auto Loader schema matches contract (fail-on-drift) │
│ - Silver expectations align with contract enums │
│ - DQ metrics keyed by contract version │



---

## Versioning Rules

We follow **semver** with strict definitions:

| Bump | Meaning | Example | Backward compatible? |
|---|---|---|---|
| **PATCH** | Doc-only change | Fix typo in description | ✅ Yes |
| **MINOR** | Additive change | Add `merchant_category` column | ✅ Yes (old code ignores new column) |
| **MAJOR** | Breaking change | Rename `amt` → `amount`, drop a column, change type | ❌ No — requires downstream migration |

**MAJOR changes require:**
- A migration plan documented in `change_log`
- Downstream consumer sign-off
- Coordinated release (source + platform deploy together)

---

## Adding a New Dataset

1. Copy `_schema.yaml` — understand the required fields.
2. Create `contracts/{dataset}.yaml` following the examples.
3. Add a `StructType` in `src/schemas_and_security.py` matching the contract exactly.
4. Add ingestion in `src/bronze_ingestion.py`.
5. Run `python scripts/validate_contracts.py --dataset {dataset}`.
6. Open PR.

---

## Schema Drift Handling

If the source system changes without updating the contract, the pipeline
**fails loudly** in Dev, not silently in Prod:

- `cloudFiles.schemaEvolutionMode = failOnNewColumns`
- `rescuedDataColumn` captures rows that don't match
- `expect_or_fail("schema_not_rescued", "_rescued_data IS NULL")` in Bronze

**Response procedure:**
1. Pipeline fails → on-call notified
2. Compare source CSV schema to contract
3. If change is legitimate:
   - Open PR to update contract + Python schema
   - Get source-owner approval
   - Merge, redeploy
4. If change is unauthorized:
   - Contact source team
   - Block until reverted

---

## Contract Validation in CI

Every PR runs:

```bash
python scripts/validate_contracts.py --all


This verifies:

YAML parses

Validates against _schema.yaml

Matches the Python StructType in src/schemas_and_security.py

Backward-compatible with the previous version (semver rules)

See .azure-pipelines/azure-pipelines.yml for the exact stage.

Anti-Patterns
❌ Don't	✅ Do
Change the Python schema without updating the contract	Update both in the same PR
Add a nullable column silently	Bump MINOR version, document in change_log
Rename a field "quietly"	Bump MAJOR, coordinate with consumers
Use inferSchema	Use explicit schema from contract
Store the contract in someone's email	Store it in contracts/ in Git
Approve your own contract change	Require review from source team
Change Log
Date	Change	Author
2026-10-04	Initial contract framework	Data Platform Engineering


