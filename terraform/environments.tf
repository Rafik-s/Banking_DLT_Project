# ============================================================================
# ENVIRONMENT CONFIGURATION — environment-specific defaults
# ============================================================================

locals {
  env_config = {
    dev = {
      vnet_cidr       = "10.20.0.0/16"
      primary_region  = "centralindia"
      secondary_region= "southindia"
      storage_repl    = "LRS"      # dev doesn't need geo-replication
      approval_gate   = false
    }
    qa = {
      vnet_cidr       = "10.30.0.0/16"
      primary_region  = "centralindia"
      secondary_region= "southindia"
      storage_repl    = "ZRS"
      approval_gate   = true
    }
    prod = {
      vnet_cidr       = "10.10.0.0/16"
      primary_region  = "centralindia"
      secondary_region= "southindia"
      storage_repl    = "RAGRS"    # read-access geo-redundant
      approval_gate   = true
    }
  }

  env = local.env_config[var.env]
}

# ----------------------------------------------------------------------------
# Resource Group
# ----------------------------------------------------------------------------
resource "azurerm_resource_group" "banking" {
  name     = "rg-banking-${var.env}"
  location = local.env.primary_region

  tags = {
    Environment = var.env
    Owner       = "data-platform"
    CostCenter  = "CDP-001"
    Compliance  = "DPDP,PCI,RBI"
  }
}

# ----------------------------------------------------------------------------
# ADLS Gen2 Storage Accounts
# ----------------------------------------------------------------------------
resource "azurerm_storage_account" "raw" {
  name                          = "stbanking${var.env}001"
  resource_group_name           = azurerm_resource_group.banking.name
  location                      = local.env.primary_region
  account_tier                  = "Standard"
  account_replication_type      = local.env.storage_repl
  account_kind                  = "StorageV2"
  is_hns_enabled                = true
  min_tls_version               = "TLS1_2"
  public_network_access_enabled = false
  shared_access_key_enabled     = false   # enforce Managed Identity
  https_traffic_only_enabled    = true

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }
}

# ----------------------------------------------------------------------------
# Databricks Workspace (VNet-injected)
# ----------------------------------------------------------------------------
resource "azurerm_databricks_workspace" "banking" {
  name                        = "adb-${var.env}-instance"
  resource_group_name         = azurerm_resource_group.banking.name
  location                    = local.env.primary_region
  sku                         = "premium"

  managed_resource_group_name = "rg-databricks-managed-${var.env}"

  custom_parameters {
    virtual_network_id                                   = azurerm_virtual_network.banking.id
    public_subnet_name                                   = azurerm_subnet.dbx_public.name
    private_subnet_name                                  = azurerm_subnet.dbx_private.name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.dbx_public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.dbx_public.id
    no_public_ip                                         = true
  }

  tags = azurerm_resource_group.banking.tags
}