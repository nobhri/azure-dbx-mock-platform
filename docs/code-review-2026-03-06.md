# Code Review — 2026-03-06

**Scope:** Activity audit — all GitHub issues and PRs from 2026-03-05 to 2026-03-06
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Builds on:** [code-review-2026-03-05.md](./code-review-2026-03-05.md)
**Status:** MVP phase

---

## Activity Summary (2026-03-05 → 2026-03-06)

### PRs Merged

| PR | Title | Closes |
|----|-------|--------|
| [#54](https://github.com/nobhri/azure-dbx-mock-platform/pull/54) | feat: add catalog/schema DDL layer via Jinja2 + Asset Bundle | #52 |
| [#57](https://github.com/nobhri/azure-dbx-mock-platform/pull/57) | fix: remove unsupported workspace.host interpolation in databricks.yml | — |
| [#58](https://github.com/nobhri/azure-dbx-mock-platform/pull/58) | fix: add data_security_mode SINGLE_USER to enable Unity Catalog on job cluster | — |
| [#59](https://github.com/nobhri/azure-dbx-mock-platform/pull/59) | fix: strip SQL comment lines before splitting to preserve CREATE CATALOG | — |
| [#60](https://github.com/nobhri/azure-dbx-mock-platform/pull/60) | fix: pass MANAGED LOCATION to CREATE CATALOG to bypass missing metastore storage root | — |
| [#63](https://github.com/nobhri/azure-dbx-mock-platform/pull/63) | fix: import existing metastore into state to resolve state drift | #62 |

### Issues Opened (this period)

| Issue | Title | Status |
|-------|-------|--------|
| [#62](https://github.com/nobhri/azure-dbx-mock-platform/issues/62) | Metastore state drift causes apply to fail with "reached limit" | Closed by PR #63 |
| [#64](https://github.com/nobhri/azure-dbx-mock-platform/issues/64) | METASTORE_ID secret is not a plain UUID — import block fails | **Open** — pending human action |
| [#66](https://github.com/nobhri/azure-dbx-mock-platform/issues/66) | docs: add code review 2026-03-06 | Closed by this PR |

### Issues Closed (this period)

| Issue | Title | Closed by |
|-------|-------|-----------|
| [#52](https://github.com/nobhri/azure-dbx-mock-platform/issues/52) | Add catalog/schema DDL layer via Jinja2 + Asset Bundle | PR #54 |
| [#62](https://github.com/nobhri/azure-dbx-mock-platform/issues/62) | Metastore state drift | PR #63 |

---

## Investigation: workload-dbx Apply Failure Chain

### Background

After the full destroy/recreate cycle on 2026-03-05, `workload-dbx` apply consistently failed. The metastore was visible and healthy in the Databricks Account Console, so infrastructure was intact.

### Phase 1 — Root cause: Terraform state drift (issue #62)

**Error observed (runs 22723161972, 22723684164, 22723790096):**

```
Error: cannot create metastore: This account with id *** has reached the limit
for metastores in region japaneast.
```

**Root cause:** The metastore existed in the Databricks account but was absent from Terraform state. On every apply Terraform planned to `create` the resource, which the API rejected (one metastore per region limit).

**Failure timeline:**

| Run | Time (UTC) | Trigger | Result | Explanation |
|-----|-----------|---------|--------|-------------|
| 22723161972 | 14:44 | apply | FAIL | State empty, tries CREATE → rejected |
| 22723491665 | 14:52 | destroy | OK | Nothing in state → "0 destroyed" |
| 22723684164 | 14:56 | apply | FAIL | Same state drift |
| 22723790096 | 14:59 | apply | FAIL | Same state drift |

The destroy at 14:52 succeeded only because there was nothing in state to destroy — confirming the drift.

**Fix (PR #63):** Added a Terraform `import` block using `var.metastore_id` so the existing metastore is reconciled into state before apply:

```hcl
import {
  provider = databricks.account
  to       = databricks_metastore.this
  id       = var.metastore_id
}
```

### Phase 2 — Secondary failure: METASTORE_ID is not a plain UUID (issue #64)

**Error observed after PR #63 merged (run 22744238085):**

```
Error: cannot read metastore: UUID string too large
```

**Root cause:** The Terraform `import` block passes `var.metastore_id` (sourced from the `METASTORE_ID` GitHub Actions secret) as the Databricks metastore ID. The Databricks provider expects a 36-character UUID. The secret contains a longer value — likely a full ABFSS path, resource ID, or composite string rather than the raw UUID.

The variable was originally designed as a **storage root path suffix** only:

```hcl
storage_root = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/${var.metastore_id}"
```

Using the same value as an import ID exposed that the secret's content does not conform to UUID format.

**Status:** Open. See [issue #64](https://github.com/nobhri/azure-dbx-mock-platform/issues/64) for the step-by-step remediation plan.

#### Remediation options

**Option A — Fix the METASTORE_ID secret**

1. Human admin: look up the actual metastore UUID in Databricks Account Console → Unity Catalog → Metastores
2. Human admin: update `METASTORE_ID` secret to the raw UUID (36 chars, `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
3. Note: this also changes the `storage_root` suffix — confirm the existing path in the console matches `abfss://uc-root@<storage>.dfs.core.windows.net/<UUID>` before updating
4. No code change needed — re-run the workflow

**Option B — Separate secret for the UUID**

1. Human admin: look up the metastore UUID in the Account Console
2. Human admin: add a new GitHub Actions secret `DATABRICKS_METASTORE_UUID` with just the UUID
3. AI agent: add `variable "databricks_metastore_uuid"` to `variables.tf`, update the import block, pass the new var in the workflow

---

## Catalog DDL Layer Fix Chain (PRs #54, #57–#60)

PR #54 (catalog/schema DDL layer) landed on 2026-03-05. Four sequential hotfixes followed on the same day as the CI revealed successive runtime failures.

### Fix chain summary

| PR | Error fixed | Root cause |
|----|-------------|------------|
| **#57** | `parse "https://${DATABRICKS_HOST}": invalid character "{"` | Asset Bundle does not support shell variable interpolation (`${...}`) in authentication fields. Removed `workspace.host: ${DATABRICKS_HOST}` — the CLI reads env vars directly. |
| **#58** | `[REQUIRES_SINGLE_PART_NAMESPACE] spark_catalog requires a single-part namespace` | Cluster defaulted to legacy Hive metastore (no `data_security_mode`). Added `data_security_mode: SINGLE_USER` to enable Unity Catalog mode on the job cluster. |
| **#59** | `NO_SUCH_CATALOG_EXCEPTION: mock_prod` | SQL comment stripping used `startswith("--")` on post-split chunks. The first chunk (comments + `CREATE CATALOG`) was entirely dropped because it started with `--`. Fixed by stripping comment lines before splitting on `;`. |
| **#60** | `INVALID_STATE: Metastore storage root URL does not exist` | `CREATE CATALOG` fell back to the metastore storage root, which does not exist as a live ADLS path at runtime. Fixed by passing explicit `MANAGED LOCATION` in `CREATE CATALOG` using the storage account from workload-azure outputs. |

### Lessons learned from the fix chain

1. **Test incrementally.** Each fix uncovered the next issue. Integration tests or a local DABs dry-run would surface these sequentially without needing four CI round-trips.
2. **Asset Bundle auth fields behave differently from regular bundle variables.** Do not use `${SHELL_VAR}` for `workspace.host` or `workspace.token` — set these exclusively via environment variables.
3. **Job cluster must explicitly opt into Unity Catalog.** `data_security_mode: SINGLE_USER` (or `USER_ISOLATION`) is required; the default is legacy mode.
4. **SQL comment stripping must happen before splitting, not after.** Filtering on chunks post-split is fragile when comments and statements share a chunk.
5. **Metastore storage root may not exist as a live path.** Even if `storage_root` is set on the metastore Terraform resource, the underlying ADLS path is not guaranteed to be provisioned. Using `MANAGED LOCATION` in `CREATE CATALOG` makes the catalog path explicit and independent of the metastore root.

---

## Issue Status Snapshot (current as of 2026-03-06)

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | Add tflint to CI | LOW | **Open** — PR #36 blocked by issue #40 |
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | OIDC not configured for `pull_request` subject | MEDIUM | **Open** — Entra ID federated credential needed |
| [#53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) | Document GRANT CREATE CATALOG prerequisite for SP | LOW | **Open** |
| [#64](https://github.com/nobhri/azure-dbx-mock-platform/issues/64) | METASTORE_ID secret not a plain UUID | HIGH | **Open** — pending human action (blocks every apply) |
| [#61](https://github.com/nobhri/azure-dbx-mock-platform/issues/61) | bundle deploy missing --var flags → empty base_parameters | HIGH | **Open** — PR #65 pending merge |
| [#68](https://github.com/nobhri/azure-dbx-mock-platform/issues/68) | workload-catalog fails when workload-dbx external location missing | MEDIUM | **Open** |

All other previously tracked issues are **Closed**.

---

## workload-catalog Fix Chain (2026-03-06 session)

### Context

After the initial five-PR fix chain (PRs #57–#60) that stabilised the catalog DDL layer, two further issues were discovered when investigating the remaining CI failure.

### Issue #61 — `bundle deploy` missing `--var` flags (PR #65)

**Error observed (run 22725571485 — 2026-03-05):**

```
External Location 'abfss://@.dfs.core.windows.net/catalogs/mock_prod' does not exist.
```

**Root cause:** Both `uc_root_container` and `storage_account_name` were empty strings in the ABFSS URL — making it structurally invalid (no container, no account). The `bundle deploy` step ran without `--var` for these variables, so the deployed job stored empty `base_parameters` (the default `""` from `databricks.yml`). `bundle run --var` resolves bundle-level variables, but the `run-now` API call uses the stored job `base_parameters` from the deployed job definition, not CLI flags passed to `run`.

**Fix (PR #65):** Pass `--var storage_account_name=...` and `--var uc_root_container=...` to `bundle deploy` so the job is deployed with the correct `base_parameters` before `bundle run` triggers it. Also restored the `STORAGE_ACCOUNT_NAME` and `UC_ROOT_CONTAINER` output captures in the `azout` step that were dropped during the cherry-pick merge.

```yaml
# Before
- name: Bundle deploy
  run: databricks bundle deploy --target ${{ steps.target.outputs.TARGET }}

# After
- name: Bundle deploy
  run: |
    databricks bundle deploy --target ${{ steps.target.outputs.TARGET }} \
      --var "storage_account_name=${{ steps.azout.outputs.STORAGE_ACCOUNT_NAME }}" \
      --var "uc_root_container=${{ steps.azout.outputs.UC_ROOT_CONTAINER }}"
```

### Issue #68 — `EXTERNAL_LOCATION_DOES_NOT_EXIST` (infrastructure ordering prerequisite)

**Error observed (run 22744669023 — 2026-03-06), after PR #65 fix:**

```
External Location 'abfss://uc-root@stdata***.dfs.core.windows.net/catalogs/mock_dev' does not exist.
```

**Progress:** The ABFSS URL is now well-formed (issue #61 fix working). The new error is a different problem entirely.

**Root cause:** `CREATE CATALOG ... MANAGED LOCATION` requires a UC External Location covering the requested path. That external location (`uc-root-location`) is created by `workload-dbx` Terraform (`databricks_external_location.uc_root`). If `workload-dbx` has not been applied, the external location does not exist in UC.

**Deployment ordering dependency:**

```
1. workload-azure apply  → ADLS storage account + container
2. workload-dbx apply    → UC metastore + storage credential + external location
3. workload-catalog run  → CREATE CATALOG (requires external location to exist)
```

`workload-catalog` has no guard to detect that step 2 is missing. The workflow proceeds, the notebook fails. This is not a code bug — it is a missing infrastructure prerequisite check.

**Status:** Open (#68). See issue for remediation options (preflight check vs documentation only).

---

## Lessons learned (2026-03-06 additions)

6. **`bundle deploy --var` and `bundle run --var` serve different purposes.** `--var` on `bundle run` resolves bundle variables for any bundle-level logic, but the job's `base_parameters` are stored at deploy time. Always pass `--var` to `bundle deploy` when variables must reach a notebook via `base_parameters`.
7. **`workload-catalog` has an undocumented infrastructure prerequisite.** The external location (`databricks_external_location.uc_root`) must exist in UC before the catalog DDL notebook can run. This requires `workload-dbx` to have been applied. Add this to the destroy/recreate checklist.

---

## Recommendations

### Fix now (blocks CI)

1. **Resolve issue #64** — `workload-dbx` apply fails on every run until this is fixed. Human admin must verify the metastore UUID in the Account Console and either correct `METASTORE_ID` or add a separate `DATABRICKS_METASTORE_UUID` secret. See issue #64 for the full step-by-step plan.
2. **Merge PR #65** — fixes empty base_parameters in `bundle deploy` (issue #61).

### Fix soon

3. **Close issue #53** — Add `GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';` to the destroy/recreate procedure in GETTING_STARTED.md alongside the existing `GRANT CREATE EXTERNAL LOCATION` step.
4. **Document issue #68** — Add `workload-dbx` apply as an explicit prerequisite before running `workload-catalog`. Update the destroy/recreate procedure checklist.
5. **Add OIDC federated credential for `pull_request` subject** (issue #40) — unblocks PR CI (`terraform plan` on PRs) and unblocks PR #36 (tflint).

### Observe

6. **`METASTORE_ID` dual-use is a code smell.** The same secret serves as a storage root path suffix and (now also) as the Terraform import ID. These two concerns should be separated — a dedicated `DATABRICKS_METASTORE_UUID` secret would make the import unambiguous and decouple it from the storage path naming convention.
7. **Manual GRANT steps after recreate** — both `GRANT CREATE EXTERNAL LOCATION` and `GRANT CREATE CATALOG` must be re-applied after each destroy+recreate. Consider adding a reference SQL file under `platform/` (e.g., `platform/sql/post_recreate_grants.sql`) that the metastore admin can run as a checklist.

---

*Generated by Claude Code — claude-sonnet-4-6*
