# Session: 2026-03-10-005 — ETL Deploy Workflow Bug Fixes

**Date:** 2026-03-10
**Issue:** [#131](https://github.com/nobhri/azure-dbx-mock-platform/issues/131)
**PRs merged:** #132 (superseded), #133, #134, #135, #136, #138

## What happened

The `workload-etl` workflow was introduced in PR #130 (feature/129) and immediately began
failing. Six PRs were required to fully fix it. Each failure was diagnosed from GH Actions
logs and fixed in a targeted PR.

## Failures and fixes (in order)

### 1 — Notebook paths wrong (PRs #132 / #133)

**Error:**
```
Error: notebook resources/notebooks/e2e_test.py not found
```

**Root cause:** `etl/resources/etl-pipeline.yml` and `etl-e2e-test.yml` used `./notebooks/`
relative paths. The Databricks CLI resolves resource-file paths from the resource file
location (`etl/resources/`), not the bundle root (`etl/`), so it looked for
`etl/resources/notebooks/` which does not exist.

**Fix (PR #133):** Changed `./notebooks/pipeline.py` → `../notebooks/pipeline.py` and
`./notebooks/e2e_test.py` → `../notebooks/e2e_test.py`.

*Note: PR #132 merged the same fix into `feature/129-etl-deploy-workflow` but that branch
had already been merged to main as PR #130, so a second PR (#133) targeting main directly
was required.*

### 2 — Wheel library paths wrong (PR #134)

**Error:**
```
Error: no files match pattern: resources/dist/*.whl
  at resources.jobs.etl-e2e-test.tasks[0].libraries[0].whl
```

**Root cause:** Same relative-path issue. `./dist/*.whl` in the resource files resolved to
`etl/resources/dist/` (non-existent). The wheel is built to `etl/dist/` by
`python -m build etl/`.

**Fix (PR #134):** Changed `./dist/*.whl` → `../dist/*.whl` in both resource files.

### 3 — Wrong schema names (PR #135)

**Error:**
```
[TABLE_OR_VIEW_NOT_FOUND] The table or view `mock`.`sales`.`orders_bronze` cannot be found.
```

**Root cause:** Both `pipeline.py` and `e2e_test.py` hardcoded `schema = "sales"`.
`platform/configs/catalog_schema.yaml` defines three schemas: `bronze`, `silver`, `gold`.
No `sales` schema exists.

**Fix (PR #135):** Removed `schema = "sales"` and mapped each table to its tier schema:
- `orders_bronze` → `mock.bronze.orders_bronze`
- `orders_silver` → `mock.silver.orders_silver`
- `daily_sales_by_region` → `mock.gold.daily_sales_by_region`

### 4 — etl-pipeline run against empty bronze (PR #136)

**Error:**
```
[TABLE_OR_VIEW_NOT_FOUND] The table or view `mock`.`bronze`.`orders_bronze` cannot be found.
```

**Root cause:** The workflow ran `etl-pipeline` (a production job that reads from
pre-existing bronze) in CI where no data exists. `etl-pipeline` is not self-contained.

**Fix (PR #136):** Changed the workflow's bundle run step from `etl-pipeline` to
`etl-e2e-test`. The e2e test job is fully self-contained: generates Faker data, writes
bronze, transforms to silver/gold, and validates schemas and row counts.

### 5 — Remove unused static CSV (PR #138)

`data/sample_orders.csv` was a placeholder from before the Faker-based e2e test was
designed. It was not referenced by any notebook, workflow, or test. Deleted.

## Confirmed working — GH Actions run 22888609919

- **Trigger:** `workflow_dispatch` on `main`, 2026-03-10 05:30 UTC
- **Bundle deploy:** `mock_platform-0.1.0-py3-none-any.whl` uploaded; deployment complete
- **Bundle run (etl-e2e-test):** RUNNING 05:31 → TERMINATED SUCCESS 05:38 (~7 min)
- **Run URL:** `https://adb-7405609923588172.12.azuredatabricks.net/?o=7405609923588172#job/1067147283594802/run/138934924671847`

Human-verified on workspace GUI:
- `mock.bronze.orders_bronze` — created ✅
- `mock.silver.orders_silver` — created ✅
- `mock.gold.daily_sales_by_region` — created ✅

## Files changed

- `etl/resources/etl-pipeline.yml` — `./notebooks/` → `../notebooks/`, `./dist/` → `../dist/`
- `etl/resources/etl-e2e-test.yml` — same path fixes
- `etl/notebooks/pipeline.py` — tier-specific schemas (bronze/silver/gold)
- `etl/notebooks/e2e_test.py` — tier-specific schemas
- `.github/workflows/workload-etl.yaml` — run `etl-e2e-test` instead of `etl-pipeline`
- `data/sample_orders.csv` — deleted (superseded by Faker-based e2e test)
