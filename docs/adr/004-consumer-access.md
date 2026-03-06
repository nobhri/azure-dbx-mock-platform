# ADR-004: Data Consumer Workspace — Access Pattern Options

**Status:** Accepted
**Date:** 2026-02-01

---

## Context

Data consumers (business teams, analysts, BI tools) need access to production data but should not
operate directly inside the platform prod workspace. Three isolation patterns are available in Unity
Catalog:

| Pattern                                    | Lineage visibility   | Cost                       | Complexity |
|--------------------------------------------|----------------------|----------------------------|------------|
| Direct access to prod catalog              | Full                 | Low                        | Low        |
| View layer in consumer catalog             | Partial (abstracted) | Low                        | Medium     |
| Materialized View layer in consumer catalog| None (fully isolated)| High (compute for refresh) | High       |

---

## Decision

Default to **View layer in a dedicated consumer catalog**.

Data consumers get a consumer workspace with its own catalog. The consumer catalog contains Views
that point to tables in the platform prod catalog. Consumers never have direct access to the platform
prod workspace or its compute.

Direct prod catalog access and full Materialized View isolation remain available as options for
specific datasets where governance requirements justify the trade-off.

---

## Rationale

**Why not direct prod access?**
Direct access is the simplest option but creates tight coupling between platform internals and
consumer access patterns. Schema changes in the platform catalog immediately affect consumers with
no abstraction layer. Access control is harder to audit: who can read which table in prod?

**Why not Materialized Views by default?**
Materialized Views provide the strongest isolation (consumers query a copy, not the live table) and
the cleanest lineage boundary. However, they require compute to refresh, which adds continuous cost
and operational complexity. For the MVP with a small number of datasets, this cost is not justified.

**Why View layer?**
Views provide a clean abstraction boundary: the platform team owns what's in the prod catalog; the
View definitions in the consumer catalog specify what consumers can see. Schema changes in upstream
tables require View updates, but only for Views that surface the changed column — not a blanket
re-deployment. Access audit is straightforward: list Views in consumer catalog, check grants.

---

## Trade-offs Accepted

- Views add a maintenance surface: when upstream schemas change, Views must be updated.
- Lineage in Unity Catalog is partial: the View is the lineage endpoint from the consumer's
  perspective; upstream table lineage is visible only to platform team users with prod catalog access.
- Materialized Views are explicitly reserved for cases where query performance or strict lineage
  isolation is required — not the default.

---

## Consequences

- Consumer workspace gets its own catalog, managed separately from the platform catalog.
- The platform team owns View definitions and is responsible for updating them when upstream
  schemas change.
- Consumers cannot accidentally modify platform prod data (Views are read-only by nature).
- Adding a new dataset for consumers requires adding a View — a low-friction operation within the
  existing Jinja2 + SQL DDL workflow.
