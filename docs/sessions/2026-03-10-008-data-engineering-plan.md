# Session: 2026-03-10-008 — Data Engineering Implementation Plan

**Date:** 2026-03-10
**Branch:** `docs/data-engineering-plan`
**Relates to:** All 5 accepted data engineering proposals

## What happened

Reviewed the 5 accepted data engineering proposals (etl-overwrite-pattern, testing-strategy,
code-design-transform-separation, sdlc-catalog-lookup, wheel-packaging) and identified 7 open
questions that were deferred to implementation time. Resolved all 7 and created a consolidation
proposal (`data-engineering-implementation-plan.md`).

## Decisions made

1. **Data domain:** Sales Orders (single entity, 7 columns)
2. **Medallion scope:** Full 3-layer (bronze → silver → gold)
3. **Catalog lookup:** Returns `mock` for all targets; pattern-only for now
4. **Wheel contents:** `transform.py` + `catalog_lookup.py`; pipeline notebook stays outside
5. **Test execution:** Unit tests on GH Actions runner; E2E on Databricks cluster
6. **Implementation order:** 3 PRs (wheel+transforms+tests → pipeline+E2E → ADR-006/007)
7. **Data generation:** Static fixtures for unit tests; Faker on Databricks for E2E (not in wheel)

## Files changed

- `docs/proposals/data-engineering-implementation-plan.md` — new proposal (Accepted)
- `docs/proposals/README.md` — added entry for new proposal
