# Session 2026-03-07-002 — ADR-005: Grant Responsibility Moved to Platform Layer

## Objective

Update ADR-005 (Identity & Permission Model) to reflect the confirmed design decision that all
Metastore-scoped grants are managed by the Platform Layer (SQL/Jinja2), not Terraform. Update
README accordingly.

## Changes Made

### `docs/adr/005-group-permissions.md` — full rewrite

- **Decision section:** Added explicit responsibility boundary — Terraform ends at infrastructure
  creation; all Metastore-scoped grants (Workspace, Catalog, Schema) belong to Platform Layer.
  Added rationale for why grants follow the SQL layer (same lifecycle as the objects they govern).
- **Trade-offs Accepted:** Added Mock Implementation Simplification (native groups vs EntraID Sync)
  and Membership Separation (what's in the repo vs what's managed externally).
- **Group Design:** New section documenting the 3-group structure (`data_platform_admins`,
  `data_engineers`, `data_consumers`) with typical roles, responsibilities, and grant granularity
  (Schema level, not Catalog level).
- **Environment-Specific GRANT:** New section documenting prod vs dev/qa GRANT differences
  (prod: data_engineers READ only; dev/qa: READ + WRITE).
- **Mock Environment Simplification:** New section documenting single Catalog, no env-differentiated
  GRANTs, and native groups.
- **Consequences:** Updated to reflect new audit sources (system tables + repo YAML, not Terraform
  state). Updated workspace addition to be a two-step process.
- **Catalog/Schema Decommissioning:** New section with prod decommissioning options table and
  recommended soft-delete procedure.

### `README.md` — three patches

1. Architecture Overview figure: `Terraform` → `Platform Layer (SQL)` for group assignment line
2. Layer Separation figure: `Catalog / Schema Layer` → `Catalog / Schema / Permission Layer`
3. ADR-005 summary: updated to reflect Platform Layer grants and Mock simplification

## Issues Addressed

- Closes #87 — ADR conflict (ADR-001 assigns catalog to Jinja2; ADR-005 previously assigned grants
  to Terraform). Resolution: Option A — amend ADR-005, move grants to Platform Layer.

## Branch

`docs/adr-005-grant-platform-layer`
