# Session 2026-03-12-001 — bronze-validation-drop-guard-cov

**Branch:** fix/2026-03-12-001-bronze-validation-drop-guard
**Issue:** #144, #155, #143
**PR:** #156
**Outcome:** completed

## Objective

Address three small pipeline and CI improvements:
- #144: Add bronze schema validation (fail-fast guard) in `pipeline.py`
- #155: Remove one-time `DROP TABLE IF EXISTS` migration guard from both notebooks
- #143: Enable pytest-cov coverage reporting with `--cov-fail-under=80` in CI

## What was done

- Added required-column check in `etl/notebooks/pipeline.py` after reading bronze table
- Removed `DROP TABLE IF EXISTS` + its print statement from `pipeline.py` (migration guard no longer needed post-PR #154)
- Removed `DROP TABLE IF EXISTS` + its print statement from `etl/notebooks/e2e_test.py`
- Updated pytest command in `.github/workflows/test-unit.yaml` to add `--cov=mock_platform --cov-report=term-missing --cov-fail-under=80`

## Decisions

- Bronze validation placed before `clean_orders()` call — earliest point where missing columns can be caught with a clear error message
- `DROP TABLE IF EXISTS` removal is safe: `CREATE OR REPLACE VIEW` is idempotent for view-to-view replacement; guard was only needed for the table→view migration

## Artifacts

- `etl/notebooks/pipeline.py` — bronze schema validation added; DROP TABLE guard removed
- `etl/notebooks/e2e_test.py` — DROP TABLE guard removed
- `.github/workflows/test-unit.yaml` — pytest-cov flags added
- `docs/sessions/2026-03-12-001-bronze-validation-drop-guard-cov.md` — this file
- `docs/status.md` — added #155; marked #143, #144, #155 as in PR #156
- PR #156 opened
