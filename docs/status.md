# Project Status Snapshot

**Last updated:** 2026-03-08
**Update instructions:** Edit this file at the end of each docs PR. Update any issue that was
opened, closed, or changed severity during the session.

---

## Open Issues

| Issue | Severity | Title | Notes |
|-------|----------|-------|-------|
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | MEDIUM | OIDC not configured for pull_request subject | PR CI always fails Azure login. Fix: add `pull_request` federated credential in Entra ID. No code change needed. |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | LOW | Document GRANT CREATE CATALOG prerequisite | Update GETTING_STARTED.md. Runbook fully updated (PR #98): correct CLI commands, SCIM API for member-add, Account Console as primary path. |
| [#84](https://github.com/nobhri/azure-dbx-mock-platform/issues/84) | HIGH | Preflight fix commit not merged into main — old buggy code still active | Fix pushed after PR #79 merged; dangling commit. PR #84 re-applies the fix. |
| [#85](https://github.com/nobhri/azure-dbx-mock-platform/issues/85) | MEDIUM | UC catalog/schema not visible to human user — missing USE CATALOG/USE SCHEMA grants | GRANT step now resilient: warns on missing principals, does not fail. Groups must be created as account-level groups via Account Console or CLI (PR #97). Re-run workload-catalog after group creation. |
| [#82](https://github.com/nobhri/azure-dbx-mock-platform/issues/82) | LOW | Test coverage gap: dynamic metastore import path not exercised in CI | Branch 3 ("Found existing metastore — importing") never triggered. Requires manual `terraform state rm` to test. See session-008 for procedure. |

---

## Pending Human Actions

These require direct human action in Azure, GitHub, or Databricks — cannot be automated via CI/CD.

| Action | Priority | Where |
|--------|----------|-------|
| Add OIDC federated credential for `pull_request` subject | MEDIUM | Entra ID → App Registration → Federated credentials |
| After each destroy/recreate: run post-destroy grants (Step 1 — SP grants) | REQUIRED | Databricks SQL warehouse — see [runbook](runbooks/post-destroy-grants.md) |
| Create account-level groups (data_platform_admins, data_engineers, data_consumers) | ONE-TIME | Databricks Account Console → User Management → Groups (see runbook Step 2) |
| After group creation: re-run workload-catalog to apply deferred GRANTs | REQUIRED | GitHub Actions → workload-catalog → Run workflow |

---

## Recently Closed Issues

| Issue | Title | Closed by |
|-------|-------|-----------|
| [#87](https://github.com/nobhri/azure-dbx-mock-platform/issues/87) | ADR conflict: catalog grants not assignable to Terraform when catalog is Jinja2-managed | ADR-005 updated — Option A: all Metastore-scoped grants moved to Platform Layer (SQL/Jinja2) |
| [#80](https://github.com/nobhri/azure-dbx-mock-platform/issues/80) | workload-dbx apply fails after successful destroy: static import block uses stale METASTORE_ID | PR #81 — dynamic metastore discovery step; METASTORE_ID secret removed |
| [#68](https://github.com/nobhri/azure-dbx-mock-platform/issues/68) | workload-catalog fails when workload-dbx external location not present | PR #78 — preflight check added to workflow; GETTING_STARTED.md updated |
| [#64](https://github.com/nobhri/azure-dbx-mock-platform/issues/64) | METASTORE_ID secret had wrong UUID (account ID copied instead of metastore ID) | PRs #72 #74 #75 — import block restored; correct UUID set; apply succeeded |
| [#62](https://github.com/nobhri/azure-dbx-mock-platform/issues/62) | Metastore state drift (reached region limit) | PR #63 — import block added |
| [#61](https://github.com/nobhri/azure-dbx-mock-platform/issues/61) | bundle deploy missing --var flags → empty base_parameters | PR #65 merged |
| [#52](https://github.com/nobhri/azure-dbx-mock-platform/issues/52) | Add catalog/schema DDL layer via Jinja2 + Asset Bundle | PR #54 merged |
| [#45](https://github.com/nobhri/azure-dbx-mock-platform/issues/45) | inputs.destroy boolean comparison broken | PR #48 merged |
| [#47](https://github.com/nobhri/azure-dbx-mock-platform/issues/47) | inputs.destroy boolean comparison broken (workload-dbx) | PR #49 merged |
| [#26](https://github.com/nobhri/azure-dbx-mock-platform/issues/26) | UC objects orphaned when destroy order wrong | PR #50 — force_destroy = true |
| [#21](https://github.com/nobhri/azure-dbx-mock-platform/issues/21) | SP lacks User Access Administrator role | UAA granted at subscription scope |
| [#19](https://github.com/nobhri/azure-dbx-mock-platform/issues/19) | SP missing CREATE EXTERNAL LOCATION | Grant applied; must redo after destroy |

---

## Open PRs

| PR | Title | Status |
|----|-------|--------|
| [#70](https://github.com/nobhri/azure-dbx-mock-platform/pull/70) | docs: add docs-restructure proposal | Pending human review |
| [#98](https://github.com/nobhri/azure-dbx-mock-platform/pull/98) | docs: fix group setup and member-add procedures in post-destroy-grants runbook | Pending human review |

---

## Architecture State

| Component | State |
|-----------|-------|
| workload-azure | Destroyed (cost-saving) |
| workload-dbx | Destroyed (cost-saving) |
| workload-catalog | Not applied (depends on workload-dbx) |
| guardrails | Deployed |
| tfstate backend | Deployed |
