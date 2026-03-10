# Proposal: Testing Strategy

**Status:** Accepted — Phase 2 data engineering
**Date:** 2026-03-05
**Layer:** Data Engineering
**Related ADRs:** ADR-003 (idempotency)

---

## Decision

Implement Option A (schema validation) and Option B (unit tests for transform logic). DuckDB is deferred.

| Option | Decision |
|--------|----------|
| A — Schema validation (column names, types, nullable assertions) | ✅ Implement |
| B — PySpark transform unit tests (local SparkSession) | ✅ Implement |
| C — DuckDB SQL unit tests | Deferred — documented as future work |

## Rationale

- Option A alone is too thin to demonstrate test design skill.
- Option B is a natural fit for a `saveAsTable`-based ETL because the test boundary (transform
  function input/output) is clean and does not require a live cluster.
- DuckDB (Option C) would create a mismatch: the pipeline uses `saveAsTable`, not a SQL execution
  engine that DuckDB naturally targets. Deferred to a future iteration where it fits better.

---

## DDL Testing Approaches

The Jinja2-based DDL layer (catalog and schema creation) currently has no automated tests. The
following patterns are candidates when DDL testing is introduced:

| Pattern | Description |
|---------|-------------|
| `CREATE IF NOT EXISTS` idempotency verification | Run the DDL notebook twice against a test catalog; assert no errors and no state change on the second run |
| Schema drift detection | Query `system.information_schema.columns` before and after DDL execution; assert the diff matches the expected changes exactly |
| DDL render test (Python) | Unit-test the Jinja2 template rendering in isolation — assert the rendered SQL string matches expected output for each environment variable combination |
| Destructive-change guard | Assert that no `DROP` or `ALTER COLUMN` statements appear in a rendered DDL unless explicitly flagged |

**Tooling options:**
- Python (`pytest`) for Jinja2 render tests — no cluster required
- PySpark / Databricks Connect for idempotency and drift detection — requires a live catalog
- DuckDB as an execution target for rendered SQL — viable if SQL is ANSI-compatible (note: some
  Databricks DDL extensions will not work in DuckDB)

---

## Deferred Items

| Item | Notes |
|------|-------|
| DuckDB SQL unit tests | Better fit when a SQL-centric pipeline exists; see Jinja2 DDL layer as a future candidate |
