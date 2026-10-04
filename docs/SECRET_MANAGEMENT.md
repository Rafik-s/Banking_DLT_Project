# 🔑 Secret Management

> **Owner:** Data Platform Engineering + InfoSec
> **Last reviewed:** 2026-10-04
> **Classification:** Internal — Restricted

---

## 1. Principle

**No secret should ever exist in:**
- Source code
- Git history
- CI/CD pipeline variables
- Terraform state
- Notebooks
- Logs
- Slack / Teams messages

All secrets live in **Azure Key Vault** (system of record) and are accessed
via **managed identity** or **Workload Identity Federation**.

---

## 2. Architecture

---

## 3. Secret Inventory

| Secret | Stored In | Accessed By | Rotation |
|---|---|---|---|
| **PII HMAC salt** | KV → Databricks Secret Scope | `security.pii_hmac()` UC function | Annually (or on incident) |
| **Databricks workspace host** | KV | CI/CD (as variable, not secret) | N/A |
| **Databricks resource ID (WIF)** | KV | CI/CD | N/A |
| **Storage account keys** | N/A — use Managed Identity | Databricks Access Connector | N/A |
| **Terraform state backend credentials** | WIF (no secret) | CI/CD | N/A |
| **Service principal client secret** | ❌ NONE — use WIF | — | — |

**Note:** With Workload Identity Federation, there is **no service principal
secret to rotate**. The trust is established via OIDC token exchange between
Azure DevOps and Entra ID.

---

## 4. Workload Identity Federation Setup

### 4.1 Register the Entra App

```bash
# One-time per environment
APP_ID=$(az ad app create --display-name "sp-banking-databricks-${ENV}" --query appId -o tsv)
SP_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)

# Grant Databricks workspace access
databricks service-principals create --application-id "$APP_ID" --display-name "sp-banking-databricks-${ENV}"

# Trust Azure Pipelines OIDC tokens for this service connection
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "azdo-banking-dlt-main",
    "issuer": "https://vstoken.dev.azure.com/<AZDO_ORG_ID>",
    "subject": "sc://<AZDO_ORG>/<AZDO_PROJECT>/<SERVICE_CONNECTION_NAME>",
    "audiences": ["api://AzureADTokenExchange"]
  }'

  