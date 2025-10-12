output "workspace_resource_id" {
  value = azurerm_databricks_workspace.this.id
}

output "workspace_url" {
  value = azurerm_databricks_workspace.this.workspace_url
}

output "workspace_name" {
  value = azurerm_databricks_workspace.this.name
}

output "access_connector_id" {
  value = azurerm_databricks_access_connector.this.id
}

output "access_connector_principal_id" {
  value = azurerm_databricks_access_connector.this.identity[0].principal_id
}

output "storage_account_name" {
  value = azurerm_storage_account.data.name
}

output "uc_root_container" {
  value = azurerm_storage_container.uc_root.name
}

output "location" {
  value = var.location
}
