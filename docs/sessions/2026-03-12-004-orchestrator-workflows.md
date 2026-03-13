# Session 2026-03-12-004 — orchestrator-workflows

**Branch:** feat/2026-03-12-004-orchestrator-workflows
**Issue:** #162
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Add `orchestrator-up.yaml` and `orchestrator-down.yaml` workflows that chain
the existing workload workflows in sequence, enabling a one-click deploy/destroy
cycle for cost-optimized platform operations.

## What was done

1. Added `workflow_call` trigger to all four workload workflows:
   - `workload-azure.yaml` — `workflow_call` with `destroy: boolean, default false`
   - `workload-dbx.yaml` — `workflow_call` with `destroy: boolean, default false`
   - `workload-catalog.yaml` — `workflow_call: {}` (no inputs)
   - `workload-etl.yaml` — `workflow_call` with `env: string, default dev`
     (`choice` type not supported by `workflow_call`; uses `string` instead)

2. Created `.github/workflows/orchestrator-up.yaml`:
   - `workflow_dispatch` trigger (no inputs)
   - Jobs: azure → dbx → catalog → etl (each `needs:` the previous)
   - All jobs use `secrets: inherit`

3. Created `.github/workflows/orchestrator-down.yaml`:
   - `workflow_dispatch` trigger (no inputs)
   - Jobs: dbx (destroy: true) → azure (destroy: true)
   - catalog and etl skipped — metastore `force_destroy = true` handles cleanup

## Decisions

- Two separate orchestrator files (not one with a toggle) per issue spec — reduces
  misclick risk in GitHub Actions UI and keeps run history readable.
- `workflow_call` input names mirror `workflow_dispatch` names — GitHub resolves
  `inputs.*` from the correct trigger at runtime, no conflict.
- `permissions: id-token: write` added to both orchestrators — required for OIDC
  in called workflows when using `secrets: inherit`.

## Artifacts

- Modified: `.github/workflows/workload-azure.yaml`
- Modified: `.github/workflows/workload-dbx.yaml`
- Modified: `.github/workflows/workload-catalog.yaml`
- Modified: `.github/workflows/workload-etl.yaml`
- Created: `.github/workflows/orchestrator-up.yaml`
- Created: `.github/workflows/orchestrator-down.yaml`
- Created: `docs/sessions/2026-03-12-004-orchestrator-workflows.md`
