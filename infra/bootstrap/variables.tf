variable "tfstate_rg_name" {
  description = "Resource group for tfstate"
  type        = string
}

variable "tfstate_sa_name" {
  description = "Storage account for tfstate"
  type        = string
  default = "tfstateabcd"
}

variable "guardrails_container" {
  description = "Container name for guardrails tfstate"
  type        = string
}

variable "workload_container" {
  description = "Container name for workload tfstate"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "japaneast"
}
