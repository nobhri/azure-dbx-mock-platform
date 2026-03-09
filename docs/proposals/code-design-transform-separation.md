# Proposal: Code Design — Transform/Pipeline Separation

**Status:** Proposed
**Date:** 2026-03-05
**Layer:** Data Engineering

---

## Decision

Separate transform logic (`transform.py`) from persistence (`pipeline.py`) at the function level.
Tests target only the transform layer.

```
transform.py   — pure PySpark transformation functions (no I/O)
pipeline.py    — orchestration + saveAsTable calls
```

**Test scope:** `transform.py` functions only (up to, but not including, `saveAsTable`).

## Rationale

- Separating transform from persistence makes the transform layer unit-testable without a running
  cluster.
- The separation pattern itself is documented as an ADR — the design decision is the artifact, not
  just the code.

---

## Implementation Notes

**Batch 1** (merge first into main):
- `transform.py` / `pipeline.py` separation
- Option B tests (PySpark unit tests targeting `transform.py`)
