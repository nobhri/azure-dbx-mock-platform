# Session 2026-03-12-001 — ci-wheel-build

**Branch:** fix/2026-03-12-001-ci-wheel-build
**Issue:** #142
**PR:** #157
**Outcome:** completed

## Objective

Add a wheel build step to `test-unit.yaml` so packaging errors are caught in CI before `bundle deploy` attempts to upload the `.whl`.

## What was done

Added a `Build wheel` step to `.github/workflows/test-unit.yaml` after the unit tests pass.
The step installs the `build` package and runs `python -m build --wheel`, outputting to `dist/`.
This catches `pyproject.toml` misconfigurations, missing `__init__.py`, and other packaging errors early.

## Artifacts

- `.github/workflows/test-unit.yaml` — added Build wheel step
