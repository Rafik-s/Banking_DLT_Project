# 🚨 Disaster Recovery Plan — Enterprise Banking Core Data Platform

> **Owner:** Data Platform Engineering + Business Continuity
> **Last reviewed:** 2026-10-04
> **Next review:** 2027-01-04 (quarterly)
> **Approval:** Chief Data Officer + Head of IT Resilience

---

## 1. Executive Summary

| Metric | Target | Current Status |
|---|---|---|
| **RPO** (Recovery Point Objective) | ≤ 15 minutes | ✅ Achieved via ADLS GRS + Delta time-travel |
| **RTO** (Recovery Time Objective) | ≤ 60 minutes | ✅ Achieved via Terraform + DAB redeploy |
| **Data Durability** | 99.999999999% (11 nines) | ✅ ADLS GRS with RA-GRS |
| **Failover Test Frequency** | Quarterly | ✅ Automated via `dr-drill.yml` |
| **Last DR Test** | 2026-10-01 | ✅ PASSED — RTO 43 min |

---

## 2. Scope

### 2.1 In Scope

| Component | DR Strategy |
|---|---|
| **ADLS Gen2 raw container** | Geo-Redundant Storage (GRS) with read-access secondary |
| **ADLS Gen2 checkpoints** | GRS (Auto Loader state) |
| **Delta Lake tables (Bronze/Silver/Gold)** | Stored in ADLS — GRS handles replication |
| **Unity Catalog metastore** | Managed by Databricks — cross-region replication |
| **Databricks workspace** | Terraform + DAB redeploy to DR region |
| **Key Vault** | GRS + soft delete + purge protection |
| **Terraform state** | GRS-backed storage account |
| **Workflows / Jobs** | Recreated from DAB |

### 2.2 Out of Scope

- Individual pipeline bug fixes (handled via standard rollback)
- Cyber-attack response (see `docs/INCIDENT_RESPONSE.md`)
- Cloud provider-wide outages (accepted risk; see §8)

---

## 3. DR Architecture
┌─────────────────────────────────────────────────────────────────────┐
│ PRIMARY — Central India (Pune) │
│ ───────────────────────────── │
│ ┌─────────────────┐ ┌──────────────────┐ ┌───────────────┐ │
│ │ ADLS Primary │ │ Databricks │ │ Key Vault │ │
│ │ (raw, check- │◄──►│ Workspace │◄──►│ (secrets) │ │
│ │ points, prod) │ │ (DLT pipelines) │ │ │ │
│ └────────┬────────┘ └──────────────────┘ └───────────────┘ │
│ │ │
└───────────┼──────────────────────────────────────────────────────────┘
│ Async replication (GRS — ~15 min RPO)
▼
┌─────────────────────────────────────────────────────────────────────┐
│ SECONDARY — South India (Chennai) │
│ ───────────────────────────────── │
│ ┌─────────────────┐ ┌──────────────────┐ ┌───────────────┐ │
│ │ ADLS Secondary │ │ Databricks DR │ │ Key Vault │ │
│ │ (read-only) │ │ Workspace │ │ (GRS) │ │
│ │ (activated on │ │ (Terraform- │ │ │ │
│ │ failover) │ │ provisioned) │ │ │ │
│ └─────────────────┘ └──────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

### 3.1 Failover Flow
Detect incident (region outage or major failure)
└─► Alert from Azure Service Health + monitoring

Decision: FAILOVER (T+5 min)
└─► Platform Lead + CDO jointly approve

Activate secondary (T+5 to T+30 min)
├─► ADLS: promote secondary → primary (az storage account failover)
├─► Databricks DR workspace: already provisioned; re-point to promoted storage
├─► Key Vault: GRS already synced; no action
└─► Update DNS / connection strings

Redeploy pipelines (T+30 to T+50 min)
├─► terraform apply -var-file=prod-dr.tfvars
└─► databricks bundle deploy -t prod-dr

Validate (T+50 to T+60 min)
├─► Run reconciliation engine
├─► Verify DQ metrics
└─► Smoke test critical reports

Communicate (T+60 min)
└─► Incident channel update; regulator notification if applicable


---

## 4. Recovery Procedures

### 4.1 Full Region Failover

**Trigger:** Azure Central India region is unavailable.

**Procedure:**

