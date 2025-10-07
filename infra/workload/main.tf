 # Resource group
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
}

# Access Connector
resource "azurerm_databricks_access_connector" "this" {
  name                = "${var.prefix}-ac"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  identity {
    type = "SystemAssigned"
  }
}

# Databricks Workspace
resource "azurerm_databricks_workspace" "this" {
  name                = "${var.prefix}-ws"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "premium"
}

# Metastore (account-level)
resource "databricks_metastore" "this" {
  provider       = databricks.account
  name           = "${var.prefix}-metastore"
  storage_root   = "abfss://${var.metastore_container}@${azurerm_storage_account.data.name}.dfs.core.windows.net/"
  owner          = "account_admin"
  region         = var.location
}

resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  workspace_id = azurerm_databricks_workspace.this.workspace_id
  metastore_id = databricks_metastore.this.id
}

# Catalog
resource "databricks_catalog" "mock" {
  provider = databricks.workspace
  name     = "mock"
  comment  = "Catalog for mock data platform"
}

# Schemas
resource "databricks_schema" "staging" {
  provider   = databricks.workspace
  name       = "staging"
  catalog_name = databricks_catalog.mock.name
}

resource "databricks_schema" "serving" {
  provider   = databricks.workspace
  name       = "serving"
  catalog_name = databricks_catalog.mock.name
}
