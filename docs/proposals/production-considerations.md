# Proposal: Production Considerations

**Status:** Superseded — content merged into [`docs/design/platform-layer.md`](../design/platform-layer.md) §Production Simplifications
**Date:** 2026-03-05
**Layer:** Platform / Cross-cutting
**Related ADRs:** ADR-001 (Terraform scope), ADR-005 (group permissions, updated 2026-03-07)

---

## Overview

These items are **not implemented in this mock** but are documented here as known simplifications.
Each represents a gap between the mock design and a production-grade platform that should be
captured in an ADR or production runbook before any real deployment.

---

## 10.1 Single Workspace vs Dedicated Workspace per Environment

**Mock design:** One workspace. Environment isolation is achieved by switching the Asset Bundles
target variable (`dev` / `staging` / `prod`), which maps to different catalog names via the SDLC
lookup function (see `sdlc-catalog-lookup.md`).

**Production reality:** Dedicated workspace per environment (dev / staging / prod). Each workspace
has its own identity boundary, network configuration, and catalog binding. Workspace-level RBAC
and governance are cleanly separated.

**Why single workspace is an intentional simplification:**
- Provisioning and maintaining three workspaces multiplies Azure cost and CI/CD complexity.
- For a portfolio mock, demonstrating the SDLC pattern (catalog switching via Asset Bundles target)
  is sufficient to show the design intent.
- The single-workspace design does not prevent later migration: catalog naming conventions and the
  SDLC lookup function are already environment-aware.

**ADR candidate:** Document the single-workspace trade-off and the migration path to per-environment
workspaces when the platform scales beyond a single team.

---

## 10.2 System Tables for Catalog / Schema Change Tracking

**Platform layer status (updated 2026-03-09):** The Jinja2 catalog/schema management layer is now
live (workload-catalog last successful run: 2026-03-08). System table tracking is actionable now
that the catalog/schema infrastructure exists.

**Current DDL state:** DDL is idempotent (`CREATE IF NOT EXISTS`). Deletions are not detected at
apply time — explicitly accepted in ADR-001 as an MVP trade-off ("DDL `IF NOT EXISTS` is idempotent
but will not detect deletions").

**When system tables become relevant:** Once schemas are being modified over time (column additions,
type changes, object drops), audit-level tracking becomes necessary for:
- Detecting drift between the declared DDL and the actual UC state
- Auditing who changed what and when (compliance, incident response)
- Triggering alerts when unexpected schema changes occur

**Enablement conditions:**
- System tables must be enabled at the account level: `system.access`, `system.information_schema`
- Requires Unity Catalog metastore (already in place as of 2026-03-07)
- Requires a scheduled job or CI/CD step that queries `system.information_schema.columns` and
  compares against the expected schema from the Jinja2 templates

**ADR candidate:** Document drift detection approach (system table query vs Terraform plan vs
application-level assertion) and the enablement prerequisites.

---

## 10.3 Infra / Platform Repo Separation and Cross-Repo Output Passing

**Current state:** Single repository. `workload-azure` and `workload-dbx` run as separate GitHub
Actions workflows in the same repo. Outputs from `workload-azure` (e.g., storage account name,
workspace URL) are available to `workload-dbx` via Terraform remote state stored in the shared
Azure Storage backend.

**Production reality:** Infrastructure (Azure resources) and platform (Databricks configuration,
Unity Catalog) are often owned by different teams and live in separate repositories. Cross-repo
output passing is a non-trivial design problem:

| Mechanism | Trade-offs |
|-----------|-----------|
| Shared Terraform remote state | Both repos must have read access to the same backend; tight coupling at the state layer |
| GitHub Secrets / Variables (manual) | Requires human update after each infra apply; error-prone |
| Cross-repo GitHub Actions triggers with output artifacts | Complex workflow orchestration; artifact lifetime management |
| Published artifact / API endpoint | Most decoupled; highest implementation cost |

**Relationship to ADR-001:** ADR-001 defines the Terraform responsibility boundary (Azure + Metastore
= Terraform, Catalog/Schema = SQL). Repo separation is the organizational consequence of that
boundary: once the boundary is firm, each side can be owned and deployed independently. The output-
passing problem only arises when the repos split.

**Relationship to ADR-005 (updated 2026-03-07):** ADR-005 moved all metastore-scoped GRANTs from
Terraform to the Platform Layer (SQL/SDK). This reinforces the Terraform responsibility boundary
and makes the infra/platform split cleaner — the infra side (Terraform) no longer issues
account-level UC grants.

**ADR candidate:** Document which cross-repo output mechanism to adopt if repos are split, and the
conditions under which a split is warranted (team size, change velocity, security isolation
requirements).

---

## 10.4 Single Service Principal vs Separated SP per Layer

**Current state:** One Service Principal handles all CI/CD operations: Azure resource provisioning
(Terraform), Databricks workspace configuration (Terraform), and Databricks job execution (Asset
Bundles + SQL notebook).

**Production reality:** Least-privilege design separates concerns:

| SP | Scope |
|----|-------|
| Infra SP | Azure RBAC (Contributor on RG, Storage Blob Data Contributor) |
| Platform SP | Databricks workspace admin, Unity Catalog grants |
| Data SP | Job execution, catalog read/write only |

**The trade-off this creates (coupled with 10.3):**
- With a single SP and single repo, Terraform remote state is readable by both the infra and
  platform workflows under the same identity — output passing is free.
- With separated SPs and separate repos, the infra SP's outputs are no longer directly accessible
  to the platform SP. An explicit output-passing mechanism (see 10.3) is required.
- Separating SPs also requires separate federated credential configurations in Entra ID and
  separate GitHub secret sets.

**Relationship to ADR-005:** ADR-005 defines the SP exception rule — the single SP is the metastore
admin and issues all account-level GRANTs. In a separated-SP design, the Platform SP would inherit
this role, and the Data SP would be a separate identity with narrower catalog-level permissions.

**ADR candidate:** Document the single-SP trade-off and the separation design when moving toward
production. Reference the repo-separation ADR candidate in 10.3 — these two decisions are coupled
and should be resolved together.

---

## Dashboard Layer — Out of Scope

Not implemented. When the need arises, the choice between the following should be treated as an
explicit design decision:

| Tool | Fit |
|------|-----|
| AI/BI Dashboards | Self-service, exploratory; individual or team consumption |
| Asset Bundles / Lakeview as code | Org-wide KPIs, cross-team reporting; code review, versioning, and environment-specific deployment required |
| Databricks Apps | Interactive applications; input forms or workflow integration |

An ADR entry covering this trade-off belongs in the README Future Work section or as a standalone
ADR when any dashboard work begins.
