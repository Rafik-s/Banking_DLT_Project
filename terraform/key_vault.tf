# ============================================================================
# KEY VAULT — Secret management for PII salt + config
# ============================================================================

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "banking" {
  name                          = "kv-banking-${var.env}"
  location                      = var.primary_region
  resource_group_name           = azurerm_resource_group.banking.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  soft_delete_retention_days    = 90
  purge_protection_enabled      = true
  enable_rbac_authorization     = true
  public_network_access_enabled = false
}

resource "azurerm_key_vault_secret" "pii_hmac_salt" {
  name         = "pii-hmac-salt"
  value        = var.pii_salt
  key_vault_id = azurerm_key_vault.banking.id

  lifecycle {
    ignore_changes = [value]   # rotate out-of-band, not via Terraform
  }
}

resource "azurerm_key_vault_secret" "databricks_host" {
  name         = "databricks-host"
  value        = "https://${var.databricks_workspace_host}"
  key_vault_id = azurerm_key_vault.banking.id
}

resource "azurerm_key_vault_secret" "databricks_resource_id" {
  name         = "databricks-resource-id"
  value        = var.databricks_workspace_resource_id
  key_vault_id = azurerm_key_vault.banking.id
}

# Grant the Databricks workspace managed identity read access
resource "azurerm_role_assignment" "databricks_kv_reader" {
  scope                = azurerm_key_vault.banking.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_databricks_workspace.banking.managed_identity_id
}

# Databricks secret scope backed by Key Vault
resource "databricks_secret_scope" "pii" {
  name = "banking-pii-${var.env}"

  keyvault_metadata {
    resource_id = azurerm_key_vault.banking.id
    dns_name    = azurerm_key_vault.banking.vault_uri
  }

  depends_on = [azurerm_role_assignment.databricks_kv_reader]
}