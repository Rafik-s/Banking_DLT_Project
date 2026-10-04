
---

## 📄 File 5 (NEW): `docs/RUNBOOK.md`

```markdown
# 📘 Operational Runbook

> **Owner:** Data Platform Engineering
> **Audience:** On-call engineers
> **Last reviewed:** 2026-10-04

---

## 1. On-Call Quick Reference

| Symptom | Section |
|---|---|
| Pipeline failed | §3 |
| Reconciliation FAIL | §4 |
| Data quality alert | §5 |
| Late data spike | §6 |
| Quarantine growth | §7 |
| Secret rotation due | §8 |
| DR activation | §9 |

---

## 2. Daily Checklist

Every morning at **07:00 IST**, on-call confirms:

- [ ] All pipelines completed successfully (Databricks Workflows)
- [ ] Reconciliation PASS for yesterday
- [ ] DQ pass rate ≥ 99% for all tables
- [ ] Quarantine row count < 100 for last 24h
- [ ] No alerts in Teams `#data-platform-alerts`
- [ ] Cost consumption within ±10% of baseline

If any check fails → go to the relevant section below.

---

## 3. Pipeline Failed

**1. Identify the failed table:**
```sql
SELECT * FROM event_log(TABLE(banking_prod_catalog.raw_bronze.bronze_transactions))
WHERE event_type = 'error'
  AND timestamp > current_timestamp() - INTERVAL 1 HOUR
ORDER BY timestamp DESC LIMIT 10;

2. Check for expect_or_fail violations:
sql
SELECT * FROM event_log(TABLE(banking_prod_catalog.clean_silver.silver_transactions))
WHERE event_type = 'flow_progress'
  AND details:flow_progress.data_quality.expectations IS NOT NULL
  AND timestamp > current_timestamp() - INTERVAL 1 HOUR;
3. Common causes:

Cause	Fix
expect_or_fail on PK	Check source for null PKs → contact upstream
Schema drift	See docs/SCHEMA_EVOLUTION.md
Storage access denied	Check Managed Identity + Private Endpoint
Out of memory	Increase cluster size or add repartition
Secret not found	Check Key Vault + Secret Scope
4. Retry:

bash
databricks bundle run -t prod banking_medallion_dlt_pipeline
5. If retry fails 2x → escalate to Platform Lead.

4. Reconciliation FAIL
1. Identify which check failed:

sql
SELECT * FROM banking_prod_catalog.cur_gold.reconciliation_failures
WHERE business_date = current_date() - 1;
2. Common scenarios:

Scenario	Diagnosis	Action
Bronze > Silver	DLT expectations dropped rows	Check DQ metrics; acceptable if within tolerance
Silver > Gold	FK join dropped rows	Check quarantine table
CR ≠ DR	Double-entry violation	CRITICAL — halt reporting; investigate source
Amount mismatch	Rounding or data corruption	Compare source vs Bronze vs Silver
3. For a CR ≠ DR violation:

sql
-- Identify the imbalance
SELECT
  db_cr_indicator,
  SUM(amount) AS total,
  COUNT(*) AS txn_count
FROM banking_prod_catalog.clean_silver.silver_transactions
WHERE date(transaction_timestamp) = current_date() - 1
GROUP BY db_cr_indicator;
Contact Core Banking team immediately. Do NOT publish reports until resolved.

5. Data Quality Alert
1. Open the DQ dashboard:

sql
SELECT * FROM banking_prod_catalog.cur_gold.dq_alerts;
2. For each failing expectation:

Expectation type	Action
expect_or_fail triggered	Pipeline is already stopped — see §3
expect_or_drop < 99%	Investigate root cause; check source file
expect warn only	Monitor trend; report if persists > 3 days
3. Trend analysis:

sql
SELECT
  metric_date,
  flow_name,
  expectation_name,
  pass_rate_pct
FROM banking_prod_catalog.cur_gold.dq_metrics_history
WHERE expectation_name = '<failing>'
  AND metric_date >= current_date() - 14
ORDER BY metric_date;
If the trend is declining → escalate to upstream team.

6. Late Data Spike
1. Check silver_transactions_late:

sql
SELECT
  DATE(_ingestion_timestamp) AS ingestion_date,
  COUNT(*)                    AS late_count,
  MAX(late_by_hours)          AS max_late_hours
FROM banking_prod_catalog.clean_silver.silver_transactions_late
WHERE _ingestion_timestamp >= current_timestamp() - INTERVAL 7 DAYS
GROUP BY 1 ORDER BY 1 DESC;
2. If max_late_hours > 48 → contact source team.

3. Replay late data:

bash
databricks bundle run -t prod banking_medallion_dlt_pipeline --full-refresh --select silver_transactions
7. Quarantine Growth
1. Check silver_transactions_quarantine:

sql
SELECT
  DATE(_ingestion_timestamp) AS ingest_date,
  COUNT(*) AS orphaned_count,
  COUNT(DISTINCT account_id) AS distinct_missing_accounts
FROM banking_prod_catalog.clean_silver.silver_transactions_quarantine
WHERE _ingestion_timestamp >= current_timestamp() - INTERVAL 7 DAYS
GROUP BY 1 ORDER BY 1 DESC;

2. If count > 1000/day → FK problem upstream. Escalate.

3. Investigate sample:

sql
SELECT account_id, COUNT(*) FROM banking_prod_catalog.clean_silver.silver_transactions_quarantine
WHERE DATE(_ingestion_timestamp) = current_date() - 1
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
4. Check accounts table:

sql
SELECT * FROM banking_prod_catalog.clean_silver.silver_accounts
WHERE account_id IN (<top-10-missing>);
8. Secret Rotation Due
Alert triggers 30 days before expiry.

1. Confirm the secret:

bash
az keyvault secret show --vault-name kv-banking-prod --name smtp-password --query attributes
2. Rotate:
See docs/SECRET_MANAGEMENT.md §5.

3. Verify:

bash
bash scripts/verify_key_vault.sh --env prod
9. DR Activation
Decision requires: Platform Lead + CDO.

Procedure: See docs/DR_PLAN.md §4.

Post-activation: Run scripts/dr_drill.sh --env prod --execute.

10. Escalation Matrix
Issue	First Contact	Escalation
Pipeline failure	On-call engineer	Platform Lead (15 min)
Reconciliation FAIL	On-call engineer	Platform Lead + Core Banking
Data breach	InfoSec	CISO + CDO
DR activation	Platform Lead	CDO + CRO
Secret compromise	InfoSec	CISO + InfoSec Lead
Storage failure	Cloud Platform	Microsoft Support (severity 1)

11. Useful Commands
bash
# Trigger a pipeline manually
databricks bundle run -t prod banking_medallion_dlt_pipeline

# Trigger reconciliation
databricks bundle run -t prod banking_reconciliation

# Full-refresh a specific table
databricks bundle run -t prod banking_medallion_dlt_pipeline \
  --full-refresh --select silver_transactions

# Check pipeline status
databricks pipelines get --pipeline-id <id>

# Check Workflow run history
databricks jobs list-runs --job-id <id> --limit 20

# Verify Terraform state
cd terraform && terraform state list

# Verify secrets
bash scripts/verify_key_vault.sh --env prod
12. Change Log
Date	Change	Author
2026-10-04	Initial runbook	Data Platform Engineering