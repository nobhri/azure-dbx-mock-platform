terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.95"
    }
  }

  # Configured by Taskfile (azurerm remote backend)
  backend "azurerm" {}
}

# ----------------------------
# Account-scope provider
# - Used for UC (metastore, assignment, account-level ops)
# ----------------------------
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
}

# ----------------------------
# Workspace-scope provider
# - Used for workspace resources (catalog, schema, grants, creds, locations)
# ----------------------------
provider "databricks" {
  alias                       = "workspace"
  azure_workspace_resource_id = var.azure_workspace_resource_id
}
