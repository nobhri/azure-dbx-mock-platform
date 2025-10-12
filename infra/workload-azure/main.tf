# Resource Group
resource "azurerm_resource_group" "this" {
  name     = var.rg_name
  location = var.location
}

# ADLS Gen2
resource "azurerm_storage_account" "data" {
  name                     = var.adls_name
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true

  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = true
}

# Data containers
resource "azurerm_storage_container" "landing" {
  name                  = var.landing_container
  storage_account_name  = azurerm_storage_account.data.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "uc_root" {
  name                  = var.uc_root_container
  storage_account_name  = azurerm_storage_account.data.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "bronze" {
  name                  = var.bronze_container
  storage_account_name  = azurerm_storage_account.data.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = var.silver_container
  storage_account_name  = azurerm_storage_account.data.name
  container_access_type = "private"
}

# Access Connector (Managed Identity for Unity Catalog)
resource "azurerm_databricks_access_connector" "this" {
  name                = "${var.prefix}-ac"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  identity { type = "SystemAssigned" }
}

# RBAC: MI of Access Connector -> Storage Blob Data Contributor (on the SA)
resource "azurerm_role_assignment" "ac_blob_contrib" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.this.identity[0].principal_id
}

# Databricks Workspace
resource "azurerm_databricks_workspace" "this" {
  name                = "${var.prefix}-ws"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = var.workspace_sku
}
