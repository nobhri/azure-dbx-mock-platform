terraform {
  required_version = ">= 1.5.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~>1.47"
    }
  }
  backend "azurerm" {}
}

# Account-level provider (Unity Catalog metastore lives here)
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
}

# Workspace-scoped provider (for catalogs/schemas/grants)
provider "databricks" {
  alias                       = "workspace"
  azure_workspace_resource_id = var.azure_workspace_resource_id
}
