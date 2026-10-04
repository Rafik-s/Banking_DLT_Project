# ============================================================================
# DISASTER RECOVERY — ADLS geo-replication + failover metadata
# ============================================================================

# ADLS storage account is configured with GRS/RAGRS in environments.tf
# This file adds DR-specific configuration.

# ----------------------------------------------------------------------------
# Secondary region resource group (holds DR workspace metadata)
# ----------------------------------------------------------------------------
resource "azurerm_resource_group" "dr" {
  count    = var.env == "prod" ? 1 : 0
  name     = "rg-banking-dr-${var.env}"
  location = local.env.secondary_region

  tags = azurerm_resource_group.banking.tags
}

# ----------------------------------------------------------------------------
# DR workspace — provisioned but not actively used
# Activated on failover via `az storage account failover`
# ----------------------------------------------------------------------------
resource "azurerm_databricks_workspace" "dr" {
  count                       = var.env == "prod" ? 1 : 0
  name                        = "adb-dr-instance"
  resource_group_name         = azurerm_resource_group.dr[0].name
  location                    = local.env.secondary_region
  sku                         = "premium"

  managed_resource_group_name = "rg-databricks-managed-dr-${var.env}"

  tags = azurerm_resource_group.banking.tags
}

# ----------------------------------------------------------------------------
# Storage account diagnostic settings for replication monitoring
# ----------------------------------------------------------------------------
resource "azurerm_monitor_diagnostic_setting" "raw_storage_dr" {
  count                      = var.env == "prod" ? 1 : 0
  name                       = "diag-storage-dr"
  target_resource_id         = "${azurerm_storage_account.raw.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.banking.id

  enabled_log {
    category = "StorageRead"
  }
  enabled_log {
    category = "StorageWrite"
  }
  enabled_log {
    category = "StorageDelete"
  }

  metric {
    category = "Transaction"
    enabled  = true
  }
}