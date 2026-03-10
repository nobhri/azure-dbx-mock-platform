# Proposal: Data Engineering Implementation Plan

**Status:** Accepted — Phase 2 data engineering
**Date:** 2026-03-10
**Layer:** Data Engineering
**Related proposals:** etl-overwrite-pattern, testing-strategy, code-design-transform-separation, sdlc-catalog-lookup, wheel-packaging
**Related ADRs:** ADR-001, ADR-003; ADR-006 and ADR-007 candidates

---

## Purpose

This proposal consolidates the five accepted data engineering proposals into a single
implementation plan. It resolves open questions (data domain, medallion scope, wheel contents,
test execution, dependency order, data generation) that the individual proposals deferred to
implementation time.

---

## Resolved Decisions

### 1. Data Domain: Sales Orders

Single entity — **Sales Orders**.

| Column | Type | Notes |
|--------|------|-------|
| `order_id` | STRING | Primary key |
| `customer_id` | STRING | |
| `product_id` | STRING | |
| `quantity` | INT | |
| `unit_price` | DECIMAL | |
| `order_date` | DATE | |
| `region` | STRING | |

**Rationale:** Universally understood by any portfolio reviewer. No domain expertise needed.
Naturally demonstrates all 3 medallion layers without excessive schema complexity.

---

### 2. Medallion Architecture: Full 3-Layer

All three layers are in scope.

| Layer | Purpose | Key transforms |
|-------|---------|---------------|
| Bronze | Raw ingestion — stored as-is | CSV load or Faker-generated records; no transformation |
| Silver | Cleaned and typed | Type casting, null handling, deduplication on `order_id` |
| Gold | Aggregated for consumption | `daily_sales_by_region` — SUM revenue (`quantity * unit_price`), COUNT orders |

Each transition (bronze→silver, silver→gold) has a dedicated transform function in
`transform.py`, testable independently.

---

### 3. Catalog Lookup: Single `mock` Catalog

The SDLC catalog lookup function resolves environment to catalog name. In the current mock
environment, all targets return `mock`.

```python
# catalog_lookup.py
def get_catalog(env: str) -> str:
    """Resolve environment name to Unity Catalog catalog name."""
    catalog_map = {"dev": "mock", "prod": "mock"}
    ...
```

**Design intent:** The function exists to demonstrate the SDLC pattern. When the platform
scales to multi-catalog (e.g., `mock_dev`, `mock_prod`), only the config changes — pipeline
code remains unchanged. See `docs/design/platform-layer.md` §S1 for the production gap
documentation.

---

### 4. Wheel Package Contents

The wheel (`mock_platform`) includes production code only.

```
src/mock_platform/
    __init__.py
    transform.py         # pure PySpark transformations (no I/O)
    catalog_lookup.py    # SDLC env→catalog resolution
```

| Module | In wheel | Rationale |
|--------|----------|-----------|
| `transform.py` | Yes | Core business logic; notebooks import via `from mock_platform.transform import ...` |
| `catalog_lookup.py` | Yes | Cross-cutting SDLC concern; used by pipeline notebooks |
| `pipeline.py` (notebook) | No | Orchestration + I/O (`saveAsTable`); entry point that imports from the wheel |
| Faker data generators | No | Test-only; declared as job-level dependency (see §7) |

---

### 5. Test Execution Environments

| Test type | Where | What | Cluster required |
|-----------|-------|------|-----------------|
| Unit tests (Option B) | GitHub Actions runner | PySpark local SparkSession; test `transform.py` functions | No |
| Schema validation (Option A) | Databricks cluster | Assert column names, types, nullable after pipeline run | Yes |
| E2E test | Databricks cluster | Faker→bronze→pipeline→validate gold output | Yes |

**Unit tests on GH Actions:** `pyspark` is installed as a test dependency in the runner.
Tests import from the source tree (or built wheel). No network, no cluster, no cost.

**E2E tests on Databricks:** Run as a separate job in `databricks.yml`. Faker generates
bronze data, pipeline runs silver→gold, assertions validate the output.

---

### 6. Implementation Order: 3 PRs

```
PR 1: Wheel scaffold + transforms + SDLC lookup + unit tests
│
│  pyproject.toml
│  src/mock_platform/__init__.py
│  src/mock_platform/transform.py
│  src/mock_platform/catalog_lookup.py
│  tests/unit/test_transform.py         (static fixtures, GH Actions)
│  tests/unit/test_catalog_lookup.py
│  .github/workflows/test-unit.yaml     (pytest on runner)
│
│  Depends on: nothing (pure Python, no cluster)
│
├──▶ PR 2: Pipeline notebook + E2E test + Asset Bundles config
│
│    etl/notebooks/pipeline.py           (imports from mock_platform wheel)
│    etl/notebooks/e2e_test.py           (Faker → bronze → pipeline → validate)
│    etl/databricks.yml                  (job definitions, wheel in libraries)
│    data/sample_orders.csv              (static seed for dev)
│
│    Depends on: PR 1 merged (wheel must exist for notebook imports)
│
└──▶ PR 3: ADR-006 + ADR-007
     docs/adr/006-overwrite-only.md
     docs/adr/007-wheel-packaging.md

     Depends on: PR 2 merged (documents implemented decisions)
```

**Why 3 PRs:** PR 1 is fully testable without a Databricks cluster. This validates core
logic in CI before introducing cluster-dependent work in PR 2. Each PR is independently
reviewable and mergeable.

---

### 7. Data Generation Strategy

| Context | Strategy | Source |
|---------|----------|--------|
| Unit tests (GH Actions) | Static fixtures | Hand-written Python dicts or small CSV in `tests/fixtures/` |
| E2E tests (Databricks) | Faker-generated | `faker` library, installed as job-level `pypi` dependency |
| Dev seed data | Static CSV | `data/sample_orders.csv` committed to repo |

**Faker is not in the production wheel.** It is declared only in the E2E test job's
`libraries` in `databricks.yml`:

```yaml
jobs:
  etl-pipeline:
    tasks:
      - task_key: run_pipeline
        libraries:
          - whl: ./dist/*.whl          # production wheel only

  etl-e2e-test:
    tasks:
      - task_key: generate_and_test
        libraries:
          - whl: ./dist/*.whl
          - pypi:
              package: faker           # test-only dependency
```

The Faker data generation logic lives in the E2E test notebook (`e2e_test.py`), not in
the wheel. The generation is simple (`fake.random_int()`, `fake.date_between()`, etc.)
and only runs in test context.

---

## Relationship to Existing Proposals

This proposal does not replace the five accepted proposals. It resolves the open questions
they deferred and adds the implementation sequence. The individual proposals remain the
authoritative source for their specific decisions and rationale:

| Proposal | What it owns | What this plan adds |
|----------|-------------|-------------------|
| etl-overwrite-pattern | Overwrite vs merge decision, ADR-006 candidate | Domain choice, medallion layer scope, data generation |
| testing-strategy | Option A/B/C decision, DDL testing approaches | Execution environments (GH Actions vs cluster), fixture strategy |
| code-design-transform-separation | transform/pipeline split rationale | Confirmation that transform.py goes in wheel |
| sdlc-catalog-lookup | Env→catalog lookup design | Single `mock` catalog for now; in-wheel placement |
| wheel-packaging | Wheel vs `%run` decision, ADR-007 candidate | Package contents, directory structure |
