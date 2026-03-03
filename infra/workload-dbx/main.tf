# -------------------------------------------------------------------
# Derive ABFSS URL for UC storage root (ADLS Gen2)
# -------------------------------------------------------------------
locals {
  storage_root_abfss = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/"
}

# -------------------------------------------------------------------
# Derive workspace info
# -------------------------------------------------------------------

data "azurerm_databricks_workspace" "ws" {
  # name / resource_group_name でも良いけど、IDがあるのでシンプルに
  name                = var.workspace_name
  resource_group_name = var.resource_group_name
}

# numeric workspace_id を local に格納
locals {
  # azurerm 側は number（環境によって string のこともある）。万一に備えて tonumber を噛ませてもOK
  workspace_id = try(
    tonumber(data.azurerm_databricks_workspace.ws.workspace_id),
    data.azurerm_databricks_workspace.ws.workspace_id
  )
}

locals {
  azure_region = lower(replace(data.azurerm_databricks_workspace.ws.location, " ", ""))
}



# -------------------------------------------------------------------
# Unity Catalog Metastore (ACCOUNT SCOPE)
# -------------------------------------------------------------------

resource "databricks_metastore" "this" {
  provider = databricks.account

  name = "mvp-metastore"
  # storage_root = local.storage_root_abfss
  storage_root = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/${var.metastore_id}"
  # force_destroy allows Terraform destroy to cascade-delete all UC objects
  # (catalogs, schemas, storage credentials) even when not managed by Terraform
  # (e.g. catalog/schema created by Jinja2 notebook — see ADR-001).
  force_destroy = true
  lifecycle {
    ignore_changes  = [storage_root, owner]
    # prevent_destroy = true # enable if you want to keep this metastore permananent.
  }
  region = local.azure_region

}

# Attach workspace (by numeric workspace_id) to the metastore
resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = local.workspace_id
}

# -------------------------------------------------------------------
# Workspace-scope objects (require the workspace to be attached to UC)
# -------------------------------------------------------------------

# Storage Credential using Access Connector (Managed Identity)
resource "databricks_storage_credential" "mi" {
  provider = databricks.workspace
  name     = "uc-mi-credential"

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }

  comment = "Credential using Access Connector managed identity"

  # Ensure metastore is attached before creating workspace objects
  depends_on = [databricks_metastore_assignment.this]
}

# External Location that points to the UC root
resource "databricks_external_location" "uc_root" {
  provider        = databricks.workspace
  name            = "uc-root-location"
  url             = local.storage_root_abfss
  credential_name = databricks_storage_credential.mi.name

  read_only     = false
  fallback      = false
  force_destroy = true
  comment       = "UC root external location"

  depends_on = [databricks_metastore_assignment.this]
}

# Catalog and schema management is intentionally handled outside Terraform.
# See ADR-001: Jinja2 + Python Notebook manages catalog/schema to avoid
# Terraform lifecycle conflicts with Unity Catalog bootstrap ordering.
# The resources below were prototyped but deferred to the notebook layer.

# # Catalog under the attached metastore
# resource "databricks_catalog" "catalog" {
#   provider = databricks.workspace
#   name     = var.catalog_name
#   comment  = "Catalog for the mock data platform"

#   properties = {
#     purpose = "mvp"
#   }

#   depends_on = [databricks_metastore_assignment.this]
# }

# # Schemas under the catalog
# resource "databricks_schema" "schemas" {
#   for_each     = toset(var.schema_names)
#   provider     = databricks.workspace
#   name         = each.key
#   catalog_name = databricks_catalog.catalog.name
#   comment      = "Schema ${each.key}"

#   depends_on = [databricks_metastore_assignment.this]
# }

# # Basic grants (adjust to your security model later)
# resource "databricks_grants" "catalog_grants" {
#   provider = databricks.workspace
#   catalog  = databricks_catalog.catalog.name

#   grant {
#     principal  = "account users"
#     privileges = ["USE_CATALOG", "USE_SCHEMA"]
#   }

#   depends_on = [databricks_metastore_assignment.this]
# }

# resource "databricks_grants" "schema_grants" {
#   for_each = toset(var.schema_names)
#   provider = databricks.workspace
#   schema   = databricks_schema.schemas[each.key].id
#   catalog  = databricks_catalog.catalog.name

#   grant {
#     principal  = "account users"
#     privileges = ["USE_SCHEMA"]
#   }

#   depends_on = [
#     databricks_schema.schemas
#   ]
# }
