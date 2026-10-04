# 🔁 Idempotency & Late-Data Strategy

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04
> **Applies to:** Bronze, Silver, Gold layers of the Banking DLT Platform

---

## 1. What "Idempotent" Means Here

A pipeline is **idempotent** if running it once, twice, or ten times on the
same input produces **exactly the same output**.

For a banking pipeline this is not optional:
- NEFT/RTGS/CHAPS files are often **re-uploaded** by upstream systems after transient errors.
- Auto Loader may **re-list** a file after a checkpoint reset.
- Databricks Workflows may **retry** a task after a cluster failure.
- A backfill may be triggered while a scheduled run is still in progress.

Every one of these scenarios must not corrupt downstream data.

---

## 2. Idempotency Guarantees by Layer

| Layer | Guarantee | Mechanism |
|---|---|---|
| **Bronze** | Exactly-once file processing | Auto Loader checkpoints + `_source_file_path_hash` |
| **Silver (transactions)** | Business-level dedup | `dropDuplicatesWithinWatermark(transaction_id, source_system, event_version)` |
| **Silver (reference data)** | Deterministic upsert | `sequence_by` = source-event time (`_record_updated_at`) |
| **Gold (dimensions)** | SCD2 correctness across retries | `apply_changes` with source-event sequencing |
| **Gold (facts)** | Deterministic reconstruction | Historical / as-of join |

### 2.1 Why `uuid()` Is Banned

`F.expr("uuid()")` was used in the original design as a batch ID. **It is
non-deterministic.** Two runs on the same input produce different IDs.
Any downstream logic keyed on it will break under retry.

**Replacement:** `_ingest_sequence = sha2(file_path || "|" || file_mtime, 256)`
— same file → same sequence, forever.

---

## 3. Business Idempotency Key

For transactions, the idempotency key is:




### Why not `transaction_id` alone?

Different source systems can generate **colliding** `transaction_id`s. For example:

| source_system | transaction_id | Meaning |
|---|---|---|
| `CORE_BANKING` | `TXN-12345` | Customer payment |
| `UPI`          | `TXN-12345` | UPI transaction (different namespace) |
| `NEFT`         | `TXN-12345` | Batch settlement line |

They are **three different transactions**. Deduping on `transaction_id` alone
would drop two of them.

### Why `event_version`?

If a source system **re-emits** the same transaction with updated fields
(e.g., a correction), the `event_version` bumps from 1 to 2. This is a
**new business event**, not a duplicate — it should be retained.

---

## 4. Late Data — Never Silently Dropped

### 4.1 The Watermark

`silver_transactions` uses:

```python
.withWatermark("transaction_timestamp", "24 hours")