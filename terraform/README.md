# 🌍 Terraform — Infrastructure as Code

> **Owner:** Data Platform Engineering
> **Provider:** `databricks/databricks` + `hashicorp/azurerm`

---

## 1. What Terraform Provisions

| Category | Resources |
|---|---|
| **Networking** | VNet, subnets, NAT gateway, Private Endpoints, Private DNS zones, NSGs |
| **Storage** | ADLS Gen2 (raw, checkpoints, metastore), blob versioning, soft delete |
| **Compute** | Databricks workspace (VNet-injected, Secure Cluster Connectivity) |
| **Security** | Key Vault, secret scopes, UC functions, column masks, row filters |
| **Governance** | UC catalog, schemas, grants, PII tags |
| **Observability** | Log Analytics, diagnostic settings |
| **DR** | Secondary region workspace, GRS configuration |

---

## 2. Directory Structure
terraform/
├── backend.tf # Remote state backend
├── backend.tfvars.example # Backend config template
├── variables.tf # Input variables
├── environments.tf # Per-env resource naming + sizing
├── networking.tf # VNet, subnets, Private Endpoints
├── key_vault.tf # Key Vault + secret scopes
├── secrets.tf # Secret scope bootstrap
├── uc_security_policies.tf # UC functions, masks, row filters
├── reconciliation_alerts.tf # Reconciliation views
├── dr_replication.tf # DR workspace + storage replication
├── outputs.tf # Outputs for DAB / CI
└── README.md # This file


---

## 3. State Management

### 3.1 Remote State

State is stored in a dedicated Azure Storage account per environment:

| Env | Storage Account | Container | Key |
|---|---|---|---|
| Dev | `stbankingtfstatedev` | `tfstate` | `banking-dlt-dev.tfstate` |
| QA | `stbankingtfstateqa` | `tfstate` | `banking-dlt-qa.tfstate` |
| Prod | `stbankingtfstateprod` | `tfstate` | `banking-dlt-prod.tfstate` |

**Security controls:**
- Encryption at rest (SSE) + infrastructure encryption
- Blob versioning (recoverable history)
- Soft delete (30-day recovery)
- Blob lease lock (prevents concurrent applies)
- RBAC restricted to platform-admins + CI SP
- No shared keys (Managed Identity only)

See [`docs/TERRAFORM_STATE.md`](../docs/TERRAFORM_STATE.md) for full details.

### 3.2 Initializing

```bash
cd terraform

# Copy the backend config template
cp backend.tfvars.example backend.tfvars
# Edit with real values

# Initialize (only the first time)
terraform init -backend-config=backend.tfvars

4. Workspaces
Terraform workspaces separate environments' state:

bash
terraform workspace list
terraform workspace new dev
terraform workspace new qa
terraform workspace new prod

terraform workspace select dev
terraform plan -var-file=dev.tfvars
5. Variables
Create a .tfvars file per environment (never commit these):

dev.tfvars
hcl
env                          = "dev"
primary_region               = "centralindia"
secondary_region             = "southindia"
vnet_cidr                    = "10.20.0.0/16"
pii_salt                     = "REPLACE_WITH_RANDOM_32_BYTE_BASE64"
databricks_workspace_host    = "adb-dev-instance.azuredatabricks.net"
databricks_workspace_resource_id = "/subscriptions/.../adb-dev-instance"
prod.tfvars
hcl
env                          = "prod"
primary_region               = "centralindia"
secondary_region             = "southindia"
vnet_cidr                    = "10.10.0.0/16"
pii_salt                     = "<from key vault>"
databricks_workspace_host    = "adb-prod-instance.azuredatabricks.net"
databricks_workspace_resource_id = "/subscriptions/.../adb-prod-instance"
6. Apply Flow
bash
# 1. Select environment
terraform workspace select prod

# 2. Plan
terraform plan -var-file=prod.tfvars -out=tfplan

# 3. Review the plan (human review for prod)
cat tfplan

# 4. Apply
terraform apply tfplan

# 5. Verify
terraform output
Order of Operations
Networking — VNet, subnets, Private Endpoints

Storage — ADLS Gen2 accounts

Key Vault — secret scope + secrets

Databricks workspace — VNet-injected

UC security — functions, masks, row filters

DR — secondary region workspace

Terraform handles the dependency graph automatically via depends_on.

7. Importing Existing Resources
If you've manually created resources and want to bring them under Terraform:

bash
terraform import azurerm_resource_group.banking /subscriptions/<sub>/resourceGroups/rg-banking-prod
Import each resource, then run terraform plan to verify no drift.

8. Drift Detection
Weekly scheduled job runs:

bash
terraform workspace select prod
terraform plan -detailed-exitcode -var-file=prod.tfvars
# Exit code 0 = no changes; 2 = drift detected
Drift is reported to #data-platform and reviewed by the Platform Lead

9. Destroying (Dev only)
⚠️ Never run terraform destroy in QA or Prod.

For Dev:

bash
terraform workspace select dev
terraform destroy -var-file=dev.tfvars
10. Common Errors
Error	Cause	Fix
Backend initialization required	Not initialized	terraform init -backend-config=backend.tfvars
Error acquiring the state lock	Another apply in progress	Wait or force unlock (carefully)
Key Vault name already exists	Soft-deleted KV retains name for 90 days	Purge or use a different name
Subnet is already delegated	Subnet used by another resource	Remove the delegation or use a different subnet
Databricks workspace not found	Workspace creation still in progress	Wait 5 min, retry
11. Change Log
Date	Change	Author
2026-10-04	Networking, Key Vault, DR integration	Data Platform Engineering

