variable "rg_name" {
  default = "rg-mock-data"
}

variable "location" {
  default = "japaneast"
}

variable "adls_name" {
  description = "ADLS Gen2 account name (must be unique)"
  type        = string
}

variable "prefix" {
  default = "mock"
}

variable "databricks_account_id" {
  description = "Databricks account ID"
  type        = string
}

variable "metastore_container" {
  description = "ADLS container for Unity Catalog metastore"
  type        = string
  default     = "uc-root"
}
