# Lookup workspace by name using Databricks Account API
data "databricks_workspace" "ws" {
  provider       = databricks.account
  workspace_name = var.workspace_name
}

locals {
  storage_root_abfss = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/"
}

# --- Unity Catalog Metastore (Account scope) ---
resource "databricks_metastore" "this" {
  provider     = databricks.account
  name         = "mvp-metastore"
  storage_root = local.storage_root_abfss
  owner        = "account_admin"
  region       = "auto" # or set explicitly, e.g., "japaneast". "auto" usually resolves in Azure.
}

# Attach Workspace to Metastore
resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = data.databricks_current_workspace.ws.workspace_id  # <-- numeric
}

# Storage Credential via Access Connector (Managed Identity)
resource "databricks_storage_credential" "mi" {
  provider = databricks.workspace
  name     = "uc-mi-credential"

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }

  comment = "Credential using Access Connector managed identity"
}

# External Location for UC Root
resource "databricks_external_location" "uc_root" {
  provider          = databricks.workspace
  name              = "uc-root-location"
  url               = local.storage_root_abfss
  credential_name   = databricks_storage_credential.mi.name
  read_only         = false
  fallback          = false
  force_destroy     = true
  comment           = "UC root external location"
}

# Catalog
resource "databricks_catalog" "catalog" {
  provider = databricks.workspace
  name     = var.catalog_name
  comment  = "Catalog for the mock data platform"
  properties = {
    purpose = "mvp"
  }
}

# Schemas
resource "databricks_schema" "schemas" {
  for_each     = toset(var.schema_names)
  provider     = databricks.workspace
  name         = each.key
  catalog_name = databricks_catalog.catalog.name
  comment      = "Schema ${each.key}"
}

# Basic grants: allow all workspace users to USE catalog (adjust later)
resource "databricks_grants" "catalog_grants" {
  provider   = databricks.workspace
  catalog    = databricks_catalog.catalog.name

  grant {
    principal  = "account users"
    privileges = ["USE_CATALOG"]
  }
}

resource "databricks_grants" "schema_grants" {
  for_each = databricks_schema.schemas
  provider = databricks.workspace
  schema   = each.value.name
  catalog  = databricks_catalog.catalog.name

  grant {
    principal  = "account users"
    privileges = ["USE_SCHEMA"]
  }
}
