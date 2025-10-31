# -------------------------------------------------------------------
# Derive ABFSS URL for UC storage root (ADLS Gen2)
# -------------------------------------------------------------------
locals {
  storage_root_abfss = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/"
}


# -------------------------------------------------------------------
# Unity Catalog Metastore (ACCOUNT SCOPE)
# -------------------------------------------------------------------
resource "databricks_metastore" "this" {
  provider     = databricks.account

  name         = "mvp-metastore"
  storage_root = local.storage_root_abfss
  owner        = "account_admin"

  # In Azure you can leave "auto" or set an explicit region like "japaneast".
  region       = "auto"
}

# Attach workspace (by numeric workspace_id) to the metastore
resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = var.workspace_id 
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

# Catalog under the attached metastore
resource "databricks_catalog" "catalog" {
  provider = databricks.workspace
  name     = var.catalog_name
  comment  = "Catalog for the mock data platform"

  properties = {
    purpose = "mvp"
  }

  depends_on = [databricks_metastore_assignment.this]
}

# Schemas under the catalog
resource "databricks_schema" "schemas" {
  for_each     = toset(var.schema_names)
  provider     = databricks.workspace
  name         = each.key
  catalog_name = databricks_catalog.catalog.name
  comment      = "Schema ${each.key}"

  depends_on = [databricks_metastore_assignment.this]
}

# Basic grants (adjust to your security model later)
resource "databricks_grants" "catalog_grants" {
  provider = databricks.workspace
  catalog  = databricks_catalog.catalog.name

  grant {
    principal  = "account users"
    privileges = ["USE_CATALOG"]
  }

  depends_on = [databricks_metastore_assignment.this]
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

  depends_on = [databricks_metastore_assignment.this]
}
