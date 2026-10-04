
---

## 📄 File 6 (NEW): `docs/INCIDENT_RESPONSE.md`

```markdown
# 🚨 Incident Response

> **Owner:** InfoSec + Data Platform Engineering
> **Last reviewed:** 2026-10-04

---

## 1. Severity Levels

| Severity | Definition | Examples | Response Time |
|---|---|---|---|
| **SEV-1** | Complete platform outage OR PII breach OR financial loss | Region failure; Aadhaar leak; CR ≠ DR in Prod | **15 min** |
| **SEV-2** | Major functionality broken | Reconciliation FAIL; pipeline stuck; DQ < 95% | **30 min** |
| **SEV-3** | Degraded but functional | DQ < 99%; quarantine > 1000/day; slow queries | **2 hours** |
| **SEV-4** | Minor issue, no impact | Documentation bug; typo | **Next business day** |

---

## 2. Incident Lifecycle

DETECT → TRIAGE → CONTAIN → RESOLVE → POST-MORTEM

text

### 2.1 Detect

Sources:
- Automated alerts (Workflow, PagerDuty)
- Business user report
- Auditors / regulators
- InfoSec monitoring

### 2.2 Triage (first 15 min)

1. **Acknowledge** the alert in PagerDuty
2. **Open incident channel** in Teams (`#incident-<id>`)
3. **Assign severity** (SEV-1 to SEV-4)
4. **Notify**:
   - SEV-1: Platform Lead, CDO, CISO, Head of IT Resilience
   - SEV-2: Platform Lead
   - SEV-3/4: Team channel only

### 2.3 Contain

Limit the blast radius:
- **SEV-1 PII breach:** revoke access, rotate secrets, preserve logs
- **SEV-1 outage:** activate DR (see `docs/DR_PLAN.md`)
- **SEV-2 reconciliation FAIL:** halt reports, notify business

### 2.4 Resolve

Fix the root cause, verify via reconciliation + DQ, resume operations.

### 2.5 Post-Mortem

Required for **SEV-1 and SEV-2**. Held within **5 business days**.

---

## 3. Communication Template
🚨 INCIDENT: <ID>
SEVERITY: SEV-X
STATUS: [INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED]
IMPACT: <description>
START TIME: <UTC>
CURRENT UPDATE: <what's happening>
NEXT UPDATE: <time>
OWNER: <on-call name>


---

## 4. Common Incident Playbooks

### 4.1 Pipeline Failure (SEV-2)

1. Check DLT event log (§3 of RUNBOOK.md)
2. Identify failing expectation / source drift / infrastructure issue
3. Roll back to previous version if corrupted data landed
4. Fix root cause
5. Resume

### 4.2 PII Breach (SEV-1)

1. **IMMEDIATELY** disable the access path (revoke grant, disable SP)
2. **Preserve logs** — do NOT delete anything
3. Notify InfoSec + CISO
4. Identify scope (what data, how many records)
5. DPDP breach notification within 72h if customer data involved
6. Customer notification if required
7. Regulator notification if required
8. Root cause analysis
9. Remediation plan

### 4.3 Reconciliation FAIL (SEV-2)

1. Halt downstream reports
2. Identify failing check (see §4 of RUNBOOK.md)
3. If CR ≠ DR — escalate to SEV-1 (financial integrity)
4. Resolve at root (source fix or transformation fix)
5. Verify via re-reconciliation
6. Resume reporting

### 4.4 Region Outage (SEV-1)

1. Confirm via Azure Service Health
2. Approve failover (Platform Lead + CDO)
3. Execute DR failover (see `docs/DR_PLAN.md` §4.1)
4. Validate via reconciliation
5. Communicate status hourly

---

## 5. Post-Mortem Template

```markdown
# Post-Mortem: <INCIDENT-ID>

**Date:** YYYY-MM-DD
**Severity:** SEV-X
**Duration:** <HH:MM>
**Impact:** <description>
**Author:** <name>

## Timeline (all times UTC)
- HH:MM — Alert triggered
- HH:MM — Acknowledged by <name>
- HH:MM — Root cause identified
- HH:MM — Fix deployed
- HH:MM — Verified resolved

## Root Cause
<technical description>

## What Went Well
- <positive observation>

## What Went Wrong
- <issue>

## Action Items
| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Add test for <case> | <name> | YYYY-MM-DD |
| 2 | Update runbook §X | <name> | YYYY-MM-DD |

## Lessons Learned
<key takeaways>

6. Regulatory Notification Requirements
Regulation	Trigger	Timeline	Contact
DPDP Act 2023	Personal data breach	72 hours	Data Protection Board of India
RBI Cyber Security	Major cyber incident	2–6 hours	RBI + CERT-In
PCI-DSS	Cardholder data breach	24 hours	Acquiring bank + card networks
GDPR (if EU customers)	Personal data breach	72 hours	Supervisory Authority
SOX (if applicable)	Financial reporting impact	24 hours	Audit Committee

7. DR Drill Report Template
markdown
# DR Drill Report — Q<N> YYYY

**Date:** YYYY-MM-DD
**Environment:** banking_test_catalog
**Participants:** <names>

## Objectives
- Verify failover procedure
- Validate RTO and RPO
- Identify gaps

## Results

| Metric | Target | Actual | Status |
|---|---|---|---|
| RTO | ≤ 60 min | <XX> min | ✅/❌ |
| RPO | ≤ 15 min | <XX> min | ✅/❌ |
| Data integrity | ≥ 99.99% | <XX.XX>% | ✅/❌ |
| Manual interventions | ≤ 2 | <N> | ✅/❌ |

## Issues Encountered
- <issue>

## Action Items
| # | Action | Owner | Due |
|---|---|---|---|

## Next Drill
**Scheduled:** YYYY-MM-DD
8. Change Log
Date	Change	Author
2026-10-04	Initial draft	InfoSec + Data Platform Engineering


