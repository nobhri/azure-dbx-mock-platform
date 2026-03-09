# Proposal: SDLC Catalog Lookup

**Status:** Proposed
**Date:** 2026-03-05
**Layer:** Data Engineering
**Related ADRs:** ADR-001 (Terraform scope)

---

## Decision

Implement a single environment-to-catalog lookup function driven by a YAML config file.

| Parameter | Value |
|-----------|-------|
| Scope | 1 function: resolve catalog name from environment |
| Config format | YAML (`environments.<env>.catalog`) |
| Integration | Asset Bundles target variable → env → catalog name |

## Rationale

- Avoids hardcoding environment-specific catalog names in notebooks or pipelines.
- Connecting Asset Bundles target variables to catalog resolution demonstrates end-to-end pipeline
  design consistency.

---

## Platform Layer Status (updated 2026-03-09)

The platform layer is now complete. Catalog, schema, groups, and GRANTs are live as of 2026-03-09
(workload-catalog last successful run: 2026-03-08). References to the catalog/schema infrastructure
as future work are no longer accurate — it is available now.

This means:
- The SDLC lookup function can be implemented and tested against the real `dev` catalog immediately.
- Environment-to-catalog mapping (`dev` → catalog `dev`, etc.) is already realized by the Jinja2
  DDL layer; the lookup function connects pipelines to this existing structure.

---

## Implementation Notes

**Batch 2** (separate PR from ETL/testing Batch 1):
- Common functions (SDLC catalog lookup)
- YAML config file (`environments.<env>.catalog`)
- Integration with Asset Bundles target variable
