# Proposals

Proposals are staged here before acceptance or rejection. Once acted on, a proposal is updated
in-place with a final status (`Closed` or `Rejected`) and remains for reference.

---

## Status Lifecycle

```
Proposed → Accepted → Closed      (implemented or superseded by a design doc / ADR)
                    → Superseded  (content absorbed into docs/design/ or docs/adr/)
                    → Rejected    (explicitly decided against)
```

| Status | Meaning |
|--------|---------|
| `Proposed` | Under consideration; not yet acted on |
| `Accepted` | Decision made; implementation in progress or planned |
| `Closed` | Fully implemented; kept for reference |
| `Superseded` | Content absorbed into a design doc or ADR; proposal kept as redirect |
| `Rejected` | Explicitly decided against; rationale documented in the file |

---

## All Proposals

### Docs/Process

| File | Title | Status | Date |
|------|-------|--------|------|
| [docs-restructure.md](docs-restructure.md) | docs/ Directory Restructure | Closed — implemented in PR #71 | 2026-03-06 |

### Platform / Cross-cutting

| File | Title | Status | Date |
|------|-------|--------|------|
| [production-considerations.md](production-considerations.md) | Production Considerations | Superseded — see `docs/design/platform-layer.md` | 2026-03-05 |

### Data Engineering

| File | Title | Status | Date |
|------|-------|--------|------|
| [etl-overwrite-pattern.md](etl-overwrite-pattern.md) | ETL Overwrite Pattern | Accepted — Phase 2 data engineering; ADR-006 candidate pending | 2026-03-05 |
| [testing-strategy.md](testing-strategy.md) | Testing Strategy | Accepted — Phase 2 data engineering | 2026-03-05 |
| [code-design-transform-separation.md](code-design-transform-separation.md) | Code Design — Transform/Pipeline Separation | Accepted — Phase 2 data engineering | 2026-03-05 |
| [sdlc-catalog-lookup.md](sdlc-catalog-lookup.md) | SDLC Catalog Lookup | Accepted — Phase 2 data engineering | 2026-03-05 |
| [wheel-packaging.md](wheel-packaging.md) | Wheel Packaging | Accepted — Phase 2 data engineering; ADR-007 candidate pending | 2026-03-05 |
| [data-engineering-implementation-plan.md](data-engineering-implementation-plan.md) | Data Engineering Implementation Plan | Accepted — consolidates open questions from 5 proposals above | 2026-03-10 |
