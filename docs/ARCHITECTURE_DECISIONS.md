# 📐 Architecture Decision Records (ADRs)

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04

This document captures the key architectural decisions for this reference
implementation. Each ADR follows the pattern: **Context → Decision → Consequences → Alternatives Considered**.

---

## ADR-001: Spark Auto Loader over `spark.read.csv`

**Date:** 2026-10-04
**Status:** Accepted

### Context
Banking data arrives as CSV files dropped into ADLS Gen2 by upstream systems.
We need exactly-once ingestion with schema enforcement.

### Decision
Use **Spark Auto Loader** (`cloudFiles` format) for all Bronze ingestion.

### Consequences
- ✅ Exactly-once via checkpointing (no duplicate processing on retry)
- ✅ Schema evolution support (fail-loudly on unexpected changes)
- ✅ File-level lineage via `_metadata` columns
- ✅ Late-file detection via `backfillInterval`
- ⚠️ Requires a checkpoint directory per dataset
- ⚠️ Adds Auto Loader startup time (small)

### Alternatives Considered
- **`spark.read.csv` with `mode=overwrite`** — rejected: not idempotent, destroys audit trail
- **Event Hubs / Kafka** — rejected: source systems publish files, not streams (for now)
- **ADF copy activity** — rejected: doesn't carry DLT metadata; lacks streaming semantics

---

## ADR-002: Delta Live Tables over plain notebooks

**Date:** 2026-10-04
**Status:** Accepted

### Context
The pipeline must produce tables with data quality enforcement, lineage, and
automatic orchestration, and be maintainable by a small team.

### Decision
Use **Delta Live Tables (DLT)** as the pipeline engine.

### Consequences
- ✅ Declarative expectations with automatic metrics
- ✅ Unity Catalog lineage built-in
- ✅ Auto-managed compute + orchestration
- ✅ `APPLY CHANGES INTO` for SCD2
- ⚠️ Vendor lock-in to Databricks
- ⚠️ Some advanced Spark patterns are harder in DLT

### Alternatives Considered
- **Plain PySpark notebooks + Workflows** — rejected: manual orchestration, no expectations
- **dbt + Databricks SQL** — rejected: doesn't handle streaming Auto Loader well
- **Apache Airflow + PySpark** — rejected: lacks DLT's managed experience

---

## ADR-003: SCD Type 2 via `APPLY CHANGES INTO`

**Date:** 2026-10-04
**Status:** Accepted

### Context
Customer, account, and other dimensions require full historical tracking
for BCBS 239 as-of-date reporting.

### Decision
Use **`dlt.apply_changes(..., stored_as_scd_type=2)`** for all historical dimensions.

### Consequences
- ✅ Auto-maintained `__START_AT` / `__END_AT` columns
- ✅ Deterministic sequencing via `sequence_by`
- ✅ Idempotent across retries
- ⚠️ Requires a source-event time column for `sequence_by`
- ⚠️ Requires SCD2-aware fact joins (as-of joins)

### Alternatives Considered
- **Manual MERGE with SCD2 logic** — rejected: error-prone; reinvents DLT
- **Snapshot-based historical tracking** — rejected: storage cost
- **SCD Type 1** — rejected: loses history, breaks regulatory reporting

### Known Issue
`dim_branches` and `dim_credit_cards` currently lack a source-event time
column in their source systems. Until the upstream systems provide
`last_modified_date`, these dimensions use `_ingestion_timestamp` for
`sequence_by`. This is retry-safe but not logically orderable.

---

## ADR-004: Business idempotency key for transactions

**Date:** 2026-10-04
**Status:** Accepted

### Context
Transactions may be re-delivered by upstream systems. `transaction_id` alone
is unique **per source system**, not globally.

### Decision
Idempotency key = `(transaction_id, source_system, event_version)`.

