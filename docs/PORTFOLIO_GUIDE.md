# 💼 Portfolio Guide — How to Present This Project

> **Purpose:** A cheat sheet for discussing this repository in interviews, portfolio reviews, and technical conversations.
> **Owner:** Rafik-s
> **Last reviewed:** 2026-10-04

---

## The 30-Second Elevator Pitch

> *"It's an enterprise-grade reference implementation of a banking data platform
> on Azure Databricks. It demonstrates the Medallion Architecture, Delta Live
> Tables, Unity Catalog governance, SCD2 historical tracking, a reconciliation
> framework, DR planning, and secure CI/CD — all the patterns used in a Tier-1
> bank. It's not deployed in a real bank; it's a portfolio project to demonstrate
> the architecture and operational maturity."*

**Why this works:** It states what it is, what it demonstrates, and what it isn't —
in one breath. Honest framing beats overselling.

---

## The 2-Minute Pitch (if asked "Tell me about it")

Walk through in this order:

1. **The problem:** "Banks need a governed, auditable, reconciled data platform
   for their core banking data — transactions, customers, loans, cards, etc."

2. **The architecture:** "I used a Medallion Architecture on Azure Databricks:
   Bronze for raw ingestion via Auto Loader, Silver for cleansing + PII masking +
   DLT expectations, Gold for SCD2 dimensions and liquid-clustered facts."

3. **The differentiators:**
   - "I built a **reconciliation engine** that ties out row counts and amounts
     across layers daily — count, amount, and double-entry checks. Pages on-call
     if anything fails."
   - "I used **business idempotency keys** — `(transaction_id, source_system, event_version)` —
     because `transaction_id` alone isn't globally unique in banking."
   - "**Late data goes to a quarantine table**, not silently dropped. Silent
     data loss in banking is unacceptable."
   - "I built the **Bronze PII boundary**: raw Aadhaar/PAN live only in Bronze,
     with `REVOKE SELECT FROM account users`, and are HMAC-hashed + masked in Silver."

4. **The operational maturity:**
   - "I documented the **DR plan** with RPO ≤ 15 min / RTO ≤ 60 min, quarterly
     automated drills, and a runbook for on-call."
   - "I designed **environment separation** — Dev/QA/Prod isolated at subscription,
     VNet, storage, and identity level."
   - "CI uses **Workload Identity Federation** — no PATs. Databricks CLI is
     pinned with SHA256 verification."

5. **The honesty close:** "It's a reference implementation, not deployed in a
   real bank. But every pattern here is drawn from real banking requirements."

---

## Anticipated Interview Questions & Answers

### Architecture

**Q: Why DLT instead of plain PySpark notebooks?**

A: "DLT gives me declarative expectations with metrics, Unity Catalog lineage,
auto-orchestration, and `APPLY CHANGES INTO` for SCD2. Plain notebooks would
mean reimplementing all of that. The trade-off is vendor lock-in to Databricks —
acceptable for a bank that's already standardized on it."

**Q: Why SCD2? Isn't that overkill?**

A: "No — BCBS 239 requires as-of-date risk reporting. If a regulator asks
'what was the loan book on 2024-03-31?', you must answer with the dimensions
**as they were** on that date, not today's. SCD2 with source-event sequencing
is how you get there."

**Q: Why do you need a reconciliation engine?**

A: "Every bank does daily reconciliation between source systems and the warehouse.
Without it, you can't prove the numbers in your reports are correct. My engine
does three kinds of checks: count tie-out across layers, amount tie-out, and
double-entry integrity (`SUM(credits) == SUM(debits)`). If anything fails, on-call
is paged."

### Security

**Q: How do you handle PII in Bronze?**

A: "Raw PII lands in Bronze by design — it's the audit trail of last resort.
But I've locked it down: `REVOKE SELECT FROM account users`, PII columns tagged
with `pii=...` and `dpdp=restricted`, and Terraform enforces the grants.
In Silver, raw PII is HMAC-hashed via a UC function backed by Key Vault, and
display-masked. Raw columns are dropped from the schema."

**Q: Why HMAC and not just SHA-256?**

