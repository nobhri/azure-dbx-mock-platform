# Session 2026-03-11-001 — Drop table before gold view

## Goal
Fix CI failure: `CREATE OR REPLACE VIEW` fails when `daily_sales_by_region` already exists as a Delta TABLE.

## Root Cause
PR #152 converted the gold layer from `saveAsTable` to `CREATE OR REPLACE VIEW`. The previous successful CI run (22888609919) had written the gold object as a Delta table. When the new view DDL ran against the existing table, Spark raised `EXPECT_VIEW_NOT_TABLE.NO_ALTERNATIVE` (SQLSTATE 42809).

## Fix
Added `DROP TABLE IF EXISTS {gold_view}` immediately before `CREATE OR REPLACE VIEW` in both notebooks:
- `etl/notebooks/pipeline.py`
- `etl/notebooks/e2e_test.py`

This is a one-time migration guard. Once the table is gone and the view exists, subsequent runs are idempotent via `CREATE OR REPLACE VIEW`.

## Artifacts
- `etl/notebooks/pipeline.py` — drop step added
- `etl/notebooks/e2e_test.py` — drop step added

## Outcome
PR created. Awaiting human review and CI confirmation.
