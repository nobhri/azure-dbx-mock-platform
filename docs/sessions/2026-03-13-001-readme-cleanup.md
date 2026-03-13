# Session 2026-03-13-001 — readme-cleanup

**Branch:** docs/2026-03-13-001-readme-cleanup
**Issue:** #105, #106
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Review and clean up README.md and GETTING_STARTED.md for public portfolio presentation targeting hiring managers at Enterprise Data Platform / Big Tech platform teams.

## What was done

- Fixed empty LinkedIn URL in README Author section
- Removed stale "In Progress: README finalization" from Current Status
- Collapsed Known Issues section in README — moved operational content behind links to GETTING_STARTED and runbooks
- Updated GETTING_STARTED.md repository structure and workflow list to match current state
- Fixed broken `#orphaned-uc-objects-recovery` anchor in GETTING_STARTED Common Pitfalls

## Decisions

- Known Issues in README reduced to one-sentence pointer to GETTING_STARTED/runbooks — operational detail belongs in GETTING_STARTED, not the architecture overview
- "Deploying this yourself" content moved out of Known Issues into Current Status as a standalone note

## Artifacts

- `README.md` — LinkedIn fix, Known Issues collapsed, stale In Progress removed
- `GETTING_STARTED.md` — repo structure updated, broken anchor fixed
- `docs/status.md` — issue #105 closed
