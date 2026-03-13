# Session 2026-03-13-001 — readme-status-cleanup

**Branch:** docs/2026-03-13-001-readme-status-cleanup
**Issue:** #105 (related: docs cleanup)
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Clean up and update documentation:
1. Check open issues on GitHub and reconcile with status.md
2. Update Known Issues section of README.md (remove closed issues, update stale entries)
3. Remove or replace the "Deploying Yourself" section in README.md with a link to GETTING_STARTED.md
4. Update docs/status.md to reflect current issue and PR state

## What was done

- Checked GitHub issues: only 3 open (#82, #11, #163)
- Many issues listed as open in status.md were actually closed (most on 2026-03-11 and 2026-03-12)
- Both open PRs in status.md (#159, #165) were already merged
- Updated README.md Known Issues: removed closed #40 entry, removed "Deploying Yourself" section, updated #53 reference
- Updated docs/status.md: removed all closed issues from Open Issues, added #163, cleared Open PRs, moved closed items to Recently Closed

## Decisions

- "Deploying Yourself" bullet removed entirely from Known Issues — it is not a known issue but a setup prerequisite, and GETTING_STARTED.md is the authoritative source
- Post-destroy manual grants bullet retained (still a real operational constraint) but #53 reference removed since that issue is closed

## Artifacts

- `README.md` — Known Issues section updated
- `docs/status.md` — Open Issues, Open PRs, Recently Closed updated
