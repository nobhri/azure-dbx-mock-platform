# Session 2026-03-10-011 — GH Actions ETL deploy workflow (#129)

**Branch:** feature/129-etl-deploy-workflow
**Issue:** #129
**Depends on:** #125 merged (via PR #128)

## What was done

- Created `.github/workflows/workload-etl.yaml`
  - Triggers: `push` to `main` (paths: `etl/**`); `workflow_dispatch` with `env` choice input (dev / prod)
  - `concurrency` group prevents overlapping deploys per target
  - Auth: Azure OIDC → Terraform init → capture `workspace_url` output → set `DATABRICKS_HOST`
  - Databricks token: acquired from Azure CLI (`az account get-access-token`) — same SP used by other workloads
  - Wheel build: `actions/setup-python@v5` + `pip install build` + `python -m build etl/`
  - Target: `dev` for push; `${{ inputs.env }}` for workflow_dispatch
  - `bundle deploy` then `bundle run etl-pipeline --no-wait=false`

## Design notes

- Follows the exact pattern of `workload-catalog.yaml` (OIDC auth, Terraform output capture, CLI install)
- `push` → `dev` target only; `prod` requires explicit `workflow_dispatch` with `env=prod` — consistent with "Prod execution: CI/CD only, no manual runs"
- Wheel build runs in the runner before `bundle deploy` so `etl/dist/*.whl` exists when the bundle is uploaded
- No new secrets required — reuses `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `TFSTATE_SA_UNIQ`

## Files changed

- `.github/workflows/workload-etl.yaml` (new)
- `docs/sessions/2026-03-10-011-etl-deploy-workflow-129.md` (this file)
