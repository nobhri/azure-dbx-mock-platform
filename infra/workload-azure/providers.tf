terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.6"
    }
  }

  # Remote state（Actions側で -backend-config 渡す想定）
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}
