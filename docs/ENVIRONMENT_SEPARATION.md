
---

## 📄 File 4 (NEW): `docs/ENVIRONMENT_SEPARATION.md`

```markdown
# 🧱 Environment Separation

> **Owner:** Data Platform Engineering + InfoSec
> **Last reviewed:** 2026-10-04

---

## 1. Principle

**Dev, QA, and Prod are isolated at every layer:** network, identity, storage,
compute, secrets, and data. A developer cannot accidentally (or maliciously)
reach Prod resources from a Dev workspace.

---

## 2. Isolation Matrix

| Layer | Dev | QA | Prod |
|---|---|---|---|
| **Azure Subscription** | `sub-banking-dev` | `sub-banking-qa` | `sub-banking-prod` |
| **Resource Group** | `rg-banking-dev` | `rg-banking-qa` | `rg-banking-prod` |
| **VNet** | `vnet-banking-dev` (10.20.0.0/16) | `vnet-banking-qa` (10.30.0.0/16) | `vnet-banking-prod` (10.10.0.0/16) |
| **Databricks Workspace** | `adb-dev-instance` | `adb-qa-instance` | `adb-prod-instance` |
| **Unity Catalog** | `banking_dev_catalog` | `banking_qa_catalog` | `banking_prod_catalog` |
| **ADLS Storage** | `stbankingdev001` | `stbankingqa001` | `stbankingprod001` |
| **Key Vault** | `kv-banking-dev` | `kv-banking-qa` | `kv-banking-prod` |
| **Service Principal** | `sp-banking-dlt-dev` | `sp-banking-dlt-qa` | `sp-banking-dlt-prod` |
| **Data** | Synthetic | Masked subset of Prod | Real customer data |
| **Approval to deploy** | Auto (on merge) | Tech Lead + QA Lead | CAB + CDO |

**No VNet peering between environments. No shared storage accounts. No shared secrets.**

---

## 3. Identity Boundaries

### 3.1 Service Principals

Each environment has its own **dedicated Entra ID service principal**:

| Env | SP Name | Permissions |
|---|---|---|
| Dev | `sp-banking-dlt-dev` | Dev workspace admin; Dev storage contributor |
| QA | `sp-banking-dlt-qa` | QA workspace contributor; QA storage contributor |
| Prod | `sp-banking-dlt-prod` | Prod workspace contributor; Prod storage reader/writer |

**No SP spans environments.** Dev SP has **zero access** to Prod resources.

### 3.2 Human Identities

| Role | Dev | QA | Prod |
|---|---|---|---|
| **Developer** | Admin | Contributor (read-only data) | ❌ No access |
| **Senior Developer** | Admin | Contributor | Break-glass only |
| **Tech Lead** | Admin | Admin | Contributor |
| **Data Platform Lead** | Admin | Admin | Admin |
| **BI Analyst** | ❌ | Read Silver + Gold | Read Gold only |
| **Compliance Auditor** | Read | Read | Read (with RLS) |
| **InfoSec** | Read | Read | Read + audit |

Enforced via **Azure PIM** (Privileged Identity Management) — Prod access is
**just-in-time**, requires **MFA + approval**, and expires in **4 hours**.

---

## 4. Deployment Flow
Developer
│
│ git push feature/*
▼
Feature Branch (GitHub / Azure DevOps)
│
│ PR to develop → CI validates → merge
▼
develop branch
│
│ Auto-deploy to DEV
▼
DEV
│
│ Automated integration tests pass
▼
QA branch (from develop)
│
│ Deploy to QA → UAT
▼
QA
│
│ Business sign-off + CAB approval
▼
main branch (merge from QA)
│
│ Manual approval → deploy to PROD
▼
PROD


**Key controls:**
- **Dev:** Auto-deploy on merge to `develop`
- **QA:** Auto-deploy on merge to `qa` branch; UAT by business
- **Prod:** Manual deploy via CAB-approved release; **no auto-deploy**

---

## 5. Data Flow Restrictions

| Source | Can write to | Can read from |
|---|---|---|
| Dev pipelines | Dev ADLS only | Dev ADLS only |
| QA pipelines | QA ADLS only | QA ADLS only |
| Prod pipelines | Prod ADLS only | Prod ADLS only |

**Cross-environment data movement:**
- Only via **controlled data masking pipeline** (Dev ← Prod masked sample)
- Only via **approved sync job** (Dev → QA for testing)
- Never automatically — always via a change request

### 5.1 Prod → Dev Sample Refresh

Monthly job that:

1. Reads a **statistically sampled subset** of Prod data
2. Applies **additional anonymization** (beyond Silver masking)
3. Writes to Dev's `stbankingdev001`
4. Logs the transfer for audit

---

## 6. Network Isolation

- **No VNet peering** between environments
- **No private DNS zone sharing**
- **No shared Private Endpoints**
- **Firewall rules** allow only intra-environment traffic
- **NSGs** deny cross-environment CIDR blocks

Test command (should fail):
```bash
# From Dev cluster
az storage blob list --account-name stbankingprod001 --container-name raw
# Expected: AccessDenied (public access disabled + no network route)

7. Secret Isolation
Secret	Dev	QA	Prod
pii-hmac-salt	Separate value	Separate value	Separate value
Databricks workspace URL	Dev URL	QA URL	Prod URL
CI service connection	sc-banking-dev-wif	sc-banking-qa-wif	sc-banking-prod-wif
Cross-environment secret access is impossible — different Key Vaults,
different RBAC, different Private Endpoints.

8. Terraform Isolation
Each environment has its own Terraform state


tfstate storage account (per env):
  stbankingtfstatedev
    └── tfstate/
        └── banking-dlt-dev.tfstate

  stbankingtfstateqa
    └── tfstate/
        └── banking-dlt-qa.tfstate

  stbankingtfstateprod
    └── tfstate/
        └── banking-dlt-prod.tfstate
No shared state. A compromised Dev state file cannot compromise Prod.

Terraform workspace per environment:

bash
terraform workspace select dev
terraform apply -var-file=dev.tfvars

terraform workspace select qa
terraform apply -var-file=qa.tfvars

terraform workspace select prod
terraform apply -var-file=prod.tfvars
9. Promotion Checklist (Dev → QA → Prod)
Dev → QA
□ All unit tests pass
□ Integration tests pass in Dev
□ Reconciliation PASS in Dev (last 3 days)
□ No unresolved expect_or_fail failures
□ Tech Lead approval
QA → Prod
□ All QA integration tests pass
□ UAT sign-off by business
□ Performance tests pass (throughput within 10% of Prod baseline)
□ Security scan clean (gitleaks, bandit, CodeQL, trivy)
□ Reconciliation PASS in QA (last 7 days)
□ Change request raised in ServiceNow
□ CAB approval (Thursday review)
□ Rollback plan documented
□ Communications sent (24h notice to downstream consumers)
□ CDO final approval
10. Compliance Mapping
Regulation	Requirement	Implementation
RBI IT Governance	Segregation of environments	Full isolation
PCI-DSS 3.2.1	6.4.1: Separate environments	Complete separation
SOX (if applicable)	Change management	CAB approval for Prod
ISO 27001	A.12.1.4: Separation of environments	Documented in this file

11. Change Log
Date	Change	Author
2026-10-04	Initial draft	Data Platform Engineering