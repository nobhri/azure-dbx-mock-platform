# Azure Subscription ID for azurerm provider
variable "subscription_id" {
  description = "Azure Subscription ID for the azurerm provider (used when use_cli=true but explicit ID is required)"
  type        = string
}

variable "azure_tenant_id" {
  description = "Azure AD tenant ID used for account-scope Databricks auth"
  type        = string
}

variable "databricks_account_id" {
  description = "Databricks Account ID (from the Account Console URL 'o=<UUID>')"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group where the Databricks workspace exists"
  type        = string
}

variable "azure_workspace_resource_id" {
  description = "Azure Resource ID of the Databricks Workspace (from workload-azure outputs)"
  type        = string
}

# variable "workspace_id" {
#   description = "Numeric Databricks workspace_id (from Account API)"
#   type        = string
# }

variable "workspace_name" {
  description = "Workspace display name as created in Azure (used to find numeric workspace_id)"
  type        = string
}

variable "access_connector_id" {
  description = "Azure Databricks Access Connector resource ID (for MI-based storage credential)"
  type        = string
}

variable "storage_account_name" {
  description = "ADLS Gen2 account name hosting the UC root container"
  type        = string
}

variable "uc_root_container" {
  description = "Container name for the UC storage root (must exist; lower-case)"
  type        = string
  default     = "uc-root"
}

# variable "catalog_name" {
#   description = "Name of the catalog to create under the metastore"
#   type        = string
#   default     = "mock"
# }

# variable "schema_names" {
#   description = "List of schemas to create in the catalog"
#   type        = list(string)
#   default     = ["staging", "serving"]
# }
