# Session 2026-03-10-008 — ETL Code Review

## Objective

Review ETL code (`etl/` and `.github/workflows/test-unit.yaml`) for alignment with
ADRs, implementation plan, and general quality. Produce proposals and issues for
identified improvements.

## Review Scope

- `etl/src/mock_platform/transform.py`
- `etl/src/mock_platform/catalog_lookup.py`
- `etl/notebooks/pipeline.py`
- `etl/notebooks/e2e_test.py`
- `etl/resources/etl-pipeline.yml`, `etl-e2e-test.yml`
- `etl/databricks.yml`, `etl/pyproject.toml`
- `etl/tests/unit/test_transform.py`, `test_catalog_lookup.py`
- `.github/workflows/test-unit.yaml`
- All ADRs (001–005)
- `docs/proposals/data-engineering-implementation-plan.md`

## Findings

### ADR Alignment

| ADR | Status | Notes |
|-----|--------|-------|
| ADR-001 (Terraform scope) | Aligned | ETL handles tables only; no Terraform |
| ADR-002 (OIDC) | Aligned | CI uses `contents: read` only |
| ADR-003 (Idempotency) | Partially aligned | Overwrite is idempotent, but ADR-006 not yet written (refs #126) |
| ADR-004 (Consumer access) | Decision made | Gold layer to use views (see below) |
| ADR-005 (Group permissions) | N/A | No permission logic in ETL |

### Implementation Plan Alignment

Code matches the plan closely. One deviation: `data/sample_orders.csv` removed in
commit 098ea15 (replaced by Faker-based E2E). ADR-006 and ADR-007 still pending
(tracked in #126).

### Decisions Made

- **Gold layer objects will use views instead of tables.** Rationale: aligns with
  ADR-004, trivial aggregation, eliminates staleness, reduces operational surface.

### Short-Term Issues Created

- Gold layer: use view instead of table
- CI: add wheel build step
- CI: enable pytest-cov
- Pipeline: add bronze schema validation

### Issues for Reference

- ADR-006 and ADR-007: tracked in #126

## Artifacts

- `docs/proposals/etl-short-term-improvements.md` (Accepted)
- `docs/proposals/etl-future-enhancements.md` (Proposed)
- `docs/proposals/README.md` updated
- GitHub issues created for short-term items
