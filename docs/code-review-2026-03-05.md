# Code Review — 2026-03-05

**Scope:** Activity audit — all GitHub issues and PRs from 2026-03-03 to 2026-03-05
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Builds on:** [code-review-2026-03-04.md](./code-review-2026-03-04.md)
**Status:** MVP phase

---

## Activity Summary (2026-03-03 → 2026-03-05)

### PRs Merged

| PR | Title | Closes |
|----|-------|--------|
| [#44](https://github.com/nobhri/azure-dbx-mock-platform/pull/44) | fix: make BUDGET_END dynamic (issue #41) | #41 |
| [#46](https://github.com/nobhri/azure-dbx-mock-platform/pull/46) | docs: add Finding 4 — inputs.destroy boolean comparison bug | — |
| [#48](https://github.com/nobhri/azure-dbx-mock-platform/pull/48) | fix: inputs.destroy boolean comparison in workload-azure (#45) | #45 |
| [#49](https://github.com/nobhri/azure-dbx-mock-platform/pull/49) | fix: inputs.destroy boolean comparison in workload-dbx (#47) | #47 |
| [#50](https://github.com/nobhri/azure-dbx-mock-platform/pull/50) | fix: add force_destroy to metastore to unblock CI destroy | #26 |
| [#51](https://github.com/nobhri/azure-dbx-mock-platform/pull/51) | docs: add code review 2026-03-04 | — |

### PRs Open

| PR | Title | Status |
|----|-------|--------|
| [#36](https://github.com/nobhri/azure-dbx-mock-platform/pull/36) | feat: add tflint step to workload-azure and workload-dbx CI (#11) | Open — blocked by issue #40 (OIDC pull_request) |
| [#54](https://github.com/nobhri/azure-dbx-mock-platform/pull/54) | feat: add catalog/schema DDL layer via Jinja2 + Asset Bundle | Open — closes #52; prerequisite #53 must be documented |

### Issues Closed (this period)

| Issue | Title | Closed by |
|-------|-------|-----------|
| [#26](https://github.com/nobhri/azure-dbx-mock-platform/issues/26) | UC objects orphaned when workload-azure destroyed before workload-dbx | PR #50 (`force_destroy = true`) |
| [#39](https://github.com/nobhri/azure-dbx-mock-platform/issues/39) | `ADLS_STORAGE_NAME` secret not set — workload-azure broken | Manual secret population |
| [#41](https://github.com/nobhri/azure-dbx-mock-platform/issues/41) | guardrails `BUDGET_END` expired | PR #44 (dynamic BUDGET_END) |
| [#45](https://github.com/nobhri/azure-dbx-mock-platform/issues/45) | `inputs.destroy` boolean comparison broken (workload-azure) | PR #48 |
| [#47](https://github.com/nobhri/azure-dbx-mock-platform/issues/47) | `inputs.destroy` boolean comparison broken (workload-dbx) | PR #49 |

### Issues Opened (this period)

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#52](https://github.com/nobhri/azure-dbx-mock-platform/issues/52) | feat: Add catalog/schema DDL layer via Jinja2 + Asset Bundle | — | **Open** — PR #54 |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | docs: Document GRANT CREATE CATALOG prerequisite for SP | LOW | **Open** |
| [#55](https://github.com/nobhri/azure-dbx-mock-platform/issues/55) | docs: sync known issues and docs with recent GitHub activity (2026-03-05) | — | **Open** (this task) |

---

## Correction: Stale Status in Previous Review (2026-03-04)

The 2026-03-04 issue snapshot listed issues #39 and #41 as **Open**. Both had already been closed before that review was written:

| Issue | Closed at | Closed by |
|-------|-----------|-----------|
| #39 (`ADLS_STORAGE_NAME`) | 2026-03-03T12:06:18Z | Manual secret population (no PR) |
| #41 (BUDGET_END expired) | 2026-03-03T15:06:08Z | PR #44 merged |

These were closed during the same code-review-2026-03-03 batch and the status was not propagated to the subsequent review.

---

## Notable Fix — PR #54: Catalog/Schema DDL Layer

PR #54 implements the catalog/schema management layer described in ADR-001. This is a significant milestone — it completes the platform layer separation:

| Layer | Tool | PR |
|-------|------|----|
| Azure infra | Terraform | pre-existing |
| Databricks Account (metastore, workspace, UC credential) | Terraform | pre-existing |
| Catalog / Schema DDL | Jinja2 + Python Notebook + Asset Bundle | **PR #54** |

### Files added

- `platform/ddl/catalog_schema.sql.j2` — Jinja2 SQL template; idempotent `IF NOT EXISTS` DDL for catalogs `mock_dev`, `mock_staging`, `mock_prod` with `bronze`/`silver`/`gold` schemas
- `platform/notebooks/00_setup_catalog_schema.py` — Databricks notebook; renders template at runtime, executes via `spark.sql()`
- `platform/databricks.yml` — Asset Bundle config; `dev`/`staging` targets use `mode: development`; `prod` uses `mode: production`; single-node `Standard_DS3_v2` cluster
- `.github/workflows/workload-catalog.yaml` — CI/CD; push to `main` with `platform/**` changes → prod; `workflow_dispatch` with `target` choice → dev or staging

### Design observations

- No `pull_request` trigger — intentional, consistent with other workflows (avoids OIDC issue #40)
- Idempotent by design — `IF NOT EXISTS` throughout; safe to re-run
- No GRANTs, no DROPs — DDL only (correct scope for the platform layer)
- Runtime path resolution in notebook — no hardcoded paths (correct pattern)

### Prerequisite (issue #53)

Before PR #54 can be used after a destroy/recreate cycle, the metastore admin must run:

```sql
GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';
```

This follows the same pattern as the existing `GRANT CREATE EXTERNAL LOCATION` requirement (issue #19). Both must be re-applied after each full destroy + recreate of `workload-dbx`.

---

## Issue Status Snapshot (current as of 2026-03-05)

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | Add tflint to CI | LOW | **Open** — PR #36 ready, blocked by issue #40 |
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | OIDC not configured for `pull_request` subject | MEDIUM | **Open** — Entra ID federated credential needed |
| [#52](https://github.com/nobhri/azure-dbx-mock-platform/issues/52) | Add catalog/schema DDL layer | — | **Open** — PR #54 in review |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | Document GRANT CREATE CATALOG prerequisite | LOW | **Open** |

All other previously tracked issues are **Closed**.

---

## Recommendations

### Merge / close now

1. **Merge PR #54** — completes the ADR-001 platform layer; no blocking issues; PR #54 is clean
2. **Close issue #53 after updating destroy/recreate docs** — add `GRANT CREATE CATALOG` step to GETTING_STARTED.md alongside the existing GRANT CREATE EXTERNAL LOCATION step

### Fix soon

3. **Add OIDC federated credential for `pull_request` subject** (issue #40) — unblocks PR CI (`terraform plan` on PRs) and unblocks PR #36 (tflint)

### Observe

4. **`-upgrade` flag in `terraform init`** (workload-dbx.yaml) — still present; should be removed and used only when explicitly bumping provider versions (carry-over from prior review)
5. **Manual GRANT steps after recreate** — both `GRANT CREATE EXTERNAL LOCATION` and `GRANT CREATE CATALOG` must be re-applied after each destroy+recreate. Consider adding a Databricks notebook or SQL file under `platform/` that contains both grants as a reference for the metastore admin (non-automated, but reduces human error).

---

*Generated by Claude Code — claude-sonnet-4-6*
