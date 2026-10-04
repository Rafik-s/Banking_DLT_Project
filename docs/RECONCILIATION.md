# 🧾 Banking Reconciliation Framework

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04
> **Regulatory scope:** RBI, BCBS 239, internal audit
> **SLAs:** Daily reconciliation must complete by 04:00 IST. All checks must PASS.

---

## 1. Why Reconciliation Is Non-Negotiable

In a bank, **a report is only as good as the numbers in it**. If the
transaction count in the warehouse doesn't match the source system, then:

- Regulatory reports (CRR, LCR) are wrong → RBI finding
- Customer statements are wrong → DPDP / consumer protection issue
- Risk calculations are wrong → BCBS 239 violation
- Finance's P&L doesn't tie → audit qualification

Reconciliation is **how you prove the numbers are correct**. It is the
single most important control in a banking data platform.

---

## 2. The Three Layers of Reconciliation

### Layer 1 — Row Count Reconciliation

> *"Did we receive every record the source sent?"*

| From | To | Expected |
|---|---|---|
| `bronze_transactions` | `silver_transactions + quarantine + late` | Equal |
| `silver_transactions` | `fact_transactions` | Equal (for closed business dates) |
| `silver_loans` | `fact_loans` | Equal |

### Layer 2 — Amount Reconciliation

> *"Do the money amounts tie out?"*

| Metric | Expected |
|---|---|
| `SUM(bronze.amount)` | `= SUM(silver.amount)` |
| `SUM(silver.amount)` | `= SUM(gold.amount)` |
| `SUM(loans.outstanding_principal)` | `= SUM(fact_loans.outstanding_principal)` |

### Layer 3 — Double-Entry Integrity

> *"Do credits equal debits?"*

For a well-formed transaction journal:






Any imbalance is **immediate FAIL**, regardless of tolerance. This is a
zero-tolerance check.

---

## 3. Status Semantics

| Status | Meaning | On-call action |
|---|---|---|
| **PASS** | Counts match exactly, amount diff = 0 | None |
| **WARNING** | Within tolerance (e.g. rounding), but not exact | Investigate within 24h |
| **FAIL** | Outside tolerance OR any count mismatch | Page on-call immediately |
| **SKIPPED** | Upstream data unavailable (e.g., holiday) | Verify next business day |

### Tolerance

Default: `tolerance_pct = 0.0001` (0.01%).

This allows for **rounding** in financial aggregation while still catching
real discrepancies. For **count reconciliation**, tolerance is **0** —
row counts must match exactly.

---

## 4. What Happens When a Check Fails

1. **Immediate:** `sys.exit(1)` in the reconciliation notebook.
2. **Workflow:** Databricks Workflow marks the task as `FAILED`.
3. **Alert:** Webhook fires → Teams `#data-platform-alerts`.
4. **Page:** PagerDuty triggers for `data-oncall`.
5. **Investigation:** On-call runs `SELECT * FROM cur_gold.reconciliation_failures`.
6. **Root cause:**
   - **Missing source file** → contact upstream team, replay file
   - **Transformation bug** → roll back pipeline, fix code
   - **Late data** → confirm it's in `silver_transactions_late`, replay
   - **Duplicate** → verify idempotency key, run corrective merge
7. **Sign-off:** Reconciliation must show PASS before close of business.
8. **Post-mortem:** Required for any FAIL, documented in `docs/incidents/`.

---

## 5. How to Re-Run Reconciliation Manually

After fixing the root cause:

```bash
databricks bundle run -t prod banking_reconciliation \
  --params business_date=2026-10-03