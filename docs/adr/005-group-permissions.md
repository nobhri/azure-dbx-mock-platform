# ADR-005: Identity & Permission Model — Group-Based Access via EntraID Sync

**Status:** Accepted (updated 2026-03-07)
**Date:** 2026-02-01

---

## Context

Databricks Unity Catalog supports granting permissions to individual users, service principals, or
groups. In an enterprise environment with multiple workspaces and catalogs, how should access be
structured so that it remains auditable and manageable as the team scales?

---

## Decision

Permissions are assigned to **Groups only — never to individual users or service principals
(except the platform SP itself)**. No `GRANT` to individual user principals appears anywhere in
the platform automation.

**Responsibility boundary:** Everything under Metastore Admin jurisdiction is managed by the
Platform Layer (SQL/Jinja2), not Terraform:

- Workspace permission grants (who can enter the Workspace)
- Catalog and Schema permission grants
- Group management within Databricks

Terraform's responsibility ends at infrastructure creation:

- Azure resources, Databricks Workspace creation, Metastore creation
- Workspace-to-Metastore binding

Terraform does not touch any grants or permissions for Metastore-scoped resources.

In production environments, EntraID Groups are synced into Databricks via **Native Sync**
(not SCIM provisioning). In this mock environment, Databricks-native groups are used as a
simplification (see [Trade-offs Accepted](#trade-offs-accepted)).

---

## Rationale

Individual permission grants fail at scale for three reasons:

1. **Audit drift** — "Who has access to prod catalog?" requires enumerating all individual grants
   across every resource. With group-based access, the answer is: "Members of group X."

2. **Offboarding gap** — when an individual is removed from the organization, their individual
   Databricks grants are often forgotten. Group-based access ensures offboarding from EntraID
   propagates automatically to all Databricks resources.

3. **Onboarding friction** — granting access to a new team member via individual grants requires
   updating every resource. Adding them to the correct EntraID group grants all necessary access
   in a single operation.

**Why Platform Layer (SQL) instead of Terraform for grants?**

Catalog, Schema, and their GRANTs share the same lifecycle: they are created, modified, and
retired together by the Data Platform team. Placing GRANTs in Terraform while the objects they
govern are managed in SQL would split responsibility for the same resource across two tools and
two teams, breaking the principle that Terraform owns infrastructure and the Platform Layer owns
Metastore-scoped governance.

---

## Trade-offs Accepted

- Group management is now a prerequisite: before a new team member can access any Databricks
  resource, the correct group must exist and be assigned. This is additional setup friction
  for the first deployment.
- Native Sync has a propagation delay: group membership changes in EntraID take some minutes to
  appear in Databricks. This is acceptable for access management (not a real-time requirement).
- Service principal grants (e.g., the CI/CD SP) are an exception to the group-only rule — the SP
  is granted directly as it is not a human user and has no EntraID group membership.

**Mock Implementation Simplification:**

In this mock environment, EntraID Sync is omitted and Databricks-native groups are used instead.
Demonstrating IdP sync in a single-developer repository adds setup complexity without validating
the group-based access principle itself — native groups are still groups. In production,
EntraID Native Sync must be used (this ADR's recommendation is unchanged).

**Membership Separation:**

Group structure (what groups exist) and permissions (GRANT statements) are declared in the
repository and managed via CI/CD. Group membership (who belongs to each group) is managed outside
the repository:

- **Mock:** Databricks CLI or Account Console GUI
- **Production:** EntraID (user assignment to EntraID groups; Native Sync propagates to Databricks)

Email addresses and individual user identifiers are not committed to this repository (public repo).
This separation is consistent with the principle that membership is an IdP concern, not a
platform-layer concern.

---

## Why Native Sync Over SCIM?

| Dimension              | Native Sync                   | SCIM Provisioning             |
|------------------------|-------------------------------|-------------------------------|
| Nested group support   | Yes                           | Limited                       |
| Setup complexity       | Lower (no external SCIM app)  | Higher (requires SCIM config) |
| Sync trigger           | Near-real-time (token issue)  | Configurable polling          |
| Group creation in DBX  | Automatic                     | Requires SCIM PUT             |

Native Sync is preferred because it supports nested groups (which SCIM provisioning handles
inconsistently across IdP versions) and requires no external SCIM application configuration.

---

## Group Design

Three groups cover the full access topology (management / production / consumption):

### `data_platform_admins`

Full access across all environments. Responsible for platform operations.

- **Typical roles:** Data Platform team, IT Infrastructure team members who operate the data
  platform
- **Responsibilities:** Catalog/Schema creation, GRANT management, audit, troubleshooting
- **Note:** In smaller organizations, Data Engineers may hold this role as well

### `data_engineers`

- **dev/qa:** READ + WRITE — interactive development and validation
- **prod:** READ only — writes to prod are CI/CD Job-only; no direct human writes
- **Typical roles:** Data Engineering team, Analytics Engineering team
- **Responsibilities:** ETL pipeline development, data modeling, table/view creation
- **Design intent:** Separating prod write access from dev/qa write access enforces CI/CD
  discipline without blocking developer iteration

### `data_consumers`

READ access to the gold/analytics layer only.

- **Typical roles:** BI/reporting teams, business units (sales, manufacturing, HR, finance, etc.),
  leadership
- **Responsibilities:** Dashboard creation, ad-hoc analysis on curated datasets
- **Note:** Depending on organizational policy, consumers may be granted access to SQL Warehouses
  only — not to interactive clusters

### Grant Granularity

GRANTs are defined at **Schema level**, not Catalog level. Reason: within a single Catalog,
schemas may carry data of different sensitivity and purpose (e.g., `bronze` vs `gold`).
Catalog-level grants would over-provision access.

---

## Environment-Specific GRANT (Production Consideration)

In this mock environment, a single Catalog (`mock`) is used and GRANTs are not differentiated by
environment (see [Mock Environment Simplification](#mock-environment-simplification)).

In production, environments should be separated by Catalog or Workspace, and GRANTs should
reflect that separation:

- **prod:** `data_engineers` receive READ only. Writes are performed exclusively by CI/CD Jobs
  (Service Principal). No direct human writes to prod.
- **dev/qa:** `data_engineers` receive READ + WRITE to support interactive development.

This aligns with the CI/CD execution policy: prod deployments are merge-to-main only; dev/qa
allow workflow_dispatch.

---

## Mock Environment Simplification

- **Single Catalog:** `mock` only. No environment-specific Catalog separation (e.g., `mock_dev`,
  `mock_staging`, `mock_prod`).
- **No environment-differentiated GRANTs:** All groups receive the same grants regardless of
  environment. In production, `data_engineers` would not have WRITE access to prod.
- **Native groups instead of EntraID Sync:** As described above.

This simplification reflects a deliberate scope decision: the mock environment demonstrates
architectural patterns and design decisions — not the full operational complexity of a
multi-environment enterprise deployment. The target architecture is documented in this ADR and
the README.

---

## Consequences

- Adding a new workspace requires two steps: (1) create the Workspace in Terraform (infrastructure
  layer); (2) add the corresponding Workspace assignment grants in the Platform Layer (SQL/Jinja2).
  No new individual grant statements are needed in either step.
- Access control reviews (SOC 2, audit, etc.) are answered from three sources:
  - **What should be (declared intent):** GRANT definitions in the repository (YAML/SQL templates)
  - **What happened (execution evidence):** Databricks system tables (`system.access.audit` and
    related tables) — built-in audit logging that automatically records all GRANT operations
  - **Who is who (identity source):** EntraID group membership (prod) / Databricks-native
    groups (mock)
  - Terraform state is **not** an audit source for grants — grants are no longer Terraform-managed.
- The platform team must maintain a group structure that maps to the desired access topology before
  standing up new workspaces. Group structure changes are CI/CD-driven; membership changes are
  IdP-driven (or CLI-driven in mock).
- Using built-in Databricks system tables as the audit log eliminates the need for a custom audit
  log implementation.

---

## Production Consideration: Catalog/Schema Decommissioning

**Mock environment:** Metastore has `force_destroy = true` (PR [#50](https://github.com/nobhri/azure-dbx-mock-platform/pull/50)).
A successful `terraform destroy` cascade-deletes the Metastore and all managed Catalogs.
Individual Catalog/Schema deletion is not required.

**Production decommissioning options:**

| Approach | Description | Risk | Recommended for |
|----------|-------------|------|-----------------|
| DROP CASCADE | `DROP SCHEMA ... CASCADE` — deletes schema and all contents | Unrecoverable if run against prod accidentally | dev/staging only |
| Soft delete (recommended) | REVOKE all grants + add COMMENT marking schema as deprecated; manual DROP after review period | Data remains; reversible; audit trail in system tables | prod |
| Terraform-managed delete | CREATE in SQL, DELETE in Terraform — asymmetric ownership | Breaks responsibility boundary | Not recommended |

**Recommended procedure (prod):**

```sql
-- Step 1: Revoke access from all groups
REVOKE ALL PRIVILEGES ON SCHEMA `catalog`.`schema` FROM `data_platform_admins`;
REVOKE ALL PRIVILEGES ON SCHEMA `catalog`.`schema` FROM `data_engineers`;
REVOKE ALL PRIVILEGES ON SCHEMA `catalog`.`schema` FROM `data_consumers`;

-- Step 2: Mark as deprecated
COMMENT ON SCHEMA `catalog`.`schema` IS 'DEPRECATED yyyy-mm-dd -- do not use';

-- Step 3: Verify no active usage (query system.access.audit for recent SELECT history)
-- Step 4: After review period (e.g., 30 days), execute manually with approval:
DROP SCHEMA `catalog`.`schema` CASCADE;
```

**Design rationale:**

- Automated DROP CASCADE in CI/CD pipelines is too high-risk for production data
- Soft delete allows recovery if unexpected dependencies are found during the review period
- REVOKE operations fit naturally into the existing GRANT pipeline as its inverse
- Databricks system tables automatically record when access was revoked — no custom logging needed
- The review period surfaces dependencies that were not captured in documentation