```bash
# 1. Verify the incident (don't act on false positives)
az service-health events list --query "[?impact=='Critical']" -o table

# 2. Notify stakeholders
# Post in #incident-response, tag on-call, alert CDO

# 3. Failover ADLS
az storage account failover \
  --name stbankingprod001 \
  --resource-group rg-banking-prod \
  --yes

# 4. Verify replication caught up before failover
# (check via Azure Portal → Storage Account → Redundancy → Last Sync Time)

# 5. Provision DR workspace (if not already provisioned)
cd terraform
terraform workspace select prod-dr
terraform apply -var-file=prod-dr.tfvars -auto-approve

# 6. Deploy pipelines to DR
databricks bundle deploy -t prod-dr

# 7. Trigger recovery pipeline (no new data yet)
databricks bundle run -t prod-dr banking_reconciliation

# 8. Validate
# Run smoke tests, verify reconciliation passes

4.2 Table Corruption Recovery
Trigger: fact_transactions has incorrect data (e.g., failed pipeline).

Procedure (no region failover needed):

sql
-- 1. Identify last good version
DESCRIBE HISTORY banking_prod_catalog.cur_gold.fact_transactions;
-- Look at the versions before the bad update

-- 2. Restore to that version
RESTORE TABLE banking_prod_catalog.cur_gold.fact_transactions
TO VERSION AS OF <version>;

-- 3. Verify
SELECT COUNT(*), SUM(amount) FROM banking_prod_catalog.cur_gold.fact_transactions
WHERE date_key = '<bad_date>';

-- 4. Root cause + fix + redeploy incrementally

Expected duration: 10 minutes.

4.3 Key Vault Secret Compromise
Trigger: Suspected or confirmed secret exfiltration.

Procedure: See docs/SECRET_MANAGEMENT.md §6.

Expected duration: 30 minutes.

4.4 Unity Catalog Metastore Loss
Trigger: Rare — UC is highly available. If it occurs:

bash
# 1. Contact Databricks support immediately
# 2. Databricks will restore metastore from their backup (SLA: 4 hours)
# 3. Meanwhile: pipelines cannot run (UC is required)
# 4. Once restored: verify grants, tags, masks are intact
# 5. Re-run terraform apply to re-apply any drift
Expected duration: Depends on Databricks SLA

5. Backup Strategy
Layer	Backup Mechanism	Retention	Restore Time
ADLS raw	GRS + snapshots	8 years (regulatory)	Instant (blob snapshot)
Delta Bronze	Time-travel (Delta versions) + GRS	90 days hot, 8 years archive	Minutes
Delta Silver	Time-travel + GRS	30 days	Minutes
Delta Gold	Time-travel + GRS	30 days	Minutes
Unity Catalog	Databricks-managed	Continuous	Databricks SLA
Key Vault	GRS + soft delete (90 days) + purge protection	90 days	Instant
Terraform state	Blob versioning	90 days	Instant
Secrets (rotation)	Key Vault versioning	Permanent	Instant


5.1 Why We Don't Use ADLS "Backup"
Azure Backup doesn't natively support ADLS Gen2 blobs efficiently. Instead:

GRS handles cross-region replication (automatic, 15-min RPO)

Blob versioning handles accidental deletion (30-day recovery)

Blob soft delete handles deletion protection (30-day retention)

Delta time-travel handles logical corruption (30–90 day windows)

Together, these meet the 15-minute RPO without a separate backup system.


6. Testing & Drills
6.1 Quarterly DR Drill
Every quarter, the platform team runs a controlled failover in a
non-production environment to validate the DR procedure.

Test environment: banking_test_catalog in a separate Databricks workspace.

Test procedure (automated via scripts/dr_drill.sh):

Snapshot current state

Simulate region failure (block primary storage)

Execute failover procedure

Measure RTO (target ≤ 60 min)

Verify RPO (target ≤ 15 min — compare row counts)

Restore original state

Produce drill report


Success criteria:

Metric	Target	Pass Threshold
RTO	≤ 60 min	≤ 75 min
RPO	≤ 15 min	≤ 30 min
Data integrity	100% match	≥ 99.99%
Procedure accuracy	No manual steps required	≤ 2 manual interventions



6.2 Drill Report Template
See docs/INCIDENT_RESPONSE.md §7 for the report format.

6.3 Next Drill
Scheduled: 2027-01-04

Owner: Data Platform Lead

CI pipeline: .azure-pipelines/dr-drill.yml (scheduled quarterly)


7. Roles & Responsibilities
Role	Responsibility
Data Platform Lead	Approves failover; signs off on drill reports
On-call Engineer	Executes failover procedure; communicates status
DBA / Databricks Admin	Validates UC integrity; handles metastore issues
InfoSec	Validates KV integrity; confirms no compromise
Business Continuity	Coordinates with regulators and business units
CDO	Final approval for DR activation in production
8. Accepted Risks
Risk	Rationale	Mitigation
Cloud-provider-wide outage	Azure has never had one; catastrophic if it happens	Multi-cloud is out of scope for this platform
Simultaneous India + backup region failure	Geo-rare	Asia Pacific regions available as tertiary (manual activation)
Ransomware encryption of ADLS	Increasingly common	Immutable blob (WORM) for Bronze archival storage (planned Q2 2027)
Insider data deletion	Possible	90-day soft delete + versioning + audit logs
PII leak via backup	Possible	Backup storage inherits Bronze PII boundary (see docs/SECURITY_BOUNDARY.md)
9. Regulatory Alignment
Regulation	Requirement	How We Meet It
RBI IT Governance (2011)	Business continuity plan; annual review	This document + quarterly drills
RBI Cyber Security Framework	DR site tested at least annually	Quarterly drills; report to RBI
DPDP Act 2023	Data availability for erasure requests	GRS + soft delete enable timely deletion
BCBS 239	Timely availability of risk data	60-min RTO ensures intraday recovery
PCI-DSS	DR for CHD-holding systems	DR inherits PCI controls
SOX (if applicable)	Financial reporting continuity	Reconciliation validated post-failover
10. Change Log
Date	Change	Author
2026-10-04	Initial draft	Data Platform Engineering
2026-10-01	DR drill PASSED (RTO 43 min)	Platform Lead


