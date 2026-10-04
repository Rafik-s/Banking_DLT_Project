
---

## 📄 File 2 (NEW): `docs/NETWORK_ARCHITECTURE.md`

```markdown
# 🌐 Network Architecture

> **Owner:** Cloud Platform Engineering + InfoSec
> **Last reviewed:** 2026-10-04
> **Classification:** Internal — Restricted

---

## 1. Design Principles

1. **Zero public network exposure.** ADLS, Databricks, Key Vault are only accessible via Private Endpoints.
2. **VNet injection for Databricks.** Compute runs inside a dedicated subnet.
3. **Egress control.** Outbound traffic through a firewall with an explicit allowlist.
4. **Least-privilege network ACLs.** NSGs restrict traffic to required ports/paths only.
5. **No storage access keys.** All access via Managed Identity + Private Endpoint.
6. **Region isolation.** Dev / QA / Prod use separate VNets and private DNS zones.

---

## 2. Topology
┌─────────────────────────────────────────────────────────────────────────────┐
│ Azure Subscription: prod-banking-platform │
│ │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ VNet: vnet-banking-prod (10.10.0.0/16) │ │
│ │ │ │
│ │ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ │ │
│ │ │ Subnet: public │ │ Subnet: private │ │ Subnet: dbx- │ │ │
│ │ │ 10.10.1.0/24 │ │ 10.10.2.0/24 │ │ compute │ │ │
│ │ │ │ │ │ │ 10.10.3.0/24 │ │ │
│ │ │ • Azure Bastion │ │ • Private EP for │ │ • Databricks │ │ │
│ │ │ • Jump box │ │ ADLS Gen2 │ │ cluster nodes │ │ │
│ │ │ │ │ • Private EP for │ │ • Photon-enabled │ │ │
│ │ │ │ │ Key Vault │ │ │ │ │
│ │ │ │ │ • Private EP for │ │ │ │ │
│ │ │ │ │ Storage (state) │ │ │ │ │
│ │ │ │ │ • Private EP for │ │ │ │ │
│ │ │ │ │ Databricks UI │ │ │ │ │
│ │ └───────────────────┘ └───────────────────┘ └───────────────────┘ │ │
│ │ │ │
│ │ ┌───────────────────┐ │ │
│ │ │ Subnet: dbx- │ │ │
│ │ │ public │ │ │
│ │ │ 10.10.4.0/24 │ │ │
│ │ │ • NAT gateway │ ─── Egress via Firewall ───► Internet (allowlist only)
│ │ └───────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│ │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Private DNS Zones (linked to VNet) │ │
│ │ • privatelink.dfs.core.windows.net (ADLS) │ │
│ │ • privatelink.vaultcore.azure.net (Key Vault) │ │
│ │ • privatelink.azuredatabricks.net (Databricks UI/API) │ │
│ │ • privatelink.blob.core.windows.net (Storage accounts) │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘


---

## 3. Private Endpoints

| Service | Private Endpoint | Subnet | DNS Zone |
|---|---|---|---|
| **ADLS Gen2 (raw)** | `pe-adls-raw-prod` | `private` | `privatelink.dfs.core.windows.net` |
| **ADLS Gen2 (checkpoints)** | `pe-adls-ckpt-prod` | `private` | `privatelink.dfs.core.windows.net` |
| **ADLS Gen2 (metastore)** | `pe-adls-meta-prod` | `private` | `privatelink.dfs.core.windows.net` |
| **Key Vault** | `pe-kv-prod` | `private` | `privatelink.vaultcore.azure.net` |
| **Terraform state storage** | `pe-tfstate-prod` | `private` | `privatelink.blob.core.windows.net` |
| **Databricks workspace (UI/API)** | `pe-dbx-prod` | `private` | `privatelink.azuredatabricks.net` |

**Public network access is DISABLED on all resources.**

---

## 4. Databricks VNet Injection

Databricks workspace is deployed with **VNet injection**:

| Setting | Value |
|---|---|
| **VNet** | `vnet-banking-prod` |
| **Public subnet** | `snet-dbx-public` (10.10.4.0/24) |
| **Private subnet** | `snet-dbx-private` (10.10.3.0/24) |
| **NAT Gateway** | Attached to public subnet (egress) |
| **NSG (public)** | Allows Databricks control plane traffic (documented ports) |
| **NSG (private)** | Allows cluster-to-cluster + cluster-to-Private-EP |
| **No public IPs on clusters** | ✅ |

### 4.1 Secure Cluster Connectivity (No Public IP)

Databricks clusters use **Secure Cluster Connectivity** — no public IPs, all
traffic routed via the control plane over a secure tunnel. This is a
mandatory setting for banking workloads.

---

## 5. Egress Control (Firewall Allowlist)

Outbound internet traffic from Databricks clusters goes through **Azure Firewall**
with an explicit allowlist:

| Destination | Purpose | Port |
|---|---|---|
| `*.databricks.com` | Databricks control plane | 443 |
| `*.azuredatabricks.net` | Databricks workspace | 443 |
| `pypi.org`, `files.pythonhosted.org` | Python packages | 443 |
| `maven.org`, `repo1.maven.org` | JVM dependencies | 443 |
| `github.com` | DAB, if needed | 443 |
| Internal ADLS via Private Endpoint | Data | 443 |

**All other egress is DENIED.** Violations are logged and alerted.

---

## 6. Traffic Flow — Example: Pipeline Reading ADLS
┌───────────────────────────┐
│ Databricks Cluster │
│ (Private subnet) │
└────────────┬──────────────┘
│
│ DNS: stbankingprod001.dfs.core.windows.net
▼
┌───────────────────────────┐
│ Private DNS Zone │
│ privatelink.dfs.core... │
│ → Resolves to 10.10.2.5 │ (Private Endpoint IP, NOT public)
└────────────┬──────────────┘
│
▼
┌───────────────────────────┐
│ Private Endpoint │
│ pe-adls-raw-prod │
└────────────┬──────────────┘
│
▼
┌───────────────────────────┐
│ ADLS Gen2 │
│ stbankingprod001 │
│ (public access = DISABLED)│
└───────────────────────────┘


**Key point:** The Databricks cluster **never** talks to the public internet
for data access. It uses the private endpoint. All data stays inside the VNet.

---

## 7. Environment Isolation

| Environment | VNet | ADLS | Key Vault | Workspace |
|---|---|---|---|---|
| **Dev** | `vnet-banking-dev` (10.20.0.0/16) | `stbankingdev001` | `kv-banking-dev` | `adb-dev-instance` |
| **QA** | `vnet-banking-qa` (10.30.0.0/16) | `stbankingqa001` | `kv-banking-qa` | `adb-qa-instance` |
| **Prod** | `vnet-banking-prod` (10.10.0.0/16) | `stbankingprod001` | `kv-banking-prod` | `adb-prod-instance` |

**No peering between environments.** A Dev cluster cannot reach Prod ADLS.
A QA pipeline cannot read Prod Key Vault. Isolation is enforced at the network layer.

---

## 8. Threat Model

| Threat | Control |
|---|---|
| Internet-based exfiltration | Egress firewall allowlist; no public IPs |
| Lateral movement from Dev to Prod | Separate VNets, no peering |
| ADLS exfiltration via public URL | Public network access disabled |
| Key Vault secret exfiltration | Private Endpoint + RBAC |
| Compromised cluster reads other tenants' data | Workspace-level isolation + Private EP |
| DNS hijacking | Private DNS zones (authoritative for private links) |
| Unauthorized VPN/jumpbox access | Bastion with MFA + PIM + audit log |

---

## 9. Compliance Mapping

| Regulation | Requirement | Implementation |
|---|---|---|
| **RBI Cyber Security Framework** | Network segmentation | VNet isolation per environment |
| **RBI IT Governance** | Data localization | Central India primary; South India DR |
| **DPDP Act 2023** | Prevent unauthorized access | Private Endpoints; no public exposure |
| **PCI-DSS 3.2.1** | 1.3.2: Restrict inbound/outbound | Firewall allowlist; NSGs |
| **ISO 27001** | A.13.1: Network security | VNet + Private Link + NAT |

---

## 10. Change Log

| Date | Change | Author |
|---|---|---|
| 2026-10-04 | Initial draft | Cloud Platform Engineering |

