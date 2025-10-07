terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.100"
    }
  }

  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}

# Subscription-level budget
resource "azurerm_consumption_budget_subscription" "monthly" {
  name              = "budget-mvp"
  subscription_id   = var.subscription_id
  amount            = var.budget_amount
  time_grain        = "Monthly"
  time_period {
    start_date = var.budget_start
    end_date   = var.budget_end
  }
  notification {
    enabled   = true
    threshold = 80.0
    operator  = "EqualTo"
    contact_emails = var.alert_emails
  }
}
