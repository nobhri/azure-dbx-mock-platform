# Session 2026-03-17-001 — metastore-import-test-flag

**Branch:** fix/2026-03-17-001-metastore-import-test-flag
**Issue:** #82
**PR:** (fill in when created)
**Outcome:** (fill in at session end)

## Objective

Exercise Branch 3 of the dynamic metastore import step in `workload-dbx.yaml` —
"Found existing metastore — importing into Terraform state" — which has never been
triggered in CI.

## What was done

Added a `reset_metastore_state` boolean input (default `false`) to `workload-dbx.yaml`.
When `true` (only triggerable via `workflow_dispatch`), a new step runs
`terraform state rm databricks_metastore.this` before the import step, simulating the
"partial destroy" scenario described in issue #82.

Orchestrators (`orchestrator-up`, `orchestrator-down`) are unaffected — they call
`workload-dbx.yaml` without passing the new input, so it defaults to `false`.

## Decisions

- Implemented as a flag on the existing workflow rather than a separate test workflow,
  to avoid file bloat and keep all metastore logic co-located.
- Flag is `workflow_dispatch`-only (not exposed via `workflow_call`), so orchestrators
  cannot accidentally trigger it.
- Guarded by `inputs.destroy != true` to prevent accidental state removal on destroy runs.

## Artifacts

- `.github/workflows/workload-dbx.yaml` — added `reset_metastore_state` input and step
