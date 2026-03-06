# ADR-005: Identity & Permission Model — Group-Based Access via EntraID Sync

**Status:** Accepted
**Date:** 2026-02-01

---

## Context

Databricks Unity Catalog supports granting permissions to individual users, service principals, or
groups. In an enterprise environment with multiple workspaces and catalogs, how should access be
structured so that it remains auditable and manageable as the team scales?

---

## Decision

Permissions are assigned to **EntraID Groups only — never to individual users or service principals
(except the platform SP itself)**. All Workspace and Catalog permission grants are managed via
Terraform. No `GRANT` to individual user principals appears anywhere in the platform automation.

EntraID Groups are synced into Databricks via **Native Sync** (not SCIM provisioning).

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

---

## Trade-offs Accepted

- Group management is now a prerequisite: before a new team member can access any Databricks
  resource, the correct EntraID group must exist and be assigned. This is additional setup friction
  for the first deployment.
- Native Sync has a propagation delay: group membership changes in EntraID take some minutes to
  appear in Databricks. This is acceptable for access management (not a real-time requirement).
- Service principal grants (e.g., the CI/CD SP) are an exception to the group-only rule — the SP
  is granted directly as it is not a human user and has no EntraID group membership.

---

## Why Native Sync Over SCIM?

| Dimension              | Native Sync                   | SCIM Provisioning            |
|------------------------|-------------------------------|------------------------------|
| Nested group support   | Yes                           | Limited                      |
| Setup complexity       | Lower (no external SCIM app)  | Higher (requires SCIM config)|
| Sync trigger           | Near-real-time (token issue)  | Configurable polling         |
| Group creation in DBX  | Automatic                     | Requires SCIM PUT            |

Native Sync is preferred because it supports nested groups (which SCIM provisioning handles
inconsistently across IdP versions) and requires no external SCIM application configuration.

---

## Consequences

- Adding a new workspace requires only adding a parameter to Terraform (group-to-workspace
  assignment) — no new individual grant statements.
- Access control reviews (SOC 2, audit, etc.) can be answered by inspecting EntraID group
  membership and Terraform-managed grants — two sources of truth, both auditable.
- The platform team must maintain an EntraID group structure that maps to the desired access
  topology before standing up new workspaces.