### Consequences
- ✅ Handles cross-system collisions
- ✅ Allows source-side correction (`event_version` bump = new row)
- ✅ Fail-fast if any component is missing
- ⚠️ Requires upstream to populate `source_system` and `event_version`

### Alternatives Considered
- **`transaction_id` alone** — rejected: not globally unique
- **Content hash of all columns** — rejected: expensive; breaks on whitespace
- **Databricks-generated `_ingest_sequence` alone** — rejected: replay produces different values

---

## ADR-005: Late data → quarantine (no silent drops)

**Date:** 2026-10-04
**Status:** Accepted

### Context
Spark watermarks drop rows older than the watermark window. In banking,
**silent data loss is not acceptable**.

### Decision
Rows past the watermark are routed to `silver_transactions_late` with a
`quarantine_reason` and `late_by_hours` metric. Alerting triggers when
volume exceeds threshold.

### Consequences
- ✅ No silent data loss
- ✅ Replayable once source system catches up
- ✅ Alertable
- ⚠️ Additional storage cost for quarantine table
- ⚠️ Requires operational process for replay

### Alternatives Considered
- **Silent drop** — rejected: unacceptable for banking
- **Unbounded watermark** — rejected: state grows indefinitely
- **Batch reprocessing on late arrival** — rejected: expensive; DLT streaming preferred

---

## ADR-006: HMAC via Unity Catalog function (salt in secret scope)

**Date:** 2026-10-04
**Status:** Accepted

### Context
PII (Aadhaar, PAN) needs deterministic matching (for joins) without storing
the raw value or exposing the salt.

### Decision
Use a **UC function `security.pii_hmac()`** that reads the salt from a
Databricks Secret Scope (backed by Azure Key Vault).

### Consequences
- ✅ Salt never in source code or Git
- ✅ UC audit logs every call
- ✅ Rotation possible without code change
- ⚠️ HMAC is not reversible; erasure requires salt-based unlinkability
- ⚠️ Requires strict grants (`REVOKE EXECUTE FROM account users`)

### Alternatives Considered
- **Salted SHA-256 with hardcoded salt** — rejected: brute-forceable; salt leaks
- **Plain SHA-256** — rejected: Aadhaar brute-force is trivial (10^12 space)
- **Format-preserving encryption** — rejected: overkill; not needed for joins
- **Third-party tokenization (Vault)** — rejected: adds infrastructure; HMAC is sufficient

---

## ADR-007: Reconciliation framework (count + amount + double-entry)

**Date:** 2026-10-04
**Status:** Accepted

### Context
A bank's data platform must prove that the numbers in the warehouse tie to
source systems. This is required by RBI, BCBS 239, and internal audit.

### Decision
Build a **first-class reconciliation engine** (`src/reconciliation.py`) that
runs daily and produces a queryable results table. Classifies as PASS /
WARNING / FAIL / SKIPPED. Pages on-call on FAIL.

### Consequences
- ✅ Regulatory reports can cite reconciliation results
- ✅ Reconciliation is a control, not an afterthought
- ✅ SLA reporting (30-day pass-rate)
- ⚠️ Requires source system to provide control totals (or trust file counts)
- ⚠️ Additional cost (one more Workflow job)

### Alternatives Considered
- **Ad-hoc SQL queries** — rejected: not scheduled, no history
- **Excel-based reconciliation** — rejected: not scalable, not auditable
- **Third-party reconciliation tool** — rejected: cost, integration overhead

---

## ADR-008: YAML data contracts (source of truth)

**Date:** 2026-10-04
**Status:** Accepted

### Context
Python `StructType` schemas were the only definition of the source schema.
No documented agreement; no versioning; no way to detect drift.

### Decision
Introduce **YAML data contracts** in `contracts/*.yaml`, validated in CI
against the Python schema. Semver rules enforced for schema changes.

### Consequences
- ✅ Formal agreement between source and platform
- ✅ Version history of schema changes
- ✅ CI-enforced backward compatibility
- ✅ Onboarding artefact for new datasets
- ⚠️ Requires discipline to keep in sync with Python schema
- ⚠️ Minor overhead per PR (contract update)

