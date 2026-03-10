# Proposal: ETL Future Enhancements

**Status:** Proposed
**Date:** 2026-03-10
**Layer:** Data Engineering
**Related ADRs:** ADR-003 (idempotency), ADR-004 (consumer access)
**Origin:** Code review of `etl/` — session 2026-03-10-013

---

## Context

Code review of the ETL implementation identified several medium and long-term
enhancements. These are not blocking current work but should be considered as the
platform matures.

---

## Medium-Term Enhancements

### 1. Data Quality Checks in Pipeline

**Current state:** Data quality validation exists only in the E2E test notebook.
The production pipeline has no runtime quality gates.

**Recommendation:** Add lightweight assertions within `pipeline.py` that fail the
job if data quality drops below acceptable thresholds. Examples:
- Row count after silver write is > 0
- Null percentage in key columns after `clean_orders()` is 0%
- Revenue values in gold are positive

**Options:**
- Inline assertions in the notebook (simplest)
- Great Expectations integration (more comprehensive, adds dependency)
- Delta Live Tables expectations (if DLT is adopted)

**When:** Before adding a second data entity or before production use.

---

### 2. Incremental Processing (MERGE Pattern)

**Current state:** All layers use `mode("overwrite")`, which rewrites the entire table
on every run. This is documented as intentional in the overwrite pattern proposal and
will be formalized in ADR-006.

**Recommendation:** When data volume grows or when fact tables with late-arriving data
are introduced, implement `DeltaTable.merge()` for the silver layer:
- Use `order_id` as the merge key
- Handle late-arriving records and corrections
- Keep overwrite for gold (or views per short-term proposal)

**Prerequisites:**
- ADR-006 must be written first (refs #126)
- A use case with incremental data (e.g., streaming source, API ingestion)

**When:** When a second data entity is added, or when overwrite latency becomes
unacceptable.

---

### 3. Pipeline Observability

**Current state:** `pipeline.py` has no logging, metrics, or audit trail. Success/failure
is visible only in the Databricks job run UI.

**Recommendation:** Add structured output to the notebook:
- Row counts at each stage (bronze read, silver write, gold write/view)
- Timing for each transformation step
- Data quality summary metrics
- Optional: write audit records to a dedicated `audit.pipeline_runs` table

**When:** Before production use or when debugging pipeline failures becomes painful.

---

### 4. Pipeline Parameterization for Multi-Entity Support

**Current state:** Table names are hardcoded in `pipeline.py`:
- `bronze.orders_bronze`
- `silver.orders_silver`
- `gold.daily_sales_by_region`

**Recommendation:** When adding a second entity, extract table names into configuration
(e.g., a YAML manifest or notebook widget parameters). This avoids duplicating the
pipeline notebook for each entity.

**Design sketch:**
```python
entities = [
    {"bronze": "orders_bronze", "silver": "orders_silver",
     "clean_fn": clean_orders},
]
for entity in entities:
    df = spark.table(f"{catalog}.bronze.{entity['bronze']}")
    cleaned = entity["clean_fn"](df)
    cleaned.write.mode("overwrite").saveAsTable(f"{catalog}.silver.{entity['silver']}")
```

**When:** When a second data entity is introduced.

---

## Long-Term Enhancements

### 5. Delta Live Tables (DLT)

**Current state:** ETL uses notebook-based orchestration with explicit
`spark.read` / `DataFrame.write` calls.

**Recommendation:** Evaluate DLT when the batch ETL pattern is stable and proven.
DLT provides:
- Declarative pipeline definitions
- Built-in expectations (data quality)
- Automatic lineage tracking
- Managed cluster lifecycle
- Incremental processing via `APPLY CHANGES INTO`

**Trade-offs:**
- DLT has its own pricing model (DBU premium)
- Less control over execution details
- Lock-in to Databricks-specific API
- The current notebook approach is more portable and easier to test locally

**When:** After batch ETL is production-stable and the team needs lineage or
built-in quality gates.

---

### 6. Schema Evolution Handling

**Current state:** `overwriteSchema` is used, which drops and recreates the table
schema on every write. This is acceptable for the mock platform but risky in production.

**Recommendation:** Define a schema evolution policy:
- **Additive changes** (new columns): use `mergeSchema` instead of `overwriteSchema`
- **Breaking changes** (column renames, type changes): require explicit migration
  notebooks with versioned schema definitions
- **Monitoring:** alert when schema changes are detected (compare pre/post write schemas)

**When:** Before production use with downstream consumers.

---

### 7. Deterministic Deduplication

**Current state:** `clean_orders()` uses `dropDuplicates(["order_id"])` which keeps an
arbitrary row when duplicates exist. Spark's `dropDuplicates` makes no ordering guarantee.

**Recommendation:** If deterministic dedup matters, replace with a Window function:
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.partitionBy("order_id").orderBy(col("order_date").desc())
df = df.withColumn("_rn", row_number().over(window)).filter("_rn = 1").drop("_rn")
```

This keeps the most recent record by `order_date`. The ordering column should match
the business requirement (e.g., ingestion timestamp if available).

**When:** When bronze data actually contains duplicates with different values, or
when audit requirements demand deterministic behavior.

---

## Relationship to Other Proposals

| Proposal | Connection |
|----------|------------|
| [etl-overwrite-pattern.md](etl-overwrite-pattern.md) | Items 2 and 6 extend the overwrite discussion |
| [etl-short-term-improvements.md](etl-short-term-improvements.md) | Short-term items from the same review |
| [testing-strategy.md](testing-strategy.md) | Item 1 (data quality) extends testing beyond E2E |
| ADR-006 (pending, refs #126) | Items 2 and 6 should be considered when writing ADR-006 |
