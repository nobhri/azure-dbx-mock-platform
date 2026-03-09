# Project Status Snapshot

**Last updated:** 2026-03-09 (session 001 — doc review)
**Update instructions:** Edit this file at the end of each docs PR. Update any issue that was
opened, closed, or changed severity during the session.

---

## Open Issues

| Issue | Severity | Title | Notes |
|-------|----------|-------|-------|
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | MEDIUM | OIDC not configured for pull_request subject | PR CI always fails Azure login. Fix: add `pull_request` federated credential in Entra ID. No code change needed. |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | LOW | Document GRANT CREATE CATALOG prerequisite | Update GETTING_STARTED.md and post-destroy-grants runbook. Partially addressed by `docs/runbooks/post-destroy-grants.md`. |
| [#82](https://github.com/nobhri/azure-dbx-mock-platform/issues/82) | LOW | Test coverage gap: dynamic metastore import path not exercised in CI | Branch 3 ("Found existing metastore — importing") never triggered. Requires manual `terraform state rm` to test. See session-008 for procedure. |
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | LOW | Add tflint step to workload-azure.yaml and workload-dbx.yaml | Enhancement blocked historically by OIDC issue #40. |
| [#105](https://github.com/nobhri/azure-dbx-mock-platform/issues/105) | HIGH | README Current Status and Known Issues stale vs status.md | "In Progress" items are done; Known Issues section diverges from this file. |
| [#106](https://github.com/nobhri/azure-dbx-mock-platform/issues/106) | HIGH | GETTING_STARTED.md prerequisites table has wrong secrets | Missing `ADLS_STORAGE_NAME`; stale `METASTORE_ID` still listed (removed by PR #81). |
| [#107](https://github.com/nobhri/azure-dbx-mock-platform/issues/107) | HIGH | post-destroy-grants.md verification SQL references wrong group name | `databricks-platform-users` should be `data_platform_admins`. |
| [#108](https://github.com/nobhri/azure-dbx-mock-platform/issues/108) | MEDIUM | Extract Production Considerations from README to docs/design/ | README is too long; prod-considerations content belongs in design doc. |
| [#109](https://github.com/nobhri/azure-dbx-mock-platform/issues/109) | MEDIUM | Add Phase 2 roadmap section to README | Project looks "done but incomplete" to external audience; no visible next-step plan. |
| [#110](https://github.com/nobhri/azure-dbx-mock-platform/issues/110) | MEDIUM | Add ADR annotations to README architecture diagram | Layer diagram has no cross-references to ADRs; reader must map manually. |
| [#111](https://github.com/nobhri/azure-dbx-mock-platform/issues/111) | MEDIUM | Improve discoverability — link status.md, add sessions/ README | status.md not linked from README; sessions/ has no explanation for external readers. |
| [#112](https://github.com/nobhri/azure-dbx-mock-platform/issues/112) | LOW | Close stale PR #70 and triage proposed-state proposals | PR #70 open but already implemented in #71; 5 proposals stuck "Proposed" since 2026-03-05. |

---

## Pending Human Actions

These require direct human action in Azure, GitHub, or Databricks — cannot be automated via CI/CD.

| Action | Priority | Where |
|--------|----------|-------|
| Add OIDC federated credential for `pull_request` subject | MEDIUM | Entra ID → App Registration → Federated credentials |
| After each destroy/recreate: run post-destroy grants (Step 1 — SP grants) | REQUIRED | Databricks SQL warehouse — see [runbook](runbooks/post-destroy-grants.md) |
| Close PR #70 (docs-restructure proposal — already implemented in PR #71) | LOW | GitHub — AI agent cannot close PRs per CLAUDE.md |

---

## Recently Closed Issues

| Issue | Title | Closed by |
|-------|-------|-----------|
| [#85](https://github.com/nobhri/azure-dbx-mock-platform/issues/85) | UC catalog/schema not visible to human user — missing USE CATALOG/USE SCHEMA grants | PRs #96 #97 — SCIM group creation + resilient GRANTs; confirmed accessible 2026-03-09 |
| [#93](https://github.com/nobhri/azure-dbx-mock-platform/issues/93) | setup_platform fails: CREATE GROUP is not valid Unity Catalog SQL | PR #94 — replaced SQL with SDK group creation |
| [#91](https://github.com/nobhri/azure-dbx-mock-platform/issues/91) | workload-catalog fails: ModuleNotFoundError: No module named 'yaml' on DBR 14.3.x | PR #92 — added PyYAML to cluster setup job |
| [#87](https://github.com/nobhri/azure-dbx-mock-platform/issues/87) | ADR conflict: catalog grants not assignable to Terraform when catalog is Jinja2-managed | PR #88 — ADR-005 updated; all metastore-scoped grants moved to Platform Layer |
| [#84](https://github.com/nobhri/azure-dbx-mock-platform/issues/84) | Preflight fix commit not merged into main — old buggy code still active | PR #86 — fix re-applied |
| [#80](https://github.com/nobhri/azure-dbx-mock-platform/issues/80) | workload-dbx apply fails after successful destroy: static import block uses stale METASTORE_ID | PR #81 — dynamic metastore discovery step; METASTORE_ID secret removed |
| [#68](https://github.com/nobhri/azure-dbx-mock-platform/issues/68) | workload-catalog fails when workload-dbx external location not present | PR #79 — preflight check added to workflow; GETTING_STARTED.md updated |
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

---

## Architecture State

| Component | State |
|-----------|-------|
| workload-azure | Applied (active as of 2026-03-07) |
| workload-dbx | Applied (active as of 2026-03-07) — metastore, external location, workspace |
| workload-catalog | Applied — catalog/schema/groups/grants confirmed accessible 2026-03-09 |
| guardrails | Deployed |
| tfstate backend | Deployed |

**Platform layer status:** Complete. Catalog and schema are created and accessible to human user. Account-level groups created and GRANTs applied successfully (workload-catalog last run: 2026-03-08, success).
