# Session 2026-03-13-002 — claude-autonomy

**Branch:** docs/2026-03-13-002-claude-autonomy
**Issue:** n/a
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Improve Claude Code autonomy: expand `settings.local.json` allowed tools and update CLAUDE.md to reflect the correct autonomy level and conflict-prevention workflow.

## What was done

- Updated `.claude/settings.local.json` (local, untracked) to auto-approve all routine git operations and gh read-only commands; removed overly broad `gh issue:*` entry
- Updated CLAUDE.md Autonomy Level section to clearly distinguish auto-approved operations from confirmation-required ones
- Updated Session Start Checklist step 3 to always fetch and branch from `origin/main`
- Added Common Mistakes entry for branching from stale HEAD

## Decisions

- `gh pr create` and `gh issue create` remain confirmation-required — these create visible external artifacts
- `gh workflow run` remains forbidden — CI/CD triggers are human-only
- `settings.local.json` is the right place for allow rules (local, untracked); `settings.json` is not used to avoid committing trust settings

## Artifacts

- `.claude/settings.local.json` — expanded allow list (direct edit, not in PR)
- `CLAUDE.md` — autonomy and Session Start Checklist updated
- `docs/sessions/2026-03-13-002-claude-autonomy.md` — this file
