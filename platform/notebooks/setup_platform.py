# Databricks notebook source

# COMMAND ----------

# Platform Layer setup -- Catalog, Schema, Groups, Grants
# ADR-001: Catalog/Schema managed here, NOT in Terraform
# ADR-005: Group-based access control
# ADR-003: All statements idempotent -- safe to re-run

import os
import yaml
from jinja2 import Template

# COMMAND ----------

# Parameters from Asset Bundles / Workflow Dispatch
dbutils.widgets.text("storage_account_name", "")
dbutils.widgets.text("uc_root_container", "")

storage_account_name = dbutils.widgets.get("storage_account_name")
uc_root_container = dbutils.widgets.get("uc_root_container")

print(f"Storage account  : {storage_account_name}")
print(f"UC root container: {uc_root_container}")

# COMMAND ----------

# Resolve paths relative to this notebook's location at runtime.
# notebookPath() returns e.g.:
#   /Users/<sp>/mock-platform-catalog/notebooks/setup_platform
# Two dirname calls -> bundle root; configs/ and templates/ live alongside notebooks/.
notebook_path = (
    dbutils.notebook.entry_point
    .getDbutils().notebook().getContext().notebookPath().get()
)
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
configs_dir = f"/Workspace{bundle_root}/configs"
templates_dir = f"/Workspace{bundle_root}/templates"

print(f"Bundle root  : {bundle_root}")
print(f"Configs dir  : {configs_dir}")
print(f"Templates dir: {templates_dir}")

# COMMAND ----------

def load_yaml(filename):
    """Load a YAML config file from configs/."""
    path = f"{configs_dir}/{filename}"
    with open(path) as f:
        return yaml.safe_load(f)


def render_and_execute(template_file, template_vars, warn_on_principal_missing=False):
    """Read a Jinja2 template, render it, and execute each SQL statement.

    If warn_on_principal_missing=True, statements that fail with
    PRINCIPAL_DOES_NOT_EXIST emit a warning and continue rather than raising.
    This is used for GRANT statements targeting groups that may not yet
    exist as account-level principals in Unity Catalog.
    """
    path = f"{templates_dir}/{template_file}"
    print(f"\n{'=' * 60}")
    print(f"Processing: {template_file}")
    print(f"{'=' * 60}")

    with open(path) as f:
        raw = f.read()

    rendered = Template(raw).render(**template_vars)
    print(rendered)

    # Strip comment lines and split into individual statements
    sql_no_comments = "\n".join(
        line for line in rendered.splitlines()
        if not line.strip().startswith("--")
    )
    statements = [s.strip() for s in sql_no_comments.split(";") if s.strip()]

    for stmt in statements:
        print(f"\nExecuting:\n{stmt}\n")
        try:
            spark.sql(stmt)
        except Exception as e:
            if warn_on_principal_missing and "PRINCIPAL_DOES_NOT_EXIST" in str(e):
                print(f"WARNING: principal not found -- skipping grant.\n"
                      f"  Create the group as an account-level group first.\n"
                      f"  Details: {e}\n")
            else:
                raise

# COMMAND ----------

# Load all configs
catalog_schema_config = load_yaml("catalog_schema.yaml")
groups_config = load_yaml("groups.yaml")
grants_config = load_yaml("grants.yaml")

catalog = catalog_schema_config["catalog"]
schemas = catalog_schema_config["schemas"]

# Build managed location from widget parameters
managed_location = (
    f"abfss://{uc_root_container}@{storage_account_name}"
    f".dfs.core.windows.net/catalogs/{catalog['name']}"
)

print(f"Catalog          : {catalog['name']}")
print(f"Schemas          : {[s['name'] for s in schemas]}")
print(f"Groups           : {[g['name'] for g in groups_config['groups']]}")
print(f"Managed location : {managed_location}")

# COMMAND ----------

# Step 1: CREATE CATALOG
render_and_execute("create_catalog.sql.j2", {
    "catalog": catalog,
    "managed_location": managed_location,
})

# COMMAND ----------

# Step 2: CREATE SCHEMA
render_and_execute("create_schema.sql.j2", {
    "catalog": catalog,
    "schemas": schemas,
})

# COMMAND ----------

# Step 3: Group prerequisite notice
# Unity Catalog GRANT requires account-level groups, not workspace-local groups.
# Workspace SCIM groups (created via /api/2.0/preview/scim/v2/Groups) are NOT
# visible to UC GRANT -- they live in a different scope.
# Account-level groups must be created manually via:
#   - Databricks Account Console > Groups
#   - Databricks CLI: databricks groups create --profile <account-profile>
# This is the same pattern as SP grants (post-destroy-grants.md runbook).
# Group names expected by the GRANT step:
for group in groups_config["groups"]:
    print(f"  Required account-level group: {group['name']}")
print("\nIf any groups above do not exist at the account level, the GRANT step")
print("below will skip those grants with a WARNING (not an error).")
print("Re-run workload-catalog after creating the groups to apply all grants.")

# COMMAND ----------

# Step 4: GRANT PERMISSIONS
# warn_on_principal_missing=True: skips grants for groups not yet created at
# the account level. The job succeeds with a warning; re-run after group creation
# to apply the skipped grants (all GRANT statements are idempotent).
render_and_execute("grant_permissions.sql.j2", {
    "catalog": catalog,
    "catalog_grants": grants_config["catalog_grants"],
    "schema_grants": grants_config["schema_grants"],
}, warn_on_principal_missing=True)

# COMMAND ----------

print("Done -- catalog and schema objects are in place.")
print("If WARNING lines appeared above, create the missing account-level groups")
print("and re-run workload-catalog to apply the deferred grants.")
