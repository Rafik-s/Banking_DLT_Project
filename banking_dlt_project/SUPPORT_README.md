# 🛡️ SUPPORT_README.md

> **README Badges — Explanation, Security Considerations, and Approved Patterns for Internal Banking Repos**

This document explains the Shields.io badges used at the top of `README.md`, why they exist, and the **approved alternatives** for an internal Tier-1 banking repository where third-party external calls are restricted.

---

## 📖 Table of Contents

1. [What Are These Badges?](#-what-are-these-badges)
2. [Anatomy of a Badge](#-anatomy-of-a-badge)
3. [Badge-by-Badge Breakdown](#-badge-by-badge-breakdown)
4. [Static vs. Dynamic Badges](#-static-vs-dynamic-badges)
5. [Why Banks Use Them](#-why-banks-use-them)
6. [⚠️ Security Consideration — Third-Party Calls](#️-security-consideration--third-party-calls)
7. [Approved Alternatives](#-approved-alternatives)
   - [Option A — Self-Hosted Shields.io](#option-a--self-hosted-shieldsio)
   - [Option B — Commit SVGs Locally (Recommended)](#option-b--commit-svgs-locally-recommended)
   - [Option C — Plain Text Header](#option-c--plain-text-header)
8. [Recommended Header for This Repo](#-recommended-header-for-this-repo)
9. [Rebuilding / Updating Local Badges](#-rebuilding--updating-local-badges)
10. [InfoSec Sign-Off Template](#-infosec-sign-off-template)

---

## 🎯 What Are These Badges?

The lines at the top of `README.md`:

```markdown
[![Platform](https://img.shields.io/badge/Platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white)](https://databricks.com)
[![Engine](https://img.shields.io/badge/Engine-Apache%20Spark%203.5+-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org)
[![Storage](https://img.shields.io/badge/Storage-Delta%20Lake-00ADD8)](https://delta.io)
[![Governance](https://img.shields.io/badge/Governance-Unity%20Catalog-1E88E5)](https://docs.databricks.com/data-governance/unity-catalog/)
[![Compliance](https://img.shields.io/badge/Compliance-DPDP%20%7C%20PCI--DSS%20%7C%20RBI-success)]()
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Azure%20DevOps-0078D7?logo=azuredevops)](https://azure.microsoft.com/en-us/products/devops)
```

Are **Shields.io badges** — small, auto-generated SVG images that visually summarize a project's tech stack, status, or metadata. They're the de facto standard for GitHub, Azure DevOps, GitLab, and Bitbucket README files.

They are **not** part of your application code. They are **not** consumed by any pipeline. They are **purely a documentation aid** rendered by the Git hosting platform (Azure DevOps, GitHub, etc.) when a human views the README.

---

## 🧩 Anatomy of a Badge

Each line follows this structure:

```markdown
[![Alt Text](https://img.shields.io/badge/{LABEL}-{MESSAGE}-{COLOR}?logo={LOGO}&logoColor={HEX})](https://link-to-something)
```

### Breakdown (using the Platform badge as example)

```markdown
[![Platform](https://img.shields.io/badge/Platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white)](https://databricks.com)
```

| Part | Value | Meaning |
|---|---|---|
| `[![Platform]` | `Platform` | Alt text — shown if image fails, read by screen readers |
| `https://img.shields.io/badge/` | — | Shields.io endpoint for static badges |
| `Platform-Azure%20Databricks-FF3621` | — | `LABEL-MESSAGE-COLOR` (`%20` = URL-encoded space) |
| `?logo=databricks` | — | Renders the Databricks logo icon |
| `&logoColor=white` | — | Icon color (badge background stays `FF3621`) |
| `](https://databricks.com)` | — | Click-through link |

**Rendered result:** A red badge that says **Platform | Azure Databricks** with the Databricks icon, clickable to databricks.com.

### Color Keywords

Shields.io supports **named color aliases** in addition to hex codes:

| Alias | Hex | Typical Use |
|---|---|---|
| `brightgreen` | `#4c1` | Success, passing |
| `green` | `#97ca00` | OK |
| `yellowgreen` | `#a4a61d` | Minor warning |
| `yellow` | `#dfb317` | Warning |
| `orange` | `#fe7d37` | Important |
| `red` | `#e05d44` | Critical |
| `blue` | `#007ec6` | Informational |
| `lightgrey` | `#9f9f9f` | Inactive |
| `success` | `#4c1` | Alias for brightgreen |
| `critical` | `#e05d44` | Alias for red |
| `important` | `#fe7d37` | Alias for orange |
| `informational` | `#007ec6` | Alias for blue |
| `inactive` | `#9f9f9f` | Alias for lightgrey |

---

## 📋 Badge-by-Badge Breakdown

| # | Badge | Label | Message | Color | Logo | Click Target |
|---|---|---|---|---|---|---|
| 1 | Platform | `Platform` | Azure Databricks | `#FF3621` (Databricks orange-red) | Databricks | databricks.com |
| 2 | Engine | `Engine` | Apache Spark 3.5+ | `#E25A1C` (Spark orange) | Apache Spark | spark.apache.org |
| 3 | Storage | `Storage` | Delta Lake | `#00ADD8` (Delta teal) | *(none)* | delta.io |
| 4 | Governance | `Governance` | Unity Catalog | `#1E88E5` (blue) | *(none)* | Databricks UC docs |
| 5 | Compliance | `Compliance` | DPDP \| PCI-DSS \| RBI | `success` (green) | *(none)* | *(none)* |
| 6 | CI/CD | `CI/CD` | Azure DevOps | `#0078D7` (Azure blue) | Azure DevOps | azure.microsoft.com/devops |

---

## 🔄 Static vs. Dynamic Badges

### Static (what we have)

Label, message, and color are **hardcoded in the URL**. Never changes unless someone edits the README.

**Pros:**
- Deterministic — no external service dependency beyond image hosting
- Fast rendering
- No auth required

**Cons:**
- Becomes stale — if you migrate from Spark 3.5 to Spark 4.0, the badge lies until someone updates the README

### Dynamic (live data)

Pull real-time data from GitHub / Azure DevOps APIs:

| Dynamic Badge | What It Shows |
|---|---|
| `https://img.shields.io/github/actions/workflow/status/{org}/{repo}/ci.yml` | GitHub Actions status |
| `https://img.shields.io/azure-devops/build/{org}/{project}/{definitionId}` | Azure DevOps build status |
| `https://img.shields.io/github/v/release/{org}/{repo}` | Latest release version |
| `https://img.shields.io/github/license/{org}/{repo}` | License |
| `https://img.shields.io/github/last-commit/{org}/{repo}` | Last commit date |

**Example — live Azure DevOps CI status:**

```markdown
[![Build Status](https://img.shields.io/azure-devops/build/your-org/banking-data-platform/42/main)](https://dev.azure.com/your-org/banking-data-platform/_build?definitionId=42)
```

Replace `your-org`, `banking-data-platform`, and `42` with your actual organization, project, and pipeline definition ID.

**Pros:**
- Always accurate
- CI visibility is a strong signal

**Cons:**
- **External service call** on every README view — InfoSec concern (see below)
- Rate-limited by Shields.io
- If Shields.io is down, badges render as broken images

---

## 🏦 Why Banks Use Them

In a Tier-1 banking repo, badges serve a **compliance and onboarding purpose**, not just decoration:

1. **Audit evidence** — A badge saying "Compliance: DPDP | PCI-DSS | RBI" signals to auditors that these frameworks were considered.
2. **Fast onboarding** — A new engineer scanning the README instantly knows the stack without reading 5 pages.
3. **CI visibility** — A red "build failing" badge on the README is impossible to ignore and drives SLAs.
4. **Change management** — A "last commit" badge helps auditors see recency of code review.

---

## ⚠️ Security Consideration — Third-Party Calls

**Shields.io is a third-party service external to your VNet.**

When someone views your README:

```
┌────────────────┐         ┌─────────────────────┐         ┌──────────────────┐
│ Developer's    │  HTTPS  │  Git hosting        │  HTTPS  │  img.shields.io  │
│ Browser        │────────▶│  (Azure DevOps)     │────────▶│  (Public Cloud)  │
└────────────────┘         └─────────────────────┘         └──────────────────┘
                                                                   ▲
                                    Request includes:               │
                                    - Org name                      │
                                    - Repo name                     │
                                    - Badge path                    │
                                    - Referrer header               │
                                    - (For dynamic badges) API call │
```

**Risk surface:**

| Risk | Impact | Severity |
|---|---|---|
| **Metadata exfiltration** | Shields.io learns your org/repo names and dynamic-badge queries | Medium |
| **Referrer leakage** | Browser sends `Referer: https://dev.azure.com/your-org/...` | Low |
| **Availability dependency** | If Shields.io is down or blocked by corporate proxy, badges render broken | Low |
| **Data poisoning (dynamic badges)** | Malicious redirect of Shields.io DNS → fake "passing" badge | High (but low likelihood) |
| **InfoSec policy violation** | Some banks forbid any external calls from internal tools | High (policy) |

**For a banking repo, InfoSec will flag this.** Expect a finding like:

> "Internal repository READMEs must not load third-party images from external domains. All assets must be self-hosted or served from an approved internal CDN."

---

## ✅ Approved Alternatives

### Option A — Self-Hosted Shields.io

Deploy the official `shieldsio/shields` Docker image inside your VNet and rewrite all URLs.

**Deployment (Kubernetes example):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shields
  namespace: internal-tools
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shields
  template:
    metadata:
      labels:
        app: shields
    spec:
      containers:
        - name: shields
          image: shieldsio/shields:latest
          ports:
            - containerPort: 8080
          env:
            - name: BASE_URL
              value: "https://shields.internal.bank.com"
```

**Then rewrite README URLs:**

```markdown
[![Platform](https://shields.internal.bank.com/badge/Platform-Azure%20Databricks-FF3621?logo=databricks)](https://databricks.com)
```

**Pros:**
- Full shields.io feature set (including dynamic badges)
- No external calls
- InfoSec approved

**Cons:**
- Requires infrastructure (K8s namespace, TLS cert, DNS, monitoring)
- Ops burden for a decorative feature
- Still needs maintenance and version upgrades

**Recommendation:** Only worthwhile if you have many repos needing dynamic badges.

---

### Option B — Commit SVGs Locally (Recommended)

Download the badge SVGs once, commit them to the repo, and serve them from your own repo.

**Step 1 — Create `.badges/` directory:**

```bash
mkdir -p .badges
```

**Step 2 — Download each badge:**

```bash
curl -o .badges/platform.svg \
  "https://img.shields.io/badge/Platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white"

curl -o .badges/engine.svg \
  "https://img.shields.io/badge/Engine-Apache%20Spark%203.5+-E25A1C?logo=apachespark&logoColor=white"

curl -o .badges/storage.svg \
  "https://img.shields.io/badge/Storage-Delta%20Lake-00ADD8"

curl -o .badges/governance.svg \
  "https://img.shields.io/badge/Governance-Unity%20Catalog-1E88E5"

curl -o .badges/compliance.svg \
  "https://img.shields.io/badge/Compliance-DPDP%20%7C%20PCI--DSS%20%7C%20RBI-success"

curl -o .badges/cicd.svg \
  "https://img.shields.io/badge/CI%2FCD-Azure%20DevOps-0078D7?logo=azuredevops"
```

**Step 3 — Reference locally in README:**

```markdown
[![Platform](.badges/platform.svg)](https://databricks.com)
[![Engine](.badges/engine.svg)](https://spark.apache.org)
[![Storage](.badges/storage.svg)](https://delta.io)
[![Governance](.badges/governance.svg)](https://docs.databricks.com/data-governance/unity-catalog/)
[![Compliance](.badges/compliance.svg)]()
[![CI/CD](.badges/cicd.svg)](https://azure.microsoft.com/en-us/products/devops)
```

**Pros:**
- Zero external calls — images served from your own Git host
- Works offline
- Immune to Shields.io outages
- No new infrastructure
- InfoSec will approve without discussion

**Cons:**
- Static — must re-download if the message changes (e.g., "Spark 3.5" → "Spark 4.0")
- SVGs add ~2 KB each to the repo (negligible)

**Recommendation:** ✅ **Use this option.** It's the standard pattern for banking repos and passes InfoSec review without conversation.

---

### Option C — Plain Text Header

If InfoSec blocks images entirely in READMEs, use plain markdown:

```markdown
**Platform:** Azure Databricks · **Engine:** Apache Spark 3.5+ · **Storage:** Delta Lake
**Governance:** Unity Catalog · **Compliance:** DPDP | PCI-DSS | RBI · **CI/CD:** Azure DevOps
```

Renders as:

> **Platform:** Azure Databricks · **Engine:** Apache Spark 3.5+ · **Storage:** Delta Lake
> **Governance:** Unity Catalog · **Compliance:** DPDP | PCI-DSS | RBI · **CI/CD:** Azure DevOps

**Pros:**
- Zero dependencies
- Zero InfoSec concerns
- Fully accessible (screen readers, CLI renderers, terminals)

**Cons:**
- Less visually striking
- No click-through links (unless you add markdown link syntax)

**When to use:** If your bank's policy forbids all external images **and** you can't be bothered to manage `.badges/`.

---

## 🏆 Recommended Header for This Repo

Given that this is a **Tier-1 banking repo** and InfoSec review is a certainty, the recommended pattern is **Option B — Committed SVGs**.

### Implementation Checklist

- [ ] Create `.badges/` directory at repo root
- [ ] Add the 6 SVGs listed above
- [ ] Update `README.md` header to reference `.badges/*.svg`
- [ ] Add `.gitattributes` entry to mark SVGs as binary (prevents diff noise):

  ```gitattributes
  .badges/*.svg binary
  ```

- [ ] Document in `CONTRIBUTING.md` that badges are self-hosted
- [ ] Add a CI check that verifies `.badges/*.svg` files exist and are valid SVG

### Final Header (`README.md`)

```markdown
[![Platform](.badges/platform.svg)](https://databricks.com)
[![Engine](.badges/engine.svg)](https://spark.apache.org)
[![Storage](.badges/storage.svg)](https://delta.io)
[![Governance](.badges/governance.svg)](https://docs.databricks.com/data-governance/unity-catalog/)
[![Compliance](.badges/compliance.svg)]()
[![CI/CD](.badges/cicd.svg)](https://azure.microsoft.com/en-us/products/devops)
```

---

## 🔧 Rebuilding / Updating Local Badges

When your stack changes (e.g., Spark 3.5 → 4.0), rebuild the affected badge:

### One-Off Update

```bash
# Update the engine badge
curl -o .badges/engine.svg \
  "https://img.shields.io/badge/Engine-Apache%20Spark%204.0-E25A1C?logo=apachespark&logoColor=white"

git add .badges/engine.svg
git commit -m "docs: update engine badge to Spark 4.0"
```

### Scripted Refresh (Recommended)

Create `scripts/refresh-badges.sh`:

```bash
#!/usr/bin/env bash
# Regenerates all committed badges from Shields.io.
# Run manually when the stack changes; never run in CI.

set -euo pipefail

BADGE_DIR=".badges"
mkdir -p "$BADGE_DIR"

declare -A BADGES=(
    ["platform.svg"]="https://img.shields.io/badge/Platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white"
    ["engine.svg"]="https://img.shields.io/badge/Engine-Apache%20Spark%203.5+-E25A1C?logo=apachespark&logoColor=white"
    ["storage.svg"]="https://img.shields.io/badge/Storage-Delta%20Lake-00ADD8"
    ["governance.svg"]="https://img.shields.io/badge/Governance-Unity%20Catalog-1E88E5"
    ["compliance.svg"]="https://img.shields.io/badge/Compliance-DPDP%20%7C%20PCI--DSS%20%7C%20RBI-success"
    ["cicd.svg"]="https://img.shields.io/badge/CI%2FCD-Azure%20DevOps-0078D7?logo=azuredevops"
)

for filename in "${!BADGES[@]}"; do
    url="${BADGES[$filename]}"
    echo "Refreshing $filename..."
    curl -fsSL -o "$BADGE_DIR/$filename" "$url"
done

echo "All badges refreshed. Review and commit:"
echo "  git diff --stat $BADGE_DIR/"
```

Make it executable:

```bash
chmod +x scripts/refresh-badges.sh
```

---

## 📝 InfoSec Sign-Off Template

If your InfoSec team needs documentation, use this template:

---

**Subject:** InfoSec Review Request — README Badges in `banking_dlt_project`

**Repository:** `banking_dlt_project`
**Team:** Data Platform Engineering
**Reviewer requested:** InfoSec Architecture

**Summary:**

The `README.md` in this repository includes six visual badges summarizing the project's technology stack (Platform, Engine, Storage, Governance, Compliance, CI/CD). The badges are implemented as **locally committed SVG files** under `.badges/`.

**Security posture:**

- ✅ **No external calls** — SVGs are served from the Git host (Azure DevOps), not from `img.shields.io`
- ✅ **No runtime dependency** — badges are documentation only; they do not affect pipeline execution
- ✅ **No secrets** — badge content is limited to publicly-known technology names
- ✅ **No PII** — no customer, employee, or account data
- ✅ **No dynamic data** — badges are static strings, not live API pulls
- ✅ **Refresh process** — `scripts/refresh-badges.sh` runs manually by a developer, reviewed via PR

**Alternative considered and rejected:** Using live `img.shields.io` URLs (rejected due to external third-party call).

**Alternative considered and rejected:** Self-hosted Shields.io instance (rejected due to infrastructure overhead for a documentation-only feature).

**Requested action:** Confirm that locally-committed SVG badges are acceptable under the bank's repository documentation standards.

---

## 📌 TL;DR

| Aspect | Details |
|---|---|
| **What they are** | Shields.io SVG badges — visual summaries of the tech stack |
| **Where they live** | `README.md` header, sourced from `.badges/*.svg` |
| **Do they call external services?** | ❌ No — committed locally per Option B |
| **Do they affect the pipeline?** | ❌ No — documentation only |
| **Who owns updates?** | Data Platform Engineering, via PR |
| **How to refresh** | Run `scripts/refresh-badges.sh`, review, commit |
| **InfoSec posture** | ✅ Approved pattern for internal banking repos |

---

**Maintained by:** Data Platform Engineering
**Last reviewed:** 2025-01-15
**Review cadence:** Annually, or when the tech stack changes
**Owner:** `#data-platform` (Teams)