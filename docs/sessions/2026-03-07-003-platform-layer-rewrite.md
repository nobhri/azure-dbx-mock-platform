# Session 2026-03-07-003 — Platform Layer Rewrite (Catalog/Schema/Group/Grant)

## Objective

Rewrite the `platform/` directory to implement the design decisions confirmed in ADR-005 (PR #88,
merged 2026-03-07). Replace the single-template/single-notebook structure with a config-driven
approach using per-responsibility Jinja2 templates and a unified setup notebook.

## Changes Made

### Deleted

- `platform/ddl/catalog_schema.sql.j2` — monolithic template replaced by 4 separate templates
- `platform/notebooks/00_setup_catalog_schema.py` — replaced by `setup_platform.py`

### New: `platform/configs/`

- `catalog_schema.yaml` — Catalog name + Schema list (bronze/silver/gold) with comments
- `groups.yaml` — 3-group structure with membership separation note
- `grants.yaml` — Catalog-level and Schema-level grants per group (ADR-005 schema-level principle)

### New: `platform/templates/`

- `create_catalog.sql.j2` — `CREATE CATALOG IF NOT EXISTS` with managed location
- `create_schema.sql.j2` — `CREATE SCHEMA IF NOT EXISTS` loop over schemas
- `create_groups.sql.j2` — `CREATE GROUP IF NOT EXISTS` loop over groups
- `grant_permissions.sql.j2` — Catalog GRANT loop + Schema GRANT nested loop

### New: `platform/notebooks/setup_platform.py`

Single generic runner notebook:
1. Receives `storage_account_name` and `uc_root_container` via widgets (no `env` widget)
2. Loads all 3 YAML configs
3. Builds managed_location from widget parameters + catalog name
4. Calls `render_and_execute()` for each template in dependency order:
   Catalog → Schema → Groups → Grants

### Modified: `platform/databricks.yml`

- Removed `catalog_env` variable
- Removed `staging` target (single Catalog: dev + prod sufficient)
- Renamed job: `setup_catalog_schema` → `setup_platform`
- Renamed task key: `ddl` → `platform_ddl_and_grants`
- Updated `notebook_path` and `base_parameters` (removed `env` param)

### Modified: `.github/workflows/workload-catalog.yaml`

- Removed `workflow_dispatch.inputs.target` (staging option eliminated)
- Simplified `concurrency.group` expression
- Updated `Set bundle target` step: workflow_dispatch always targets `dev`
- Updated bundle run step: `setup_catalog_schema` → `setup_platform`

## Design Decisions Applied

| Decision | Implementation |
|----------|---------------|
| Single Catalog (`mock`) | `configs/catalog_schema.yaml`: `name: mock` |
| No env-differentiated GRANTs | Single `grants.yaml`; ADR-005 documents prod difference |
| Schema-level grants | `grants.yaml` structure: per-schema, not per-catalog |
| Group membership outside repo | `groups.yaml` comment explains membership separation |
| YAML-driven templates | Notebook is a generic runner; logic is in configs + templates |
| 1 Job (dependency order enforced) | Step order in notebook: Catalog→Schema→Groups→Grants |

## Branch

`feature/platform-layer-rewrite`
