# Session 2026-03-17-001 — tflint-hcl-config

**Branch:** fix/2026-03-17-001-tflint-hcl-config
**Issue:** #11
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Add `.tflint.hcl` config files to `infra/workload-azure` and `infra/workload-dbx` so that `tflint --init` downloads the azurerm ruleset and enforces provider-specific rules in CI.

## What was done

- Added `infra/workload-azure/.tflint.hcl` with `plugin "azurerm" { version = "0.27.0" }`
- Added `infra/workload-dbx/.tflint.hcl` with `plugin "azurerm" { version = "0.27.0" }`
- The Databricks provider has no tflint ruleset; azurerm covers the Azure resources in both workloads

## Decisions

- Used `tflint-ruleset-azurerm` 0.27.0 — supports both azurerm ~3.x (workload-azure) and ~4.x (workload-dbx)
- Same plugin version for both configs to reduce maintenance drift

## Artifacts

- `infra/workload-azure/.tflint.hcl` — new
- `infra/workload-dbx/.tflint.hcl` — new
- `docs/sessions/2026-03-17-001-tflint-hcl-config.md` — this file
