# 📖 Glossary

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04

Terms used throughout this repository and in banking data engineering.

---

## A

**ADR (Architecture Decision Record)**
A short document capturing a significant technical decision, its context,
and consequences. See [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md).

**APPLY CHANGES INTO**
DLT syntax for CDC-style merges with automatic SCD1 or SCD2 handling.
Replaces manual MERGE logic.

**Auto Loader**
Databricks feature (`cloudFiles`) for incrementally ingesting files from
cloud storage with exactly-once semantics, schema evolution, and checkpointing.

---

## B

**Bronze**
The raw ingestion layer of the Medallion Architecture. In this platform,
Bronze is **append-only**, immutable, and holds raw PII (restricted access).

**BCBS 239**
Basel Committee on Banking Supervision standard #239 — Principles for effective
risk data aggregation and risk reporting. Requires accurate, complete, timely data.

---

## C

**CDF (Change Data Feed)**
Delta Lake feature that emits row-level change events for downstream consumers.

**CIF (Customer Information File)**
A bank's unique identifier for a customer. Used interchangeably with `customer_id`.

**Contract (Data Contract)**
A formal, versioned agreement between a source system and the platform
specifying schema, nullability, primary key, event time, and classification.
See [`../contracts/`](../contracts/).

**CR / DR (Credit / Debit)**
Double-entry bookkeeping indicators. A transaction is either a credit (increases
balance) or debit (decreases balance).

---

## D

**DAB (Databricks Asset Bundle)**
Databricks' Infrastructure-as-Code format for defining pipelines, jobs,
and workspaces. Uses `databricks.yml` + YAML resources.

**DLT (Delta Live Tables)**
Databricks' declarative pipeline framework. Uses Python decorators
(`@dlt.table`, `@dlt.expect_*`) and manages orchestration, lineage, and quality.

**DPDP Act 2023**
India's Digital Personal Data Protection Act. Governs processing of personal
data, requires purpose limitation, data minimization, and right to erasure.

**DPD (Days Past Due)**
A loan classification metric. `dpd = 0` → current. `dpd > 90` → non-performing asset.

---

## E

**Expectation**
A data quality rule attached to a DLT table. Variants: `expect` (warn),
`expect_or_drop` (drop + metric), `expect_or_fail` (halt pipeline).

---

## F

**Fact Table**
A dimensionally-modeled table representing business events (transactions,
alerts, loan disbursements). Joined to dimensions for analysis.

---

## G

**Gold**
The business-ready layer of the Medallion Architecture. Contains star schema
(dimensions + facts) with SCD2 history. Consumed by BI tools.

**GRS / RA-GRS (Geo-Redundant Storage)**
Azure Storage replication options. GRS = 3 copies in primary region + 3 in
paired region. RA-GRS = GRS + read access to secondary.

---

## H

**HMAC (Hash-based Message Authentication Code)**
A keyed cryptographic hash. Used in this platform for PII (deterministic
matching without storing raw values).

---

## I

**Idempotency**
The property that running an operation N times produces the same result as
running it once. Critical for pipeline retry safety.

**IFSC Code**
Indian Financial System Code — an 11-character code identifying a bank branch
for electronic transfers.

---

## J

**JIT (Just-In-Time) Access**
Privileged access granted on-demand for a limited duration. Used in this
platform for Prod access via Azure PIM.

---

## K

**Key Vault (Azure Key Vault)**
Azure service for storing secrets, keys, and certificates. In this platform,
the PII HMAC salt lives here.

**KYC (Know Your Customer)**
RBI-mandated customer identification process. KYC documents include Aadhaar,
PAN, passport, etc.

---

## L

**Late Data**
Data that arrives after the pipeline's watermark window. In this platform,
late data is routed to a quarantine table rather than dropped.

**Liquid Clustering**
Modern Delta Lake physical layout technique that adaptively clusters data
by columns, replacing Z-Ordering.

---

## M

**Medallion Architecture**
A data design pattern with three layers: Bronze (raw), Silver (cleansed),
Gold (business-ready).

**Metastore (Unity Catalog)**
The top-level container for catalogs, schemas, tables, and grants in
Unity Catalog.

---

## N

**NPA (Non-Performing Asset)**
A loan classification. `dpd > 90` typically triggers NPA classification.

---

## P

**PAN (Permanent Account Number)**
Indian tax identifier — a 10-character alphanumeric code.

**PCI-DSS**
Payment Card Industry Data Security Standard. Governs handling of cardholder
data. Version 3.2.1 is referenced in this repo.

**PII (Personally Identifiable Information)**
Data that can identify an individual. Examples: name, Aadhaar, PAN, email, phone.

**PIM (Privileged Identity Management)**
Azure service for just-in-time privileged access with approval workflows.

**Private Endpoint**
An Azure network interface that connects you privately to a service (ADLS,
Key Vault, etc.) — traffic stays on the Microsoft backbone.

**Private Link**
Azure service for accessing PaaS over a private endpoint.

---

## R

**RBAC (Role-Based Access Control)**
Access control model based on roles. Used in Azure and Unity Catalog.

**Reconciliation**
The process of verifying that data across layers (source → Bronze → Silver → Gold)
ties out in count and amount. See [`RECONCILIATION.md`](RECONCILIATION.md).

**RPO (Recovery Point Objective)**
The maximum acceptable data loss, expressed in time. This platform: ≤ 15 minutes.

**RTO (Recovery Time Objective)**
The maximum acceptable downtime after a failure. This platform: ≤ 60 minutes.

---

## S

**SCD (Slowly Changing Dimension)**
Pattern for tracking history in dimension tables. Type 1 = overwrite; Type 2 = keep
full history with effective dates.

**Silver**
The cleansed layer of the Medallion Architecture. Contains deduplicated, masked,
type-enforced data.

**SMA (Special Mention Account)**
Loan classification for early delinquency (1–90 DPD).

**Structured Streaming**
Spark's stream processing engine. Underlies Auto Loader and DLT streaming tables.

---

## T

**Tag (Unity Catalog)**
Key-value metadata attached to tables or columns. Used here for PII classification
(`pii=aadhaar`, `dpdp=restricted`).

**Time Travel (Delta)**
Querying a Delta table as it existed at a previous version or timestamp.

---

## U

**UC (Unity Catalog)**
Databricks' governance layer. Provides a 3-level namespace
(`catalog.schema.table`), access controls, lineage, and auditing.

---

## V

**VNet (Azure Virtual Network)**
Isolated network in Azure. Databricks can be deployed VNet-injected.

**VNet Injection**
Deploying a Databricks workspace inside a customer-managed VNet with
dedicated public and private subnets.

---

## W

**Watermark**
A time bound for streaming data. Data older than the watermark is considered
"late" and either dropped or (in this platform) quarantined.

**WIF (Workload Identity Federation)**
Azure Entra ID feature allowing external identities (like Azure DevOps) to
authenticate without secrets. Used for CI/CD authentication.

**WORM (Write Once Read Many)**
Immutable storage that prevents modification after write. Used for regulatory
retention.

---

## Z

**Z-Ordering**
Legacy Delta Lake clustering technique. Being replaced by Liquid Clustering.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-10-04 | Initial glossary | Rafik-s |
