# Code Review — 2026-03-03

**Scope:** Full codebase re-review — all Terraform, GitHub Actions, Taskfile, docs, and .gitignore (~2,400 lines)
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Builds on:** [code-review-2026-03-02.md](./code-review-2026-03-02.md)
**Status:** MVP phase

---

## Changes Since Previous Review

| Item | Change |
|------|--------|
| Issue #21 — SP lacks User Access Administrator | **Resolved** — UAA granted at subscription scope (2026-03-02) |
| Issue #22 — Read outputs ANSI corruption | **Fixed** — PR #24 merged |
| Issue #26 — UC objects orphaned on wrong destroy order | **Opened** — pending manual recovery and code safeguard |
| Issue #28 — `inputs.destroy` comparison style inconsistency | **Opened** — new finding from this review |

---

## New Finding

### Issue #28 — `inputs.destroy` comparison style inconsistency (MEDIUM)

`workload-azure.yaml` compares the `inputs.destroy` boolean input using unquoted boolean syntax; `workload-dbx.yaml` uses the explicit string form. GitHub Actions `workflow_dispatch` boolean inputs are passed as the strings `'true'`/`'false'` at runtime, not as actual booleans. Both forms work today via implicit type coercion, but the inconsistency creates a maintenance hazard and obscures intent.

| File | Line | Expression | Style |
|------|------|------------|-------|
| `workload-azure.yaml` | 82 | `inputs.destroy != true` | boolean (implicit coercion) |
| `workload-azure.yaml` | 93 | `inputs.destroy` | truthy (implicit) |
| `workload-dbx.yaml` | 101 | `inputs.destroy != 'true'` | string (explicit) ✓ |
| `workload-dbx.yaml` | 117 | `inputs.destroy == 'true'` | string (explicit) ✓ |

**Fix:** Align `workload-azure.yaml` to the explicit string style used in `workload-dbx.yaml`:
```yaml
# Apply guard (line 82)
if: github.ref == 'refs/heads/main' && inputs.destroy != 'true'

# Destroy step (line 93)
if: inputs.destroy == 'true'
```

→ [Issue #28](https://github.com/nobhri/azure-dbx-mock-platform/issues/28)

---

## Issue Status Snapshot

| Issue | Title | Severity | Status |
|-------|-------|----------|--------|
| [#7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7) | Hardcoded ADLS name in workload-azure.yaml | HIGH | Open |
| [#9](https://github.com/nobhri/azure-dbx-mock-platform/issues/9) | No inline comment on commented-out catalog/schema block | LOW | Open |
| [#10](https://github.com/nobhri/azure-dbx-mock-platform/issues/10) | SCHEMAS_JSON backslash escaping in Taskfile | LOW | Open |
| [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | No tflint/checkov in CI | LOW | Open |
| [#12](https://github.com/nobhri/azure-dbx-mock-platform/issues/12) | terraform.tfstate in repo root | LOW | Open |
| [#15](https://github.com/nobhri/azure-dbx-mock-platform/issues/15) | DATABRICKS_ACCOUNT_ID secret empty | HIGH | Open (resolved operationally — secret populated; issue not yet closed) |
| [#19](https://github.com/nobhri/azure-dbx-mock-platform/issues/19) | SP missing CREATE EXTERNAL LOCATION on UC metastore | HIGH | Open (resolved per cycle; must re-grant after each full destroy/recreate) |
| [#26](https://github.com/nobhri/azure-dbx-mock-platform/issues/26) | UC objects orphaned when destroy order is wrong | HIGH | Open |
| [#28](https://github.com/nobhri/azure-dbx-mock-platform/issues/28) | `inputs.destroy` comparison style inconsistency | MEDIUM | Open — new |

---

## No Regression on Existing Findings

All files re-read in full. No regressions detected on previously resolved items:

- [#6](https://github.com/nobhri/azure-dbx-mock-platform/issues/6) — variable mismatches: **still fixed** (PR #14)
- [#21](https://github.com/nobhri/azure-dbx-mock-platform/issues/21) — SP lacks UAA: **still resolved**
- [#22](https://github.com/nobhri/azure-dbx-mock-platform/issues/22) — ANSI output guard: **still fixed** (PR #24) — `workload-azure.yaml:113` now reads `if: always() && inputs.destroy != true`

---

## Recommendations

### Fix Now

1. **Standardise `inputs.destroy` comparison** in `workload-azure.yaml` — one-line change each for Apply and Destroy steps → [Issue #28](https://github.com/nobhri/azure-dbx-mock-platform/issues/28)
2. **Close issue #15** — `DATABRICKS_ACCOUNT_ID` was populated and SP was granted Account Admin; the issue remains open on GitHub despite being operationally resolved
3. **Move `ADLS_NAME` to GitHub Secret** → [Issue #7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7)

### Fix Soon

4. **Recover from issue #26** (manual steps in Databricks Account Console — delete `uc-mi-credential` and `uc-root-location`, re-run workload-dbx apply, re-apply CREATE EXTERNAL LOCATION grant)
5. **Add destroy-order guard** to `workload-azure.yaml` destroy step — fail if workload-dbx tfstate is non-empty → [Issue #26](https://github.com/nobhri/azure-dbx-mock-platform/issues/26)
6. **Add inline comment** to commented-out catalog/schema block explaining ADR-001 Jinja2 handoff → [Issue #9](https://github.com/nobhri/azure-dbx-mock-platform/issues/9)

### Future

7. **Add tflint/checkov** steps to CI → [Issue #11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11)
8. **Verify and fix SCHEMAS_JSON escaping** in Taskfile → [Issue #10](https://github.com/nobhri/azure-dbx-mock-platform/issues/10)

---

*Generated by Claude Code — claude-sonnet-4-6*
