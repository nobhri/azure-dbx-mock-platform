# Session: 2026-03-10-003 — Extract Production Considerations (#108)

**Date:** 2026-03-10
**Branch:** docs/prod-considerations-108
**Issue:** refs #108

## What was done

- Created `docs/design/production-considerations.md` with the full content previously in the
  README "Production Considerations" section (Network Isolation, Storage Account Architecture,
  Serverless Compute & NCC).
- Replaced the verbose README section with a 4-line summary and a link to the new design doc.

## Why

The README "Production Considerations" section was ~70 lines of detail that made the README
harder to skim. Design-level detail belongs in `docs/design/`, alongside `platform-layer.md`.
The README now provides a summary and directs readers to the full doc.

## Files changed

- `docs/design/production-considerations.md` — new file (extracted content)
- `README.md` — Production Considerations section replaced with summary + link
