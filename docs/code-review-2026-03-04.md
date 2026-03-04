# Code Review — 2026-03-04

**Scope:** Targeted review — GitHub Actions run analysis post PR #48/#49 (inputs.destroy boolean fixes)
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Builds on:** [code-review-2026-03-03.md](./code-review-2026-03-03.md)
**Status:** MVP phase

---

## Changes Since Previous Review (PR #49 baseline)

| Item | Change |
|------|--------|
| Issue #45 — `inputs.destroy` boolean comparison (workload-azure) | **Closed** — PR #48 fixed string `'true'` → boolean `true` |
| Issue #47 — `inputs.destroy` boolean comparison (workload-dbx) | **Closed** — PR #49 same fix applied to workload-dbx.yaml |
| Issue #26 — UC objects orphaned / metastore not empty on destroy | **Reopened → fix in PR #50** — `force_destroy = true` added to `databricks_metastore.this` |

---

## New Finding — metastore destroy blocked by notebook-created catalog (issue #26 revisited)

**Run:** [22648177521](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22648177521)
**Triggered:** workflow_dispatch (destroy) on main, 2026-03-03T23:49Z

```
Error: cannot delete metastore: Metastore '30ebd5eb-ba32-4617-b715-1bbad2ad51e0' is not empty.
The metastore has 1 catalog(s), 1 storage credential(s), 0 share(s) and 0 recipient(s)
```

**Root cause:**

The destroy plan contained only 2 resources:
- `databricks_metastore_assignment.this`
- `databricks_metastore.this`

The catalog is created by the Jinja2/Python notebook (ADR-001) and is never in Terraform state. The storage credential is orphaned (not in state). Terraform cannot clean up what it does not track, so the Databricks API rejects the metastore delete.

This is distinct from the original issue #26 scenario (wrong destroy order) — even with correct order, the notebook-created catalog prevents metastore deletion.

**Fix:** `force_destroy = true` on `databricks_metastore.this` — instructs the Databricks API to cascade-delete all child UC objects (catalogs, schemas, storage credentials) before removing the metastore, regardless of Terraform state.

**PR:** [#50](https://github.com/nobhri/azure-dbx-mock-platform/pull/50)

---

## Issue Status Snapshot (current)

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | Add tflint to CI | LOW | **Open** — blocked by OIDC issue #40 |
| [#26](https://github.com/nobhri/azure-dbx-mock-platform/issues/26) | UC objects orphaned — metastore not empty on destroy | HIGH | **Fix in PR #50** — `force_destroy = true` |
| [#39](https://github.com/nobhri/azure-dbx-mock-platform/issues/39) | `ADLS_STORAGE_NAME` secret not set — workload-azure broken | HIGH | **Open** — manual secret population required |
| [#40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40) | OIDC not configured for `pull_request` subject | MEDIUM | **Open** — Entra ID federated credential needed |
| [#41](https://github.com/nobhri/azure-dbx-mock-platform/issues/41) | guardrails `BUDGET_END` expired | LOW | **Open** — `BUDGET_END` needs future date |
| [#45](https://github.com/nobhri/azure-dbx-mock-platform/issues/45) | `inputs.destroy` boolean comparison broken (workload-azure) | HIGH | **Closed** — PR #48 |
| [#47](https://github.com/nobhri/azure-dbx-mock-platform/issues/47) | `inputs.destroy` boolean comparison broken (workload-dbx) | HIGH | **Closed** — PR #49 |

---

## Regressions / Carry-over from Previous Review

| Item | Status |
|------|--------|
| Issue #7 — ADLS hardcoded | ⚠️ **Regression** — secret `ADLS_STORAGE_NAME` still not populated; workload-azure broken |
| Issue #26 — UC orphaned objects | ⚠️ **Not operationally resolved** — documentation-only close was insufficient; PR #50 applies code fix |
| Issue #28 — destroy comparison style | ✅ Superseded — PRs #48/#49 corrected all boolean comparisons |

---

## Observations — No Issue Required

- **`force_destroy` scope:** The `force_destroy = true` flag only applies on `terraform destroy`. It has no effect on `terraform apply` — existing UC objects created by the notebook are not affected during apply cycles.
- **Post-PR #50 destroy behaviour:** Correct destroy order (workload-dbx first, workload-azure second) is still required. `force_destroy` eliminates the notebook-catalog blocker but does not change the dependency on Azure resources being present when workload-dbx destroys.
- **Manual grant still required after full recreate:** After a full destroy + recreate cycle, `GRANT CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>'` must be re-applied manually (issue #19 — documented per-cycle step, cannot be automated).

---

## Recommendations

### Unblock now

1. **Merge PR #50** — resolves workload-dbx destroy failure; no manual UC cleanup needed after merge
2. **Populate `ADLS_STORAGE_NAME` secret** in GitHub → Settings → Secrets → Actions (unblocks all workload-azure runs — issue #39)
3. **Update `BUDGET_END`** in `guardrails.yaml` to a future date (unblocks guardrails — issue #41)

### Fix soon

4. **Add OIDC federated credential for `pull_request` subject** in Entra ID app registration (enables PR-time `terraform plan` — issue #40)
5. **Address tflint OIDC blocker** before merging PR for issue #11

### Future

6. **Remove `-upgrade` from `terraform init`** in workload-dbx.yaml — use explicitly only when bumping providers (carry-over observation)

---

*Generated by Claude Code — claude-sonnet-4-6*