A: "Aadhaar is only 12 digits — the search space is 10^12. A plain SHA-256
would be brute-forced in hours on a GPU. HMAC with a salt from Key Vault
makes that attack infeasible. Also, the salt is never in source code, so
even a repo compromise doesn't help."

**Q: What about PCI-DSS?**

A: "It's **PCI-DSS-aligned**, not certified. I mask PAN as first-6 + last-4,
restrict access via RLS, and log reads. But full PCI-DSS requires network
segmentation, FIM, HSM key management, log integrity, and a QSA assessment —
that's out of scope for a portfolio project. I'm careful not to claim certification."

**Q: How do you authenticate CI/CD?**

A: "Workload Identity Federation between Azure DevOps and Entra ID. No PATs,
no secrets. The Databricks CLI uses `DATABRICKS_AUTH_TYPE=azure-cli` to exchange
the OIDC token. Additionally, the CLI binary itself is pinned to a specific
version with SHA256 verification — no more `curl | sh` supply-chain risk."

### Operations

**Q: What's your RPO and RTO?**

A: "RPO ≤ 15 minutes, RTO ≤ 60 minutes. Achieved via ADLS RA-GRS replication
and a Terraform-provisioned DR workspace. Failover is documented in the
DR plan; quarterly drills validate the procedure."

**Q: How do you separate environments?**

A: "Full isolation. Separate Azure subscriptions, separate VNets with no peering,
separate ADLS, separate Key Vaults, separate service principals. Prod access
is via PIM (just-in-time, 4-hour expiry, requires approval). A Dev cluster
literally cannot reach Prod storage."

**Q: What happens when the source system changes a column?**

A: "The data contract in `contracts/{dataset}.yaml` is the source of truth.
`cloudFiles.schemaEvolutionMode = failOnNewColumns` means the pipeline fails
loudly. The response is documented: compare source to contract, open a PR
to update the contract + Python schema, get source-owner approval, redeploy.
Backward-compatibility is enforced in CI via semver rules."

### Data Engineering

**Q: How do you deduplicate transactions?**

A: "Business idempotency key: `(transaction_id, source_system, event_version)`.
`transaction_id` alone is not globally unique — a NEFT transaction and a UPI
transaction can both be `TXN-12345`. `event_version` handles corrections —
a source re-emit is a new business event, not a duplicate."

**Q: What happens to late-arriving data?**

A: "It goes to `silver_transactions_late` with `quarantine_reason` and
`late_by_hours`. Alerting triggers if volume exceeds threshold. It's replayable
once the source system catches up. No silent data loss."

**Q: Why Liquid Clustering over Z-Ordering?**

A: "Liquid Clustering is adaptive — it rebalances as data distribution changes.
Z-Order requires manual `OPTIMIZE ... ZORDER` and is being deprecated. The
trade-off is DBR 13.3+ requirement, which isn't a problem for a modern deployment."

---

## What to Emphasize (and What Not To)

### Emphasize ✅

1. **The reconciliation engine** — it's rare, it's banking-specific, it's a differentiator
2. **The business idempotency key** — shows you understand banking data nuances
3. **The Bronze PII boundary** — shows you take governance seriously
4. **DR plan with RPO/RTO** — shows operational maturity
5. **WIF + pinned CLI** — shows supply-chain awareness
6. **Data contracts** — shows you can formalize agreements
7. **The honest framing** — this is what separates junior from senior engineers

### Do NOT Overclaim ❌

- ❌ Don't say "production-grade" or "deployed in a Tier-1 bank"
- ❌ Don't say "PCI-DSS compliant" or "DPDP certified"
- ❌ Don't say "handles petabytes" (it doesn't)
- ❌ Don't say "replaces Tableau" (it doesn't)
- ❌ Don't claim unit tests cover everything (26 tests; integration pending)

---

## The Resume Bullet Points

Copy-paste-ready for your resume:

