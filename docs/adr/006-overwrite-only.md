# ADR-006: Overwrite-Only Writes — Merge Pattern Deferred

**Status:** Accepted
**Date:** 2026-03-12

---

## Context

The ETL pipeline processes Sales Orders through three medallion layers:

- **Bronze** — raw ingestion, CSV-sourced or Faker-generated records, no transformation
- **Silver** — cleaned and typed (type casting, null handling, dedup on `order_id`)
- **Gold** — aggregated for consumption (`daily_sales_by_region`)

All writes must be idempotent by construction (ADR-003). Two write patterns were candidates for
the silver layer: full overwrite and upsert via merge.

The gold layer is a SQL view rather than a table, which removes it from the overwrite-vs-merge
decision entirely — `CREATE OR REPLACE VIEW` is inherently idempotent and has no merge analogue.

---

## Decision

- **Silver layer:** `saveAsTable(mode("overwrite"))` with `overwriteSchema=true`
- **Gold layer:** `CREATE OR REPLACE VIEW` — no separate write step (aligns with ADR-004)
- **`DeltaTable.merge()` (or SQL `MERGE INTO`):** explicitly deferred — not implemented

---

## Rationale

**Overwrite satisfies ADR-003 idempotency automatically.**
A failed run can be retried immediately without inspecting or cleaning up partial state. No
deduplication logic, no primary-key enforcement, and no conflict-resolution strategy is required
at the write step.

**A full batch reload is acceptable at current scale.**
The Sales Orders dataset is small, bounded, and fully regenerated on every E2E test run. There is
no SLA constraint that makes a full rewrite prohibitive. The cost difference between overwrite and
incremental merge is negligible at this volume.

**Merge requires upstream design decisions that are not yet made.**
A correct merge implementation requires a stable primary key enforced upstream, a
conflict-resolution strategy for late-arriving records, and an ingestion timestamp or equivalent
ordering field. None of these exist in the current pipeline. Introducing merge without them would
produce an implementation that looks incremental but silently produces incorrect results under
retry or late-arrival conditions.

**Overwrite makes the test contract simpler.**
Unit tests operate on pure transformation functions (in `transform.py`) with no I/O. E2E tests
generate a fresh dataset on every run. Overwrite semantics mean test assertions are always against
a clean table state — no test setup or teardown required to handle residual data from a previous run.

---

## When Merge Becomes Necessary

The overwrite pattern should be revisited when any of the following conditions arise:

| Condition | Why overwrite breaks down |
|-----------|--------------------------|
| **Fact tables with late-arriving records** | Corrections that arrive after the initial load overwrite the corrected row with stale data on the next full reload |
| **Incremental loads from high-volume sources** | Full rewrite latency becomes unacceptable as data volume grows (streaming sources, high-frequency APIs) |
| **SCD Type 2 (preserve history)** | Overwrite destroys previous versions of a row; historical access requires a merge-based upsert with effective-date tracking |
| **Multiple upstream sources contributing to the same table** | Full overwrite from one source silently deletes rows written by another |

---

## Design Changes Required When Merge Is Introduced

The write step in `pipeline.py` must be replaced with an upsert operation keyed on `order_id`.
Two implementation paths are candidates at that point:

- **PySpark (`DeltaTable.merge()`)** — merge logic expressed in Python, consistent with the
  existing `transform.py` / `pipeline.py` split. Transformation and persistence remain in the
  same language layer.
- **SQL (`MERGE INTO`) via Jinja2 template** — merge logic expressed in SQL, consistent with the
  Jinja2 templating pattern already used in the Platform Layer for catalog/schema DDL. Suitable
  if the merge logic grows complex enough that SQL readability outweighs the additional template
  management overhead.

Regardless of implementation path, the following must be defined before merge is introduced:

- **`order_id` uniqueness enforcement upstream** — duplicate `order_id` values in bronze must be
  resolved before the merge step, or the merge condition must be defined to handle them explicitly
- **Conflict-resolution strategy** — a deterministic rule for which record wins when the same
  `order_id` arrives multiple times (e.g., keep the record with the latest ingestion timestamp)
- **Late-arrival handling** — a field (ingestion timestamp or `order_date`) that establishes
  ordering for out-of-sequence records

The implementation choice and the upstream enforcement design are deferred to the ADR that
replaces or extends this one.

---

## Trade-offs Accepted

- **Compute cost:** Full table rewrite on every run is more expensive than an incremental merge
  for large tables. This trade-off is accepted: correctness and simplicity over cost optimization
  at current scale (consistent with ADR-003).
- **`overwriteSchema=true` silently drops schema:** If a column is removed from the transformation
  output, the table schema changes without warning to downstream consumers. Acceptable for the mock
  environment; in production, schema evolution must be controlled explicitly (see
  `docs/proposals/etl-future-enhancements.md` §6).

---

## Rejected Alternatives

**`mode("append")`** — produces duplicates on every retry. Violates ADR-003. Rejected.

**`MERGE INTO` now** — over-engineering: implementing merge before the upstream primary key
enforcement and late-arrival handling design is in place produces a merge that appears correct
under the happy path but silently fails under late-arrival or retry conditions. The operational
risk of a "merge-shaped bug" in production is higher than the operational risk of a known
overwrite limitation that is explicitly documented.

---

## Consequences

- Every pipeline run rewrites the full silver table. Downstream consumers reading during a pipeline
  run will observe a momentary empty table (Delta Lake time-travel mitigates this in production if
  `readChangeFeed` or snapshot isolation is used).
- The `order_id` deduplication in `clean_orders()` (`transform.py`) uses `dropDuplicates`, which
  makes no ordering guarantee when duplicates have different field values. This is acceptable for
  overwrite; it must be replaced with a deterministic Window function if merge is introduced
  (see `docs/proposals/etl-future-enhancements.md` §7).
- When merge is introduced, this ADR should be superseded (marked **Superseded**) and replaced
  with a new ADR documenting the merge design.
