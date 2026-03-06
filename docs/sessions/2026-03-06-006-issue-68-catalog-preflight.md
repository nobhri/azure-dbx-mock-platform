# Session 2026-03-06-006 — Issue #68: workload-catalog preflight check

## Summary

Added a preflight check to `workload-catalog.yaml` that fails fast with a clear error when
the UC External Location (`uc-root-location`) is missing. Also documented the
`workload-catalog` deployment step and its dependency in `GETTING_STARTED.md`.

## Changes

- `.github/workflows/workload-catalog.yaml`: added "Preflight — verify UC external location
  exists" step before `bundle deploy`; uses `databricks external-locations list --output json`
  + `jq` to check for `uc-root-location`; exits with `::error::` annotation if not found
- `GETTING_STARTED.md`: added step 5 (Workload — Catalog Layer) to Deployment Steps with
  explicit prerequisite note; added `EXTERNAL_LOCATION_DOES_NOT_EXIST` entry to Common Pitfalls

## Root Cause (Issue #68)

`CREATE CATALOG ... MANAGED LOCATION` requires a UC External Location covering the target
ABFSS path. `uc-root-location` is created by `workload-dbx` Terraform. Without it, the
notebook fails with `AnalysisException: EXTERNAL_LOCATION_DOES_NOT_EXIST`. The underlying
cause is not a catalog bug — it is a missing infrastructure prerequisite.

## Why This Fix

Without the preflight, the error surfaces deep inside the notebook run as a SQL
`AnalysisException`, which is hard to diagnose. The preflight surfaces it as a workflow step
failure with an explicit message pointing to the runbook, before any bundle deploy occurs.

## PR

PR #78 (`fix/68-catalog-preflight`)