### Alternatives Considered
- **Python schema only** — rejected: no documented agreement
- **Confluent Schema Registry** — rejected: no Kafka in scope
- **Avro / Protobuf** — rejected: CSV source, not binary
- **Unity Catalog as schema registry** — considered; rejected for portability

---

## ADR-009: Liquid Clustering over Z-Ordering

**Date:** 2026-10-04
**Status:** Accepted

### Context
Delta tables need physical layout optimization for query performance.

### Decision
Use **Liquid Clustering** (`cluster_by`) on Gold fact tables.

### Consequences
- ✅ No need to run `OPTIMIZE ... ZORDER` manually
- ✅ Adaptive clustering as data distribution changes
- ✅ Better performance for high-cardinality columns
- ⚠️ Requires DBR 13.3+
- ⚠️ Not applicable for all workloads (small tables)

### Alternatives Considered
- **Z-Ordering** — rejected: deprecated in favor of Liquid Clustering
- **Partitioning** — rejected: too rigid; Liquid is more flexible
- **No optimization** — rejected: poor performance

---

## ADR-010: Workload Identity Federation for CI/CD

**Date:** 2026-10-04
**Status:** Accepted

### Context
CI/CD needs to authenticate to Azure and Databricks without storing long-lived
credentials.

### Decision
Use **Workload Identity Federation (WIF)** between Azure DevOps and Entra ID.
Databricks CLI authenticates via Azure CLI token exchange (`DATABRICKS_AUTH_TYPE=azure-cli`).

### Consequences
- ✅ No PATs, no secrets to rotate
- ✅ Short-lived OIDC tokens
- ✅ Audit trail through Entra
- ⚠️ Initial setup complexity (federated credential)
- ⚠️ Cannot be used locally (developers use `az login`)

### Alternatives Considered
- **PATs** — rejected: long-lived, high-risk
- **Service principal secrets** — rejected: still needs rotation
- **Managed Identity on self-hosted agent** — considered; WIF is simpler

---

## ADR-011: Disaster Recovery (active-passive)

**Date:** 2026-10-04
**Status:** Accepted

### Context
RBI mandates DR for banking systems. Need RPO ≤ 15 min, RTO ≤ 60 min.

### Decision
Use **active-passive DR** with ADLS GRS replication and a Terraform-provisioned
DR workspace. Failover is manual (approved by Platform Lead + CDO).

### Consequences
- ✅ Meets RBI requirements
- ✅ Cost-efficient (DR workspace idle)
- ✅ Simple to reason about
- ⚠️ Failover requires manual intervention (~45 min)
- ⚠️ Not suitable for tier-0 systems requiring < 5 min RTO

### Alternatives Considered
- **Active-active multi-region** — rejected: complexity; reserved for tier-0
- **Backup/restore only** — rejected: RTO too high (> 4 hours)
- **No DR** — rejected: regulatory violation

---

## ADR-012: Environment isolation (Dev / QA / Prod)

**Date:** 2026-10-04
**Status:** Accepted

### Context
Developers must not reach Prod data. Regulatory requirement (RBI, PCI).

### Decision
Full isolation per environment:
- Separate Azure subscriptions
- Separate VNets (no peering)
- Separate ADLS, Key Vault, Databricks workspaces
- Separate service principals
- Prod access only via PIM (just-in-time)

### Consequences
- ✅ Hard boundary — no accidental Prod access
- ✅ Meets RBI / PCI requirements
- ⚠️ More infrastructure to manage
- ⚠️ Data promotion requires explicit sync jobs

### Alternatives Considered
- **Shared subscription with RBAC** — rejected: insufficient isolation
- **Single workspace with catalog separation** — rejected: shared compute is a risk

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-10-04 | Initial 12 ADRs | Rafik-s |
