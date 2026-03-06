# Proposal: Data Engineering Implementation Scope

> Scope decisions for the ETL, testing, common functions, and packaging layers.
> Decided: 2026-03-05

---

## 1. ETL Implementation

**Decision:** `saveAsTable` with `mode("overwrite")` only. Merge pattern is deferred.

| Parameter | Value |
|-----------|-------|
| Table persistence | `saveAsTable` (`mode("overwrite")`) |
| Merge / upsert | Deferred — see ADR-006 |
| ETL count | 1 notebook (dim-table-equivalent overwrite) |
| Idempotency | Guaranteed automatically by overwrite — consistent with ADR-003 |

**Rationale:**
- Overwrite alone achieves idempotency naturally and keeps test logic simple.
- The conditions under which merge becomes necessary (fact tables, incremental loads, SCD Type 2) and the design changes required are documented in ADR-006, which itself demonstrates architectural thinking without requiring implementation.

---

## 2. Testing

**Decision:** Implement Option A (schema validation) and Option B (unit tests for transform logic). DuckDB is deferred.

| Option | Decision |
|--------|----------|
| A — Schema validation (column names, types, nullable assertions) | ✅ Implement |
| B — PySpark transform unit tests (local SparkSession) | ✅ Implement |
| C — DuckDB SQL unit tests | Deferred — documented as future work |

**Rationale:**
- Option A alone is too thin to demonstrate test design skill.
- Option B is a natural fit for a `saveAsTable`-based ETL because the test boundary (transform function input/output) is clean and does not require a live cluster.
- DuckDB (Option C) would create a mismatch: the pipeline uses `saveAsTable`, not a SQL execution engine that DuckDB naturally targets. Deferred to a future iteration where it fits better.

---

## 3. Code Design Pattern

**Decision:** Separate transform logic (`transform.py`) from persistence (`pipeline.py`) at the function level. Tests target only the transform layer.

```
transform.py   — pure PySpark transformation functions (no I/O)
pipeline.py    — orchestration + saveAsTable calls
```

**Test scope:** `transform.py` functions only (up to, but not including, `saveAsTable`).

**Rationale:**
- Separating transform from persistence makes the transform layer unit-testable without a running cluster.
- The separation pattern itself is documented as an ADR — the design decision is the artifact, not just the code.

---

## 4. Common Functions (SDLC)

**Decision:** Implement a single environment-to-catalog lookup function driven by a YAML config file.

| Parameter | Value |
|-----------|-------|
| Scope | 1 function: resolve catalog name from environment |
| Config format | YAML (`environments.<env>.catalog`) |
| Integration | Asset Bundles target variable → env → catalog name |

**Rationale:**
- Avoids hardcoding environment-specific catalog names in notebooks or pipelines.
- Connecting Asset Bundles target variables to catalog resolution demonstrates end-to-end pipeline design consistency.

---

## 5. Packaging

**Decision:** Wheel packaging via `pyproject.toml`, distributed via Asset Bundles `libraries`.

| Approach | Decision |
|----------|----------|
| Wheel (`pyproject.toml` or `setup.py`) + Asset Bundles `libraries` | ✅ Adopted |
| `%run` / naive relative imports | ❌ Rejected — documented in ADR-007 |

**Rationale:**
- `%run` and naive relative imports cause path-resolution failures in real cluster deployments and are a known anti-pattern.
- Wheel + Asset Bundles `libraries` integrates cleanly with the existing CI/CD structure.
- The wheel build and distribution steps extend CI/CD coverage further up the stack.

---

## 6. Implementation Batches

**Batch 1** (merge first):
- ETL notebook (`saveAsTable` overwrite)
- Option A tests (schema validation)
- Option B tests (transform unit tests)
- `transform.py` / `pipeline.py` separation

**Batch 2** (separate PR):
- Common functions (SDLC catalog lookup)
- Wheel packaging (`pyproject.toml` + Asset Bundles libraries)

**Rationale:** Batch 2 introduces additional dependencies (build tooling, YAML config). Merging Batch 1 first distributes review load and keeps each PR reviewable independently.

---

## 7. ADR Candidates

### ADR-006: Why the merge pattern is deferred

Contents:
- Conditions under which merge becomes necessary (fact tables, incremental loads, SCD Type 2, late-arriving data)
- Design changes required when merge is introduced (`DeltaTable.merge()`, dedupe logic, late-arrival handling)
- Rationale for overwrite-only in this implementation

### ADR-007: Why wheel packaging over `%run`

Contents:
- Path-resolution failures caused by `%run` and naive relative imports on Databricks clusters
- Trade-offs of wheel packaging (additional build CI/CD step)
- Integration design with Asset Bundles `libraries`

---

## 8. Deferred and Out-of-Scope Items

### Out of scope — not implemented, documented for future work

| Item | Notes |
|------|-------|
| DuckDB SQL unit tests | Better fit when a SQL-centric pipeline exists; see Jinja2 DDL layer as a future candidate |
| Merge ETL (fact table) | Documented in ADR-006; implement when an incremental-load use case is added |
| Delta Live Tables | Evaluate after batch ETL pattern is stable |
| Structured Streaming / Auto Loader | Batch first; streaming as a named extension once the batch layer is proven |

### Dashboard layer — out of scope

Not implemented. When the need arises, the choice between the following should be treated as an explicit design decision:

| Tool | Fit |
|------|-----|
| AI/BI Dashboards | Self-service, exploratory; individual or team consumption |
| Asset Bundles / Lakeview as code | Org-wide KPIs, cross-team reporting; code review, versioning, and environment-specific deployment required |
| Databricks Apps | Interactive applications; input forms or workflow integration |

An ADR entry covering this trade-off belongs in the README Future Work section or as a standalone ADR when any dashboard work begins.

---

## 9. Sample ETL — Business Domain

**Decision:** Manufacturing domain (1–2 entities). Domain TBD at implementation time.

**Candidate entities:** Sales Orders, Production, Payments, Inventory.

**Design constraints:**
- No real company data — general manufacturing domain model only.
- 1–2 entities maximum; complexity should serve the ETL design, not the domain model.
- Sample data generation: hand-written CSV or Faker (decide at implementation time).
- Medallion architecture (bronze → silver → gold): show one layer transition at minimum; full three-layer medallion is optional.
