# Project Status Snapshot

**Last updated:** 2026-03-06
**Update instructions:** Edit this file at the end of each docs PR. Update any issue that was
opened, closed, or changed severity during the session.

---

## Open Issues

| Issue | Severity | Title | Notes |
|-------|----------|-------|-------|
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | MEDIUM | OIDC not configured for pull_request subject | PR CI always fails Azure login. Fix: add `pull_request` federated credential in Entra ID. No code change needed. |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | LOW | Document GRANT CREATE CATALOG prerequisite | Update GETTING_STARTED.md and post-destroy-grants runbook. Partially addressed by `docs/runbooks/post-destroy-grants.md`. |
| [#64](https://github.com/nobhri/azure-dbx-mock-platform/issues/64) | HIGH | METASTORE_ID secret not a plain UUID | Fix: remove stale import block from `workload-dbx/main.tf` + add `metastore_id` output (code fix PR pending). Post-apply human action: copy new UUID from CI Apply output and update `METASTORE_ID` GitHub secret. |
| [#68](https://github.com/nobhri/azure-dbx-mock-platform/issues/68) | MEDIUM | workload-catalog fails when workload-dbx external location not present | Infrastructure ordering dependency. `workload-dbx` must complete before `workload-catalog`. Documented in `docs/runbooks/destroy-recreate.md`. |

---

## Pending Human Actions

These require direct human action in Azure, GitHub, or Databricks — cannot be automated via CI/CD.

| Action | Priority | Where |
|--------|----------|-------|
| After `workload-dbx` apply: update `METASTORE_ID` GitHub secret with new UUID from CI Apply output (`metastore_id` output) | HIGH | GitHub → Settings → Secrets |
| Add OIDC federated credential for `pull_request` subject | MEDIUM | Entra ID → App Registration → Federated credentials |
| After each destroy/recreate: run post-destroy grants | REQUIRED | Databricks SQL warehouse — see [runbook](runbooks/post-destroy-grants.md) |

---

## Recently Closed Issues

| Issue | Title | Closed by |
|-------|-------|-----------|
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

---

## Architecture State

| Component | State |
|-----------|-------|
| workload-azure | Destroyed (cost-saving) |
| workload-dbx | Destroyed (cost-saving) |
| workload-catalog | Not applied (depends on workload-dbx) |
| guardrails | Deployed |
| tfstate backend | Deployed |
