# Security Policy

> **Classification:** Internal — Public (for responsible disclosure)
> **Owner:** InfoSec + Data Platform Engineering

---

## Supported Versions

| Version | Supported |
|---|---|
| 1.x (current) | ✅ |

---

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report privately via one of:

| Channel | Details |
|---|---|
| **Email** | security@your-bank.example |
| **Internal Teams** | `#infosec-review` |
| **PagerDuty** | `data-oncall` for production-critical |

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Our commitment

| Timeframe | Action |
|---|---|
| **24 hours** | Acknowledge receipt |
| **72 hours** | Initial assessment + severity |
| **7 days** | Fix for critical/high |
| **30 days** | Fix for medium/low |

---

## Security Controls in This Repository

| Control | Implementation |
|---|---|
| **Secret management** | Databricks Secret Scopes + Azure Key Vault; no secrets in code |
| **CI/CD authentication** | Workload Identity Federation (Entra ID) — no PATs |
| **Supply chain** | Pinned CLI versions with SHA256 verification |
| **Secret scanning** | gitleaks in pre-commit + CI |
| **SAST** | bandit on Python; CodeQL on weekly schedule |
| **Dependency scan** | pip-audit + Dependabot |
| **IaC scan** | checkov + trivy on Terraform |
| **Terraform state** | Remote backend with locking, encryption, RBAC |
| **PII protection** | HMAC hashing + column masks + row filters |
| **Bronze PII boundary** | Documented and enforced (`docs/SECURITY_BOUNDARY.md`) |

---

## Automated Scanning Schedule

| Scan | Trigger | Owner |
|---|---|---|
| gitleaks (pre-commit) | Every commit locally | Developer |
| gitleaks (CI) | Every PR + main push | CI |
| bandit | Every PR | CI |
| pip-audit | Every PR | CI |
| checkov | Every PR | CI |
| trivy | Every PR | CI |
| CodeQL | Weekly + PR | GitHub Actions |
| Dependabot | Daily | GitHub |

---

## Vulnerability Disclosure Policy

We follow **coordinated disclosure**. Once we confirm a vulnerability:

1. We develop and test a fix.
2. We deploy the fix to production.
3. We publish an advisory (if applicable).
4. We credit the reporter (with their permission).

We do not pay bounties for internal repository findings, but we acknowledge
all responsible disclosures.

---

## Compliance

| Regulation | Relevance |
|---|---|
| **DPDP Act 2023** | Personal data protection |
| **PCI-DSS 3.2.1** | Cardholder data (aligned, not certified) |
| **RBI IT Governance** | Banking IT controls |
| **BCBS 239** | Risk data aggregation |

---

## Change Log

| Date | Change |
|---|---|
| 2026-10-04 | Initial policy |