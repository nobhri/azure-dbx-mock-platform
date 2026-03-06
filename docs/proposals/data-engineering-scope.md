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

---

## 10. Production Considerations and ADR Candidates

These items are **not implemented in this mock** but are documented here as known simplifications.
Each represents a gap between the mock design and a production-grade platform that should be
captured in an ADR or production runbook before any real deployment.

---

### 10.1 Single Workspace vs Dedicated Workspace per Environment

**Mock design:** One workspace. Environment isolation is achieved by switching the Asset Bundles
target variable (`dev` / `staging` / `prod`), which maps to different catalog names via the SDLC
lookup function (see Section 4).

**Production reality:** Dedicated workspace per environment (dev / staging / prod). Each workspace
has its own identity boundary, network configuration, and catalog binding. Workspace-level RBAC
and governance are cleanly separated.

**Why single workspace is an intentional simplification:**
- Provisioning and maintaining three workspaces multiplies Azure cost and CI/CD complexity.
- For a portfolio mock, demonstrating the SDLC pattern (catalog switching via Asset Bundles target)
  is sufficient to show the design intent.
- The single-workspace design does not prevent later migration: catalog naming conventions and the
  SDLC lookup function are already environment-aware.

**ADR candidate:** Document the single-workspace trade-off and the migration path to per-environment
workspaces when the platform scales beyond a single team.

---

### 10.2 System Tables for Catalog / Schema Change Tracking

**Current state:** DDL is idempotent (`CREATE IF NOT EXISTS`). Deletions are not detected at apply
time — explicitly accepted in ADR-001 as an MVP trade-off ("DDL `IF NOT EXISTS` is idempotent but
will not detect deletions").

**When system tables become relevant:** Once the Jinja2 catalog/schema management layer is in place
and schemas are being modified over time (column additions, type changes, object drops), audit-level
tracking becomes necessary for:
- Detecting drift between the declared DDL and the actual UC state
- Auditing who changed what and when (compliance, incident response)
- Triggering alerts when unexpected schema changes occur

**Enablement conditions:**
- System tables must be enabled at the account level: `system.access`, `system.information_schema`
- Requires Unity Catalog metastore (already in place)
- Requires a scheduled job or CI/CD step that queries `system.information_schema.columns` and
  compares against the expected schema from the Jinja2 templates

**ADR candidate:** Document drift detection approach (system table query vs Terraform plan vs
application-level assertion) and the enablement prerequisites.

---

### 10.3 Infra / Platform Repo Separation and Cross-Repo Output Passing

**Current state:** Single repository. `workload-azure` and `workload-dbx` run as separate GitHub
Actions workflows in the same repo. Outputs from `workload-azure` (e.g., storage account name,
workspace URL) are available to `workload-dbx` via Terraform remote state stored in the shared
Azure Storage backend.

**Production reality:** Infrastructure (Azure resources) and platform (Databricks configuration,
Unity Catalog) are often owned by different teams and live in separate repositories. Cross-repo
output passing is a non-trivial design problem:

| Mechanism | Trade-offs |
|-----------|-----------|
| Shared Terraform remote state | Both repos must have read access to the same backend; tight coupling at the state layer |
| GitHub Secrets / Variables (manual) | Requires human update after each infra apply; error-prone |
| Cross-repo GitHub Actions triggers with output artifacts | Complex workflow orchestration; artifact lifetime management |
| Published artifact / API endpoint | Most decoupled; highest implementation cost |

**Relationship to ADR-001:** ADR-001 defines the Terraform responsibility boundary (Azure + Metastore
= Terraform, Catalog/Schema = SQL). Repo separation is the organizational consequence of that
boundary: once the boundary is firm, each side can be owned and deployed independently. The output-
passing problem only arises when the repos split.

**ADR candidate:** Document which cross-repo output mechanism to adopt if repos are split, and the
conditions under which a split is warranted (team size, change velocity, security isolation
requirements).

---

### 10.4 Single Service Principal vs Separated SP per Layer

**Current state:** One Service Principal handles all CI/CD operations: Azure resource provisioning
(Terraform), Databricks workspace configuration (Terraform), and Databricks job execution (Asset
Bundles + SQL notebook).

**Production reality:** Least-privilege design separates concerns:

| SP | Scope |
|----|-------|
| Infra SP | Azure RBAC (Contributor on RG, Storage Blob Data Contributor) |
| Platform SP | Databricks workspace admin, Unity Catalog grants |
| Data SP | Job execution, catalog read/write only |

**The trade-off this creates (coupled with 10.3):**
- With a single SP and single repo, Terraform remote state is readable by both the infra and
  platform workflows under the same identity — output passing is free.
- With separated SPs and separate repos, the infra SP's outputs are no longer directly accessible
  to the platform SP. An explicit output-passing mechanism (see 10.3) is required.
- Separating SPs also requires separate federated credential configurations in Entra ID and
  separate GitHub secret sets.

**ADR candidate:** Document the single-SP trade-off and the separation design when moving toward
production. Reference the repo-separation ADR candidate in 10.3 — these two decisions are coupled
and should be resolved together.

---

### 10.5 DDL Testing Approaches

*Extends the future work items in Section 8.*

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
