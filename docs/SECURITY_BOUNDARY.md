# 🔒 Security Boundary — Bronze PII Zone

> **Document owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04
> **Review cadence:** Quarterly
> **Classification:** Internal — Restricted

---

## Purpose

This document defines the **security boundary** around the Bronze PII zone in the
Enterprise Banking Core Data Platform. It answers three questions:

1. **What** raw PII exists in Bronze?
2. **Who** can access it?
3. **How** is access enforced, audited, and reviewed?

This is a **mandatory review artefact** for:
- Internal Audit
- InfoSec Architecture Review Board
- DPDP Act 2023 RoPA (Record of Processing Activities)
- RBI IT Governance annual review

---

## 1. What PII Exists in Bronze?

Bronze is the **raw ingestion layer** — data lands here **unmodified** from source systems.
As a consequence, raw PII **is present** in the following Bronze tables:

| Bronze Table | PII Column | Classification | Regulatory Scope |
|---|---|---|---|
| `raw_bronze.bronze_customers` | `aadhaar_number` | Restricted | DPDP, RBI KYC |
| `raw_bronze.bronze_customers` | `pan_number` | Restricted | DPDP, RBI KYC |
| `raw_bronze.bronze_customers` | `email` | Confidential | DPDP |
| `raw_bronze.bronze_customers` | `phone` | Confidential | DPDP |
| `raw_bronze.bronze_credit_cards` | `card_number_raw` | PCI-Restricted | PCI-DSS |
| `raw_bronze.bronze_kyc_documents` | `document_number_raw` | Restricted | DPDP |
| `raw_bronze.bronze_employees` | `email` | Confidential | DPDP |
| `raw_bronze.bronze_employees` | `phone` | Confidential | DPDP |

### Why raw PII lands in Bronze

Bronze is **append-only and immutable** — it is the **audit trail of last resort**.
Regulators require the ability to **reconstruct the exact state** of a source record
at any point in time. If Bronze were masked at ingestion, we could never prove what
the source system actually sent.

**Therefore:** raw PII **must** land in Bronze. The security boundary is around **who can read it**, not around whether it exists.

---

## 2. Access Model

### 2.1 Identity Model

| Group | Purpose | Bronze Access |
|---|---|---|
| `data-platform-admins` | Break-glass platform admins | ✅ Full read (audit-logged) |
| `data-platform-dlt-sp-${env}` | DLT service principal | ✅ Read + Write (writes Bronze) |
| `compliance_auditors` | Regulatory audit | ⚠️ On request, time-bound |
| `fraud_investigators` | Fraud investigation | ⚠️ On request, case-based |
| `card_ops_level2` | Card operations | ⚠️ On request, PAN only |
| `executive_board` | Leadership | ❌ No Bronze access |
| `account users` (all workspace users) | Default | ❌ **No access** |

### 2.2 Enforcement (Unity Catalog)

```sql
-- Enforced via terraform/uc_security_policies.tf

-- Deny broad access
REVOKE SELECT ON SCHEMA ${catalog}.raw_bronze FROM `account users`;

-- Grant only to DLT SP + platform admins
GRANT USAGE, SELECT ON SCHEMA ${catalog}.raw_bronze TO `data-platform-dlt-sp-${env}`;
GRANT ALL PRIVILEGES  ON SCHEMA ${catalog}.raw_bronze TO `data-platform-admins`;