# Session 2026-03-06-007 — Issue #80: Replace static import block with dynamic CI discovery

## Summary

Replaced the static `import {}` block in `workload-dbx/main.tf` with a dynamic
"Import metastore if it exists but not in state" CI step. Also removed the
`METASTORE_ID` GitHub secret dependency and fixed the preflight bug in
`workload-catalog.yaml`.

## Root Cause (Issue #80)

The first-ever successful `workload-dbx` destroy (after issue #64 was fixed with the
correct UUID) deleted the metastore. On the next apply, the static import block tried
to import using the old `METASTORE_ID` UUID — which no longer existed.

The import block design assumed the metastore always survived a destroy run. This was
true while #64 was unresolved (bad UUID → destroy always failed at the import step).
Now that the correct UUID is in use, destroy can succeed and actually delete the metastore.

## Root Cause (Preflight Bug — discovered in same session)

`databricks external-locations list` returned an error to stderr when no metastore
was assigned. stdout was empty → jq produced no output → `COUNT` was `""` →
`[ "" -eq 0 ]` returned exit 2 (`integer expression expected`). In bash `if` context,
exit 2 is treated as "false" → body skipped → "Preflight passed" printed despite failure.

## What Changed

- `infra/workload-dbx/main.tf`: removed static `import {}` block; changed `storage_root`
  to use container root (no longer depends on metastore UUID path suffix)
- `infra/workload-dbx/variables.tf`: removed `metastore_id` variable
- `.github/workflows/workload-dbx.yaml`: removed `-var="metastore_id=..."` from all three
  terraform steps; added "Import metastore if it exists but not in state" step after init
- `.github/workflows/workload-catalog.yaml`: fixed preflight to capture CLI exit code
  explicitly (`if ! RAW=$(...)`) so CLI errors are treated as preflight failures
- `docs/runbooks/destroy-recreate.md`: removed METASTORE_ID update step from recreate
  procedure; updated Notes section
- `GETTING_STARTED.md`: removed `METASTORE_ID` from required secrets table

## Dynamic Import Step Logic

1. If `databricks_metastore.this` is already in Terraform state → skip (no-op)
2. Call `GET /api/2.0/accounts/<account_id>/metastores` via Azure-issued Bearer token
3. If a metastore is found → `terraform import databricks_metastore.this <uuid>`
4. If no metastore found → no-op (Terraform will create fresh on apply)

## PRs

- PR #79 (`fix/68-catalog-preflight`) — includes the preflight bug fix (second commit)
- PR #81 (`fix/80-dynamic-metastore-import`) — this PR
