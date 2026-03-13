# Project Status Snapshot

**Last updated:** 2026-03-13 (session 2026-03-13-001 — README and status.md cleanup)
**Update instructions:** Edit this file at the end of each docs PR. Update any issue that was
opened, closed, or changed severity during the session.

---

## Open Issues

| Issue | Severity | Title | Notes |
|-------|----------|-------|-------|
| [#82](https://github.com/nobhri/azure-dbx-mock-platform/issues/82) | LOW | Test coverage gap: dynamic metastore import path not exercised in CI | Branch 3 ("Found existing metastore — importing") never triggered. Requires manual `terraform state rm` to test. See session-008 for procedure. |
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | LOW | Add tflint step to workload-azure.yaml and workload-dbx.yaml | Enhancement; tflint added to workload-azure and workload-dbx by PR #159, but further refinement possible. |
| [#163](https://github.com/nobhri/azure-dbx-mock-platform/issues/163) | LOW | Verify NAT Gateway and Serverless behavior after March 31 VNet default change | Azure defaults new VNets to private (no outbound internet) as of 2026-03-31. Verify after first post-March-31 destroy→recreate cycle. |

---

## Pending Human Actions

These require direct human action in Azure, GitHub, or Databricks — cannot be automated via CI/CD.

| Action | Priority | Where |
|--------|----------|-------|
| After each destroy/recreate: run post-destroy grants (Step 1 — SP grants) | REQUIRED | Databricks SQL warehouse — see [runbook](runbooks/post-destroy-grants.md) |

---

## Recently Closed Issues

| Issue | Title | Closed by |
|-------|-------|-----------|
| [#162](https://github.com/nobhri/azure-dbx-mock-platform/issues/162) | Add orchestrator workflows for cost-optimized deploy and destroy sequences | PR #165 — merged 2026-03-12 |
| [#155](https://github.com/nobhri/azure-dbx-mock-platform/issues/155) | etl: remove DROP TABLE IF EXISTS migration guard from gold view DDL | PR #156 — merged 2026-03-12 |
| [#144](https://github.com/nobhri/azure-dbx-mock-platform/issues/144) | Pipeline: add bronze schema validation at read time | PR #156 — merged 2026-03-12 |
| [#143](https://github.com/nobhri/azure-dbx-mock-platform/issues/143) | CI: enable pytest-cov coverage reporting | PR #156 — merged 2026-03-12 |
| [#142](https://github.com/nobhri/azure-dbx-mock-platform/issues/142) | CI: add wheel build step to test-unit.yaml | PR #157 — merged 2026-03-12 |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | Document GRANT CREATE CATALOG prerequisite for SP | PR #158 — GETTING_STARTED.md and post-destroy-grants runbook updated; merged 2026-03-12 |
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | OIDC not configured for pull_request subject | PR #159 — tflint + OIDC PR runbook added; PR #160 — GETTING_STARTED.md updated; merged 2026-03-12 |
| [#126](https://github.com/nobhri/azure-dbx-mock-platform/issues/126) | Write ADR-006 (overwrite-only) and ADR-007 (wheel packaging) | PR #161 — merged 2026-03-12 |
| [#141](https://github.com/nobhri/azure-dbx-mock-platform/issues/141) | Gold layer: use view instead of table for daily_sales_by_region | PR #154 — merged 2026-03-10; DROP guard removed in PR #156 |
| [#151](https://github.com/nobhri/azure-dbx-mock-platform/issues/151) | CLAUDE.md: add Common Mistakes section | PR #153 — merged 2026-03-11 |
| [#150](https://github.com/nobhri/azure-dbx-mock-platform/issues/150) | MEMORY.md: remove duplicate open issues table | PR #153 — merged 2026-03-11 |
| [#149](https://github.com/nobhri/azure-dbx-mock-platform/issues/149) | Move Session File Naming rules from CLAUDE.md to docs/sessions/README.md | PR #153 — merged 2026-03-11 |
| [#148](https://github.com/nobhri/azure-dbx-mock-platform/issues/148) | Fix duplicate session NNN numbering on 2026-03-10 | PR #153 — merged 2026-03-11 |
| [#147](https://github.com/nobhri/azure-dbx-mock-platform/issues/147) | Standardize session file template in docs/sessions/README.md | PR #153 — merged 2026-03-11 |
| [#146](https://github.com/nobhri/azure-dbx-mock-platform/issues/146) | CLAUDE.md: add Session Start / End checklists | PR #153 — merged 2026-03-11 |
| [#112](https://github.com/nobhri/azure-dbx-mock-platform/issues/112) | Triage proposed-state proposals | PR #153 — merged 2026-03-10 |
| [#111](https://github.com/nobhri/azure-dbx-mock-platform/issues/111) | Improve discoverability — link status.md, add sessions/ README | PR #153 — merged 2026-03-10 |
| [#110](https://github.com/nobhri/azure-dbx-mock-platform/issues/110) | Add ADR annotations to README architecture diagram | PR #153 — merged 2026-03-10 |
| [#109](https://github.com/nobhri/azure-dbx-mock-platform/issues/109) | Add Phase 2 roadmap section to README | PR #153 — merged 2026-03-10 |
| [#108](https://github.com/nobhri/azure-dbx-mock-platform/issues/108) | Extract Production Considerations from README to docs/design/ | PR #153 — merged 2026-03-10 |
| [#107](https://github.com/nobhri/azure-dbx-mock-platform/issues/107) | post-destroy-grants.md verification SQL references wrong group name | PR #153 — merged 2026-03-10 |
| [#106](https://github.com/nobhri/azure-dbx-mock-platform/issues/106) | GETTING_STARTED.md prerequisites table has wrong secrets | PR #153 — merged 2026-03-10 |
| [#105](https://github.com/nobhri/azure-dbx-mock-platform/issues/105) | README Current Status and Known Issues stale vs status.md | PR #153 — merged 2026-03-10 |
| [#131](https://github.com/nobhri/azure-dbx-mock-platform/issues/131) | workload-etl workflow failing — notebook/whl paths wrong, wrong schema names, wrong CI job | PRs #133 #134 #135 #136 #138 — all path and schema fixes + use etl-e2e-test in CI; confirmed success 2026-03-10 |
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

None.

---

## Architecture State

| Component | State |
|-----------|-------|
| workload-azure | Applied (active as of 2026-03-07) |
| workload-dbx | Applied (active as of 2026-03-07) — metastore, external location, workspace |
| workload-catalog | Applied — catalog/schema/groups/grants confirmed accessible 2026-03-09 |
| workload-etl | Deployed — etl-e2e-test CI passing 2026-03-10; bronze/silver/gold tables confirmed in workspace |
| guardrails | Deployed |
| tfstate backend | Deployed |

**Platform layer status:** Complete. Catalog and schema are created and accessible to human user. Account-level groups created and GRANTs applied successfully (workload-catalog last run: 2026-03-08, success).

**ETL layer status:** Active. `workload-etl` CI passing as of 2026-03-10 (run 22888609919). Bronze/silver/gold tables confirmed in workspace. `etl-pipeline` (production) also manually triggered and verified by human on 2026-03-10.
