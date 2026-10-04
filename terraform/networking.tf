
---

## 📄 File 7 (NEW): `terraform/networking.tf`

```hcl
# ============================================================================
# NETWORKING — VNet, Subnets, Private Endpoints, DNS
# ============================================================================

resource "azurerm_virtual_network" "banking" {
  name                = "vnet-banking-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name
  address_space       = [var.vnet_cidr]
}

resource "azurerm_subnet" "public" {
  name                 = "snet-public"
  resource_group_name  = azurerm_resource_group.banking.name
  virtual_network_name = azurerm_virtual_network.banking.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 8, 1)]
}

resource "azurerm_subnet" "private" {
  name                 = "snet-private"
  resource_group_name  = azurerm_resource_group.banking.name
  virtual_network_name = azurerm_virtual_network.banking.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 8, 2)]

  private_endpoint_network_policies_enabled = true
}

resource "azurerm_subnet" "dbx_public" {
  name                 = "snet-dbx-public"
  resource_group_name  = azurerm_resource_group.banking.name
  virtual_network_name = azurerm_virtual_network.banking.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 8, 3)]

  delegation {
    name = "databricks"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
    }
  }
}

resource "azurerm_subnet" "dbx_private" {
  name                 = "snet-dbx-private"
  resource_group_name  = azurerm_resource_group.banking.name
  virtual_network_name = azurerm_virtual_network.banking.name
  address_prefixes     = [cidrsubnet(var.vnet_cidr, 8, 4)]

  delegation {
    name = "databricks"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
    }
  }
}

# ----------------------------------------------------------------------------
# NAT gateway for egress
# ----------------------------------------------------------------------------
resource "azurerm_public_ip" "nat" {
  name                = "pip-nat-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_nat_gateway" "nat" {
  name                    = "nat-banking-${var.env}"
  location                = var.primary_region
  resource_group_name     = azurerm_resource_group.banking.name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
}

resource "azurerm_nat_gateway_public_ip_association" "nat" {
  nat_gateway_id       = azurerm_nat_gateway.nat.id
  public_ip_address_id = azurerm_public_ip.nat.id
}

resource "azurerm_subnet_nat_gateway_association" "dbx_public" {
  subnet_id      = azurerm_subnet.dbx_public.id
  nat_gateway_id = azurerm_nat_gateway.nat.id
}

# ----------------------------------------------------------------------------
# Private DNS Zones
# ----------------------------------------------------------------------------
locals {
  private_dns_zones = {
    adls    = "privatelink.dfs.core.windows.net"
    blob    = "privatelink.blob.core.windows.net"
    kv      = "privatelink.vaultcore.azure.net"
    dbx     = "privatelink.azuredatabricks.net"
  }
}

resource "azurerm_private_dns_zone" "zones" {
  for_each            = local.private_dns_zones
  name                = each.value
  resource_group_name = azurerm_resource_group.banking.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "links" {
  for_each              = local.private_dns_zones
  name                  = "link-${each.key}-${var.env}"
  resource_group_name   = azurerm_resource_group.banking.name
  private_dns_zone_name = azurerm_private_dns_zone.zones[each.key].name
  virtual_network_id    = azurerm_virtual_network.banking.id
  registration_enabled  = false
}

# ----------------------------------------------------------------------------
# Private Endpoints
# ----------------------------------------------------------------------------
resource "azurerm_private_endpoint" "adls_raw" {
  name                = "pe-adls-raw-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name
  subnet_id           = azurerm_subnet.private.id

  private_service_connection {
    name                           = "psc-adls-raw-${var.env}"
    private_connection_resource_id = azurerm_storage_account.raw.id
    is_manual_connection           = false
    subresource_names              = ["dfs"]
  }

  private_dns_zone_group {
    name                 = "dns-adls-raw"
    private_dns_zone_ids = [azurerm_private_dns_zone.zones["adls"].id]
  }
}

resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-kv-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name
  subnet_id           = azurerm_subnet.private.id

  private_service_connection {
    name                           = "psc-kv-${var.env}"
    private_connection_resource_id = azurerm_key_vault.banking.id
    is_manual_connection           = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "dns-kv"
    private_dns_zone_ids = [azurerm_private_dns_zone.zones["kv"].id]
  }
}

resource "azurerm_private_endpoint" "databricks" {
  name                = "pe-dbx-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name
  subnet_id           = azurerm_subnet.private.id

  private_service_connection {
    name                           = "psc-dbx-${var.env}"
    private_connection_resource_id = azurerm_databricks_workspace.banking.id
    is_manual_connection           = false
    subresource_names              = ["databricks_ui_api"]
  }

  private_dns_zone_group {
    name                 = "dns-dbx"
    private_dns_zone_ids = [azurerm_private_dns_zone.zones["dbx"].id]
  }
}

# ----------------------------------------------------------------------------
# NSGs
# ----------------------------------------------------------------------------
resource "azurerm_network_security_group" "dbx_public" {
  name                = "nsg-dbx-public-${var.env}"
  location            = var.primary_region
  resource_group_name = azurerm_resource_group.banking.name

  security_rule {
    name                       = "AllowDatabricksControlPlane"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "AzureDatabricks"
  }

  security_rule {
    name                       = "AllowVnetInbound"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  security_rule {
    name                       = "DenyAllInbound"
    priority                   = 4000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "dbx_public" {
  subnet_id                 = azurerm_subnet.dbx_public.id
  network_security_group_id = azurerm_network_security_group.dbx_public.id
}
