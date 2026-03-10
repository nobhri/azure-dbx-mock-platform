# Proposal: ETL Short-Term Improvements

**Status:** Accepted
**Date:** 2026-03-10
**Layer:** Data Engineering
**Related ADRs:** ADR-003 (idempotency), ADR-004 (consumer access)
**Origin:** Code review of `etl/` — session 2026-03-10-008

---

## Context

After completing Phase 2 data engineering (PRs #124, #125, and related), a code review
of the `etl/` directory and `.github/workflows/test-unit.yaml` identified several
short-term improvements that should be addressed before the next feature work.

---

## 1. Gold Layer: Use Views Instead of Tables

**Decision:** Replace `daily_sales_by_region` materialized table with a SQL view.

**Current state:** `pipeline.py` computes the gold aggregation via `aggregate_daily_sales()`
and writes it as a table using `saveAsTable(mode="overwrite")`.

**Change:** Create `daily_sales_by_region` as a `CREATE OR REPLACE VIEW` over the silver
table. The `aggregate_daily_sales()` function in `transform.py` remains as-is for unit
testing, but the pipeline notebook no longer materializes gold.

**Rationale:**
- ADR-004 establishes views as the default consumer access pattern.
- The aggregation (`GROUP BY region, order_date` with SUM/COUNT) is trivial for
  Delta/Photon to compute on-read.
- Views always reflect the latest silver data — no staleness window.
- Eliminates the gold overwrite job step and its operational surface.
- Data volume in this mock platform is tiny; materialization adds cost without benefit.

**Production note:** Per-object materialization decisions should be based on query patterns
and SLAs. The default should be views; tables only when performance requires it. This can
be documented in ADR-006 alongside the overwrite pattern.

**Impact:**
- `etl/notebooks/pipeline.py` — remove gold write step; add `CREATE OR REPLACE VIEW`
- `etl/notebooks/e2e_test.py` — update gold validation (view instead of table)
- `etl/src/mock_platform/transform.py` — no change (function retained for unit tests)
- `etl/tests/unit/test_transform.py` — no change

---

## 2. Add Wheel Build Step to CI

**Current state:** `.github/workflows/test-unit.yaml` runs `pip install -e ".[dev]"` and
`pytest`, but never tests that the wheel actually builds.

**Problem:** A broken `pyproject.toml` (e.g., missing package discovery config, bad
metadata) would pass CI but fail at `bundle deploy` time when the wheel is built.

**Change:** Add a step after install that runs `pip wheel --no-deps -w dist .` and
verifies a `.whl` file is produced. This catches packaging issues before they reach
Databricks.

**Impact:**
- `.github/workflows/test-unit.yaml` — add wheel build step after pytest

---

## 3. Use pytest-cov or Remove It

**Current state:** `pyproject.toml` declares `pytest-cov>=4.1` as a dev dependency, but
the CI command (`pytest tests/unit/ -v --tb=short`) does not use it.

**Decision:** Enable coverage reporting with a minimum threshold.

**Change:** Update the pytest command to:
```
pytest tests/unit/ -v --tb=short --cov=mock_platform --cov-report=term-missing --cov-fail-under=80
```

**Rationale:** The dependency is already paid for. A coverage gate catches regressions
early — especially useful as more transforms are added.

**Impact:**
- `.github/workflows/test-unit.yaml` — update pytest command

---

## 4. Bronze Schema Validation at Read Time

**Current state:** `pipeline.py` reads the bronze table and passes it directly to
`clean_orders()`. If the bronze table has unexpected or missing columns, the pipeline
fails with opaque Spark errors.

**Change:** Add a lightweight column-existence check after reading bronze, before
calling `clean_orders()`. Example:

```python
required_columns = {"order_id", "customer_id", "product_id",
                    "quantity", "unit_price", "order_date", "region"}
missing = required_columns - set(bronze_df.columns)
if missing:
    raise ValueError(f"Bronze table missing columns: {missing}")
```

This is not a full schema enforcement framework — just a fail-fast guard that produces
a clear error message.

**Impact:**
- `etl/notebooks/pipeline.py` — add column check after bronze read

---

## Implementation Order

These items are independent and can be addressed in any order or combined into a single PR.

| Item | Scope | Effort |
|------|-------|--------|
| Gold as view | pipeline.py, e2e_test.py | Small |
| Wheel build in CI | test-unit.yaml | Trivial |
| pytest-cov | test-unit.yaml | Trivial |
| Bronze schema check | pipeline.py | Small |

---

## Deferred Items

See [etl-future-enhancements.md](etl-future-enhancements.md) for medium/long-term
recommendations from the same review.
