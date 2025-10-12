variable "databricks_account_id" {
  description = "Databricks Account ID (from the Accounts console)"
  type        = string
}

# From workload-azure outputs (pass via workflow)
variable "azure_workspace_resource_id" {
  description = "Azure Resource ID of the Databricks Workspace"
  type        = string
}

variable "access_connector_id" {
  description = "Resource ID of the Databricks Access Connector"
  type        = string
}

variable "storage_account_name" {
  description = "ADLS Gen2 account name for UC root"
  type        = string
}

variable "uc_root_container" {
  description = "Container name for UC storage root"
  type        = string
  default     = "uc-root"
}

variable "catalog_name" {
  type    = string
  default = "mock"
}

variable "schema_names" {
  type    = list(string)
  default = ["staging", "serving"]
}
