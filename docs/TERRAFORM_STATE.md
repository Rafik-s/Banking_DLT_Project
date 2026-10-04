# 🔐 Terraform State Security

> **Owner:** Data Platform Engineering
> **Last reviewed:** 2026-10-04
> **Classification:** Internal — Restricted

---

## 1. Why Terraform State Is Sensitive

Terraform state (`.tfstate`) contains **the full configuration and current
state of every resource** Terraform manages. This includes:

- Resource IDs and attributes
- **Some secret values in plaintext** (e.g., default secret values for `databricks_secret` if you don't use external references)
- Service principal IDs and, in some cases, secrets
- Key Vault resource IDs
- SQL warehouse IDs
- Network topology

**A leaked state file is a full infrastructure compromise.**

Never commit `terraform.tfstate` to Git. Never store it on a developer's
laptop for anything beyond throwaway testing.

---

## 2. Backend Architecture

| Aspect | Design |
|---|---|
| **Storage** | Azure Storage Account (dedicated `stbankingtfstate{env}`) |
| **Container** | `tfstate` |
| **Blob key** | `banking-dlt-{env}.tfstate` |
| **Encryption** | Azure Storage Service Encryption (SSE) + infrastructure encryption |
| **Access** | Managed Identity for CI, Entra ID for humans, no shared keys |
| **Locking** | Blob lease (Terraform-native) — prevents concurrent applies |
| **Versioning** | Blob versioning enabled (recover previous state) |
| **Soft delete** | 30-day recovery |
| **Network** | Private endpoint from the VNet (Workstream 6) |
| **RBAC** | `Storage Blob Data Contributor` for SP + platform-admins only |

### Diagram



---

## 3. Setup (One-Time per Environment)

### 3.1 Create the backend resources (bootstrap)

```bash
# Bootstrap script — run once per environment by platform-admin
RG="rg-banking-tfstate-dev"
SA="stbankingtfstatedev"
CONTAINER="tfstate"
LOCATION="centralindia"

az group create -n "$RG" -l "$LOCATION"

az storage account create \
  --name "$SA" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_GPRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --https-only true \
  --require-infrastructure-encryption true

# Enable blob versioning + soft delete
az storage account blob-service-properties update \
  --account-name "$SA" \
  --resource-group "$RG" \
  --enable-versioning true \
  --enable-delete-retention true \
  --delete-retention-days 30

az storage container create -n "$CONTAINER" --account-name "$SA" --auth-mode login

cd terraform
cp backend.tfvars.example backend.tfvars
# Edit backend.tfvars with your real values
terraform init -backend-config=backend.tfvars

# CI service principal
az role assignment create \
  --assignee <sp-object-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$SA

# Platform admins group
az role assignment create \
  --assignee <platform-admins-group-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$SA

  # List blob versions
az storage blob list \
  --account-name stbankingtfstatedev \
  --container-name tfstate \
  --include v \
  --query "[?name=='banking-dlt-dev.tfstate'].{Version:versionId, Time:properties.creationTime}" \
  -o table

# Restore a specific version
az storage blob copy start \
  --account-name stbankingtfstatedev \
  --destination-container tfstate \
  --destination-blob banking-dlt-dev.tfstate \
  --source-uri "https://stbankingtfstatedev.blob.core.windows.net/tfstate/banking-dlt-dev.tfstate?versionid=<version-id>"

  # Detect drift
terraform plan -detailed-exitcode
# Exit code 2 means drift detected

# Reconcile
terraform plan
# Review the changes, then either:
terraform apply            # accept the external change
# OR
terraform import <resource> <id>   # import existing into state

