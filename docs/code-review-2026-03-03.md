# Code Review — 2026-03-03

**Scope:** Full codebase re-review — all Terraform, GitHub Actions, Taskfile, docs, and .gitignore (~2,400 lines)
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Builds on:** [code-review-2026-03-02.md](./code-review-2026-03-02.md)
**Status:** MVP phase — second update this date (post-PR-batch)

---

## Changes Since Previous Review (PR #29 baseline)

Many issues were closed in a batch of PRs (#30–#38) after the initial 2026-03-03 code review was written. This update reflects the current state of the repository and three new findings from GitHub Actions run analysis.

| Item | Change |
|------|--------|
| Issue #7 — Hardcoded ADLS name | **Closed** — PR #33 moved to `secrets.ADLS_STORAGE_NAME`; **but secret not populated → regression** |
| Issue #9 — No comment on commented-out block | **Closed** — PR #34 added inline comment |
| Issue #10 — SCHEMAS_JSON escaping | **Closed** — PR #32 fixed escaping |
| Issue #12 — terraform.tfstate in repo root | **Closed** — PR #35 added docs/warning |
| Issue #19 — SP missing CREATE EXTERNAL LOCATION | **Closed** — grant re-applied; documented as per-cycle manual step |
| Issue #26 — UC objects orphaned on wrong destroy order | **Closed** — PR #31 added documentation; orphan persists in live environment, must be cleared manually |
| Issue #28 — `inputs.destroy` comparison style inconsistency | **Closed** — PR #30 standardised to explicit string |

---

## New Findings

### Finding 1 — `ADLS_STORAGE_NAME` secret not set (HIGH)

**Runs:** [22606582325](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22606582325), [22606636664](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22606636664)
**Triggered:** workflow_dispatch on main, 2026-03-03T03:13–03:15Z

PR #33 replaced the hardcoded `ADLS_NAME: stdataabcdedata` with `${{ secrets.ADLS_STORAGE_NAME }}`. The secret was never added to GitHub repository secrets, so `ADLS_NAME` resolves to an empty string at runtime.

```
Error: name ("") can only consist of lowercase letters and numbers,
       and must be between 3 and 24 characters long
  with azurerm_storage_account.data, on main.tf line 9
```

Both post-PR-#33 workload-azure runs fail at `Terraform Apply (main)`. The fix for issue #7 is incomplete — the secret must be populated in GitHub → Settings → Secrets → Actions.

**Fix:** Add secret `ADLS_STORAGE_NAME` = storage account name to GitHub repository secrets.

→ Filed as new issue.

---

### Finding 2 — OIDC not configured for `pull_request` subject (MEDIUM)

**Runs:** [22604751488](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22604751488) (workload-azure), [22604750297](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22604750297) (workload-dbx)
**Triggered:** pull_request event on `worktree-feature/issue-11-tflint` branch

```
AADSTS700213: No matching federated identity record found for
presented assertion subject 'repo:nobhri/azure-dbx-mock-platform:pull_request'
```

The Entra ID app registration's federated credentials only accept tokens for `refs/heads/main` (push) and `workflow_dispatch`. GitHub Actions OIDC tokens for `pull_request` events carry the subject `repo:<owner>/<repo>:pull_request`, which is not in the allowed list. As a result, **every PR that touches `infra/workload-azure/**` or `infra/workload-dbx/**` will fail Azure login and cannot run `terraform plan`**.

This means PR-time plan preview is non-functional — a significant gap in the review workflow.

**Fix options:**
- Add a federated credential for subject `repo:nobhri/azure-dbx-mock-platform:pull_request` in Entra ID app registration (preferred — minimal blast radius)
- Or scope to `ref:refs/pull/*` using a wildcard subject (check Entra ID support)

→ Filed as new issue.

---

### Finding 3 — guardrails `BUDGET_END` expired (LOW)

**Run:** [22581502011](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22581502011)
**Triggered:** workflow_dispatch, 2026-03-02T14:55Z

```
Error: creating Scoped Budget: unexpected status 400 (400 Bad Request)
  End date should be greater than the start date.
```

`guardrails.yaml` hardcodes `BUDGET_END: "2026-01-01T00:00:00Z"`, which is now in the past. The dynamic override only rewrites `BUDGET_START` (current month), leaving `BUDGET_END` stale. Azure rejects budget creation when `end < start`.

**Fix:** Update `BUDGET_END` in `guardrails.yaml` to a future date (e.g., `2027-01-01T00:00:00Z`) and consider making it dynamic like `BUDGET_START`.

→ Filed as new issue.

---

## Ongoing Finding — workload-dbx orphaned credential (issue #26 not operationally resolved)

**Run:** [22606426819](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22606426819)
**Triggered:** push to main (merge of PR #34), 2026-03-03T03:06Z

```
Error: cannot create storage credential:
       Storage Credential 'uc-mi-credential' already exists
```

Issue #26 was closed as "documented" — PR #31 added recovery steps to docs. However, the orphaned `uc-mi-credential` was never actually deleted from the Databricks account, so `workload-dbx` continues to fail on every run. The environment is currently broken.

**Required manual steps (before next workload-dbx apply):**
1. Databricks Account Console → Unity Catalog → External Locations → delete `uc-root-location`
2. Databricks Account Console → Unity Catalog → Storage Credentials → delete `uc-mi-credential`
3. Re-run workload-dbx apply
4. Re-grant `CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>'`

This is a live environment blocker. Consider reopening issue #26 to track operational recovery.

---

## Issue Status Snapshot (current)

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | Add tflint to CI | LOW | **Open** — PR attempted but blocked by OIDC issue |
| New | `ADLS_STORAGE_NAME` secret not set — workload-azure broken | HIGH | **Open** — filed today |
| New | OIDC not configured for `pull_request` subject | MEDIUM | **Open** — filed today |
| New | guardrails `BUDGET_END` expired | LOW | **Open** — filed today |

**All other previously tracked issues are now closed.**

---

## Regressions on Previously Resolved Items

| Item | Status |
|------|--------|
| Issue #7 — ADLS hardcoded | ⚠️ **Regression** — moved to secret (PR #33) but secret unpopulated; apply fails |
| Issue #9 — Commented block | ✅ Fixed (PR #34) |
| Issue #10 — SCHEMAS_JSON | ✅ Fixed (PR #32) |
| Issue #12 — tfstate in root | ✅ Fixed (PR #35 docs) |
| Issue #19 — CREATE EXTERNAL LOCATION | ✅ Documented as per-cycle manual step |
| Issue #26 — UC orphaned objects | ⚠️ **Not operationally resolved** — docs added but orphan not cleared |
| Issue #28 — destroy comparison style | ✅ Fixed (PR #30) |
| Issue #6 — variable mismatches | ✅ No regression |
| Issue #21 — SP lacks UAA | ✅ No regression |
| Issue #22 — ANSI output guard | ✅ No regression |

---

## Observations — No Issue Required

- **workload-dbx `init -upgrade` flag**: `infra/workload-dbx` uses `terraform init -upgrade` (line 79 of workload-dbx.yaml). This forces provider re-download on every run. Consider removing `-upgrade` and only using it intentionally when bumping provider versions — it adds latency and introduces non-determinism.
- **`storage_root` path includes `metastore_id` suffix**: `workload-dbx/main.tf` sets `storage_root = "abfss://uc-root@<sa>.dfs.core.windows.net/<metastore_id>"`. This appends the metastore ID as a path component, which is unconventional. Since `lifecycle { ignore_changes = [storage_root] }` is set, this won't cause drift, but it's worth noting for documentation clarity.
- **`# HACKME` comment removed**: PR #33 removed the `# HACKME` comment with the hardcoded value — good housekeeping.

---

## Recommendations

### Unblock now

1. **Populate `ADLS_STORAGE_NAME` secret** in GitHub → Settings → Secrets → Actions (unblocks all workload-azure runs)
2. **Clear orphaned UC objects** — delete `uc-mi-credential` and `uc-root-location` in Databricks Account Console, then re-run workload-dbx apply and re-grant CREATE EXTERNAL LOCATION (unblocks all workload-dbx runs)
3. **Update `BUDGET_END`** in `guardrails.yaml` to a future date (unblocks guardrails)

### Fix soon

4. **Add OIDC federated credential for `pull_request` subject** in Entra ID app registration (enables PR-time `terraform plan` to run)
5. **Address tflint OIDC blocker** before merging PR for issue #11 (the tflint PR itself is ready; the Azure login step must work for PR events first)

### Future

6. **Remove `-upgrade` from `terraform init`** in workload-dbx.yaml — use it explicitly only when bumping providers

---

*Generated by Claude Code — claude-sonnet-4-6*
