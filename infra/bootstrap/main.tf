terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource group for tfstate
resource "azurerm_resource_group" "tfstate" {
  name     = var.tfstate_rg_name
  location = var.location
}

# Storage account for tfstate
resource "azurerm_storage_account" "tfstate" {
  name                     = var.tfstate_sa_name
  resource_group_name      = azurerm_resource_group.tfstate.name
  location                 = azurerm_resource_group.tfstate.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = true
}

# Containers for tfstate separation
resource "azurerm_storage_container" "guardrails" {
  name                  = var.guardrails_container
  storage_account_name  = azurerm_storage_account.tfstate.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "workload" {
  name                  = var.workload_container
  storage_account_name  = azurerm_storage_account.tfstate.name
  container_access_type = "private"
}

output "tfstate_storage_account_id" {
  value = azurerm_storage_account.tfstate.id
}
