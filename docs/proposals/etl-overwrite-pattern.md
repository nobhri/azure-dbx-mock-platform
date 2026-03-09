# Proposal: ETL Overwrite Pattern

**Status:** Proposed
**Date:** 2026-03-05
**Layer:** Data Engineering
**Related ADRs:** ADR-003 (idempotency)

---

## Decision

`saveAsTable` with `mode("overwrite")` only. Merge pattern is deferred.

| Parameter | Value |
|-----------|-------|
| Table persistence | `saveAsTable` (`mode("overwrite")`) |
| Merge / upsert | Deferred — see ADR-006 candidate below |
| ETL count | 1 notebook (dim-table-equivalent overwrite) |
| Idempotency | Guaranteed automatically by overwrite — consistent with ADR-003 |

## Rationale

- Overwrite alone achieves idempotency naturally and keeps test logic simple.
- The conditions under which merge becomes necessary (fact tables, incremental loads, SCD Type 2)
  and the design changes required are documented in the ADR-006 candidate section below, which
  demonstrates architectural thinking without requiring implementation.

---

## Sample ETL Domain

**Decision:** Manufacturing domain (1–2 entities). Domain TBD at implementation time.

**Candidate entities:** Sales Orders, Production, Payments, Inventory.

**Design constraints:**
- No real company data — general manufacturing domain model only.
- 1–2 entities maximum; complexity should serve the ETL design, not the domain model.
- Sample data generation: hand-written CSV or Faker (decide at implementation time).
- Medallion architecture (bronze → silver → gold): show one layer transition at minimum; full
  three-layer medallion is optional.

---

## Implementation Notes

**Batch 1** (merge first into main):
- ETL notebook (`saveAsTable` overwrite)
- Option A tests (schema validation)
- Option B tests (transform unit tests)
- `transform.py` / `pipeline.py` separation

---

## Deferred Items

| Item | Notes |
|------|-------|
| Merge ETL (fact table) | Documented in ADR-006 candidate; implement when an incremental-load use case is added |
| Delta Live Tables | Evaluate after batch ETL pattern is stable |
| Structured Streaming / Auto Loader | Batch first; streaming as a named extension once the batch layer is proven |

---

## ADR-006 Candidate: Why the merge pattern is deferred

**Not yet written** — candidate for the data engineering phase.

Proposed contents:
- Conditions under which merge becomes necessary (fact tables, incremental loads, SCD Type 2,
  late-arriving data)
- Design changes required when merge is introduced (`DeltaTable.merge()`, dedupe logic,
  late-arrival handling)
- Rationale for overwrite-only in this implementation
