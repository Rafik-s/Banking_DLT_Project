
---

## 📄 File 2 (NEW): `docs/WHAT_IS_NOT_INCLUDED.md`

```markdown
# ❌ What Is Not Included

> **Purpose:** Explicit scope boundaries for this reference implementation.
> **Audience:** Reviewers, hiring managers, auditors, contributors.
> **Last reviewed:** 2026-10-04

---

## Why This Document Exists

Overselling a portfolio project damages credibility more than underselling it.
This document lists — **honestly and explicitly** — what this repository does
**not** include.

An experienced reviewer will ask: *"Is this production?"* The answer is **no**.
This document explains exactly how far this repo goes and where a real
production deployment would need to extend it.

---

## 1. Data & Privacy

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Real customer / account / transaction data | Compliance (DPDP, RBI) | Ingest from source systems with proper DPA |
| Consent tracking | DPDP requirement | Integration with consent management platform |
| Data subject access request (DSAR) portal | DPDP requirement | Portal + automated export pipeline |
| Data Protection Impact Assessment (DPIA) | DPDP requirement for high-risk processing | Formal DPIA signed off by DPO |
| Right-to-erasure automation | DPDP requirement | Request intake → pipeline trigger → vault salt deletion |
| Retention policy enforcement | RBI / DPDP | Automated archival + deletion jobs |
| Cross-border transfer register | DPDP | Documented transfer mechanism |

---

## 2. Security & Compliance

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| PCI-DSS certification | Not audited | QSA assessment, AOC |
| Full PCI control set (network segmentation, FIM, HSM, log integrity) | Out of scope | Enterprise security program |
| SOC 2 Type II | Not audited | Annual third-party audit |
| ISO 27001 certification | Not audited | ISMS implementation |
| DPDP certification / audit | Not audited | DPB-recognized audit |
| Penetration test report | Not performed | Annual pen test by certified firm |
| Threat model workshop | Simplified in docs | Full STRIDE / LINDDUN analysis |
| SIEM integration | Not wired | Sentinel / Splunk integration |
| DLP integration | Not wired | Purview / DLP policies on egress |
| Endpoint detection | Not applicable | Corporate EDR |
| Physical security | N/A | Datacenter controls |
| Background checks / personnel security | N/A | HR controls |

---

## 3. Infrastructure

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Real Azure subscription | Not provisioned | Enterprise agreement with RBI-mandated region |
| Multi-region **active-active** | Only active-passive DR | Complex; usually reserved for tier-0 systems |
| Multi-cloud failover | Out of scope | Azure → AWS/GCP strategy (rare in banking) |
| Real network topology | Documented, not deployed | VNet with Private Endpoints, firewall, NSG |
| ExpressRoute / VPN | Not configured | Private connectivity from on-prem |
| Dedicated HSM | Not provisioned | Azure Dedicated HSM for key management |
| Customer-managed keys (CMK) | Not enabled | CMK for ADLS, Key Vault |
| Immutable blob (WORM) | Not enabled | For Bronze archival (regulatory retention) |

---

## 4. Operations

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Production monitoring dashboards | Basic SQL queries only | Grafana / Power BI / Datadog |
| Real alerting (PagerDuty) | Webhook placeholder | PagerDuty service + on-call rotation |
| Real incident management | Documented, not integrated | ServiceNow / Jira Service Management |
| Runbook automation | Manual procedures | Automated remediation (auto-restart, auto-scale) |
| Chaos engineering | Not performed | Regular fault injection |
| Capacity planning | Estimated only | Historical trends + forecasting |
| Cost optimization dashboards | Not built | FinOps dashboards |
| SLA tracking | Not automated | Automated SLA reporting + breach alerts |

---

## 5. Data Platform Scope

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Real-time streaming | Only micro-batch (Auto Loader) | Kafka / Event Hubs + Structured Streaming |
| ML / AI workloads | Out of scope | Feature store, model serving, MLflow |
| Data science workspace | Not included | Shared DS workspace + Databricks ML |
| Feature engineering pipelines | Not included | Feature store + versioned features |
| Vector search / GenAI | Not included | Databricks Vector Search + RAG patterns |
| Lakehouse Federation | Not configured | Federated queries to external systems |
| Delta Sharing | Not configured | For secure inter-org sharing |
| Unity Catalog **marketplace** | Not configured | Data product catalogue |
| BI semantic layer | Not built | Power BI / Tableau / Looker semantic models |
| Data catalog / glossary | Simplified | Purview / Collibra integration |

---

## 6. Software Engineering

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Integration tests | Not yet | Test against `banking_test_catalog` with real Spark |
| End-to-end tests | Not yet | Full pipeline on synthetic data |
| Performance tests | Not yet | Load tests at Prod-scale volumes |
| Contract tests (bi-directional) | Partial | Source-side and consumer-side contract tests |
| Chaos tests | Not performed | Fault injection on pipeline, storage, network |
| Code coverage target (70%) enforced in CI | Not enforced | Add `--cov-fail-under=70` to CI |
| Property-based tests | Not used | Hypothesis for masking / FK functions |
| Mutation testing | Not used | Mutmut for validation of test quality |

---

## 7. Documentation

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Training materials | Not included | Runbooks, onboarding, video walkthroughs |
| Business glossary (full) | Simplified | Aligned with bank-wide taxonomy |
| Data dictionary (full) | Via contracts | Auto-generated from contracts + Unity Catalog |
| Regulatory mapping (complete) | Partial | Full compliance mapping to RBI circulars |
| Architecture decision records (full) | Only highlights | ADR per significant decision |
| API documentation | N/A | If exposing APIs |

---

## 8. Governance

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Data governance council | N/A | Formal council for data policies |
| Data stewardship program | Not established | Named stewards per dataset |
| Data quality council | Not established | Cross-functional DQ oversight |
| Data lineage visualization | Via UC UI only | Automated lineage dashboard |
| Data lineage for regulatory reports | Not traced | Trace every RBI report back to source |
| Metadata management | Partial (tags) | Full metadata repository |
| Master data management (MDM) | Not included | MDM platform integration |
| Reference data management | Not included | RDM platform |
| Data classification automation | Manual tags | ML-based classification |

---

## 9. Change & Release Management

| Missing | Why | What a Real Deployment Needs |
|---|---|---|
| Formal CAB process integration | Documented only | ServiceNow change workflow |
| Release notes per change | Via CHANGELOG | Auto-generated release notes |
| Rollback automation | Manual procedure | Automated rollback via feature flags |
| Blue-green deployment | Not implemented | Parallel environments for zero-downtime |
| Canary releases | Not implemented | Gradual rollout with auto-rollback |
| Feature flags | Not used | Toggle-based rollouts |

---

## 10. What IS Included (for balance)

To be clear, this repo **does** include:

- ✅ Complete medallion architecture (Bronze/Silver/Gold)
- ✅ DLT pipelines with expectations
- ✅ Auto Loader ingestion with idempotency
- ✅ SCD2 dimensions via `APPLY CHANGES`
- ✅ Reconciliation framework (count + amount + double-entry)
- ✅ Data contracts (YAML, semver-versioned)
- ✅ PII protection (HMAC + masking + UC tags)
- ✅ Unity Catalog governance (masks, RLS, grants)
- ✅ Workload Identity Federation for CI
- ✅ Terraform IaC (network, KV, UC, DR)
- ✅ Comprehensive documentation (17 docs)
- ✅ Unit tests (26 tests)
- ✅ CI/CD pipeline definition
- ✅ Disaster recovery plan with RPO/RTO
- ✅ Operational runbook + incident response

---

## 11. How to Extend for Production

If you were to take this reference implementation and deploy it to a real bank,
the order of work would be:

| Priority | Workstream | Effort |
|---|---|---|
| **P0** | Real Azure subscription + VNet + Private Endpoints | 2 weeks |
| **P0** | Source system integrations (contracts + connectors) | 4 weeks |
| **P0** | Integration + e2e test suite | 3 weeks |
| **P1** | SIEM + monitoring integration | 2 weeks |
| **P1** | CMK encryption for all data at rest | 1 week |
| **P1** | Immutable blob (WORM) for Bronze archival | 1 week |
| **P1** | PagerDuty + ServiceNow integration | 1 week |
| **P2** | Feature store + ML platform (if needed) | 4 weeks |
| **P2** | Multi-region active-active | 8 weeks |
| **P2** | Pen test + PCI QSA assessment | 6 weeks |

**Total to production-grade:** ~6 months with a small team.

---

## 12. How to Talk About This in an Interview

**Bad (overselling):**
> "I built a production-grade Tier-1 banking data platform."

*Follow-up question: "Which bank?"* → awkward silence.

**Good (honest):**
> "I built an enterprise-grade reference implementation demonstrating the
> patterns used in Tier-1 banking — Medallion, DLT, SCD2, reconciliation,
> Unity Catalog governance, DR planning. It's not deployed in a real bank,
> but the architecture and controls are patterned on real banking requirements."

*Follow-up question: "How would you extend it?"* → see §11.

The second answer is **more credible** and demonstrates engineering maturity.

---

## 13. Change Log

| Date | Change | Author |
|---|---|---|
| 2026-10-04 | Initial draft | Rafik-s |