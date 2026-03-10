# Proposal: Wheel Packaging

**Status:** Accepted — Phase 2 data engineering; ADR-007 candidate pending
**Date:** 2026-03-05
**Layer:** Data Engineering

---

## Decision

Wheel packaging via `pyproject.toml`, distributed via Asset Bundles `libraries`.

| Approach | Decision |
|----------|----------|
| Wheel (`pyproject.toml` or `setup.py`) + Asset Bundles `libraries` | ✅ Adopted |
| `%run` / naive relative imports | ❌ Rejected — documented in ADR-007 candidate below |

## Rationale

- `%run` and naive relative imports cause path-resolution failures in real cluster deployments and
  are a known anti-pattern.
- Wheel + Asset Bundles `libraries` integrates cleanly with the existing CI/CD structure.
- The wheel build and distribution steps extend CI/CD coverage further up the stack.

---

## Implementation Notes

**Batch 2** (separate PR from ETL/testing Batch 1):
- `pyproject.toml` wheel build
- Asset Bundles `libraries` configuration referencing the built wheel

---

## ADR-007 Candidate: Why wheel packaging over `%run`

**Not yet written** — candidate for the data engineering phase.

Proposed contents:
- Path-resolution failures caused by `%run` and naive relative imports on Databricks clusters
- Trade-offs of wheel packaging (additional build CI/CD step)
- Integration design with Asset Bundles `libraries`
