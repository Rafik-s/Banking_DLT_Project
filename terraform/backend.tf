# ============================================================================
# TERRAFORM REMOTE BACKEND
#
# State is stored in Azure Storage with:
#   - Encryption at rest (Azure-managed keys + optional CMK)
#   - Blob versioning (recoverable state history)
#   - Soft delete (7-day recovery)
#   - Resource lock (prevents concurrent applies)
#   - Restricted RBAC (only platform-admins + service principal)
#
# Setup (run once per environment):
#   terraform -chdir=terraform init \
#     -backend-config=backend.tfvars
# ============================================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  backend "azurerm" {
    # All values supplied via backend.tfvars (never committed).
    # See backend.tfvars.example.
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false   # enforce soft delete on KV
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

provider "databricks" {
  host = "https://${var.databricks_workspace_host}"

  # Azure CLI auth (WIF) — no PAT, no service principal secret.
  # In CI, OIDC token from Azure Pipelines flows through to Entra ID.
  auth_type = "azure-cli"
}