> **Enterprise Banking Data Platform** — *Azure Databricks, DLT, Unity Catalog, Delta Lake, Terraform*
> - Designed and implemented a Medallion Architecture (Bronze/Silver/Gold) for 10 core banking datasets with DLT-based data quality expectations
> - Built a **daily reconciliation engine** tying out row counts and amounts across layers (count, amount, double-entry); pages on-call on failures
> - Enforced PII protection via **HMAC-SHA256 UC functions** with salt in Azure Key Vault; restricted Bronze PII via `REVOKE SELECT`
> - Implemented SCD Type 2 dimensions via `APPLY CHANGES INTO` with source-event sequencing for BCBS 239 as-of-date reporting
> - Built a **data contracts framework** (YAML + CI validation) to formalize source↔platform schema agreements with semver enforcement
> - Designed **Disaster Recovery** plan (RPO ≤ 15 min, RTO ≤ 60 min) with automated quarterly drills
> - Modernized CI/CD with **Workload Identity Federation** (no PATs), pinned CLI with SHA256, and full security scanning (gitleaks, bandit, checkov, trivy, CodeQL)
> - Documented operational maturity: 17 design docs, 26 unit tests, incident response playbook, DR plan, environment separation model

---

## LinkedIn / GitHub Description

> **Enterprise Banking Core Data Platform** — An enterprise-grade reference implementation demonstrating the architectural patterns, security posture, and operational maturity of a Tier-1 banking data platform on Azure Databricks. Features Medallion Architecture, DLT, Unity Catalog governance, SCD2 dimensions, reconciliation framework, DR planning, and secure CI/CD with WIF.
>
> ⚠️ Reference implementation — not deployed in a real bank.

---

## The ONE Sentence for Recruiters

> *"A Tier-1 banking data platform reference implementation on Azure Databricks — demonstrating Medallion architecture, DLT, Unity Catalog governance, reconciliation, and secure CI/CD."*

---

## What This Repository Says About You (as an Engineer)

When a hiring manager browses this repo, they infer:

| Signal | What They Think |
|---|---|
| Medallion architecture | "Knows modern data lakehouse patterns" |
| DLT with expectations | "Understands declarative pipelines" |
| Business idempotency key | "Has thought about real banking data" |
| Late-data quarantine | "Won't silently drop data — cares about integrity" |
| Reconciliation engine | "Banking-aware; not just a generalist" |
| Bronze PII boundary | "Takes governance seriously" |
| DR plan with RPO/RTO | "Operations-focused, not just development" |
| WIF + pinned CLI | "Security-conscious; supply-chain aware" |
| Data contracts | "Formalizes agreements; enterprise-thinking" |
| WHAT_IS_NOT_INCLUDED | "Honest; knows the difference between portfolio and production" |
| 17 design docs | "Communicates well; writes clearly" |
| 26 unit tests | "Tests their work" |

**That last group — honesty, documentation, testing — is what separates senior engineers from mid-level.**

---

## What to Do Next (Career Path)

If you're targeting a **Data Platform Engineer / Databricks Admin / Lead DE** role:

### Short-term (next 30 days)

1. **Deploy this repo to a real Azure Dev environment** — even a personal subscription. Take screenshots. Add them to the README.
2. **Add integration tests** — spin up `banking_test_catalog`, run a small pipeline, assert results. Target 5–10 tests.
3. **Record a 5-minute walkthrough video** — narrate the architecture, the reconciliation engine, the DR plan. Post to YouTube/Loom.

### Medium-term (next 90 days)

4. **Add a second pipeline** — a streaming pipeline using Event Hubs or Kafka. Shows you can handle real-time.
5. **Add ML/AI** — a simple churn prediction or fraud scoring model using MLflow + Databricks ML. Extends the platform into the ML space.
6. **Write a blog post or LinkedIn article** — "How I Built a Tier-1 Banking Data Platform Reference Implementation."

### Long-term (next 12 months)

7. **Get certified:** Databricks Certified Data Engineer Professional, or Databricks Certified Associate Developer for Apache Spark.
8. **Contribute to open source** — DLT, Delta Lake, or Databricks SDK.
9. **Speak at a meetup** — Databricks User Group, PyData, or local Data Engineering meetup.

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-10-04 | Initial portfolio guide | Rafik-s |