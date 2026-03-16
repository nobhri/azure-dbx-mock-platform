# Session 2026-03-16-001 — claude-config

**Branch:** feature/2026-03-16-001-claude-config
**Issue:** N/A
**PR:** (fill in when created)
**Outcome:** in-progress

## Objective
Add Claude Code configuration to the repository: CLAUDE.md new sections, settings.local.json permissions + deny list + Stop hook, ruff linting in CI/CD, skills (adr-workflow, pre-impl-check, watch-ci, session-log), and docs/sessions/.gitkeep.

## What was done
(to be filled in)

## Decisions
- `Edit` and `Write` added explicitly to allow in settings.local.json for self-documentation
- settings.json (committed) keeps shared read-only ops; settings.local.json (gitignored) holds write ops, deny list, and hooks
- settings.local.json.example updated to mirror settings.local.json

## Artifacts
- `CLAUDE.md` — 4 new sections appended
- `.claude/settings.local.json` — replaced with full permissions + deny + Stop hook
- `.claude/settings.local.json.example` — updated to match settings.local.json
- `etl/pyproject.toml` — added [tool.ruff] and [tool.ruff.lint]
- `.github/workflows/workload-etl.yaml` — added lint job before deploy
- `.claude/skills/adr-workflow/SKILL.md`
- `.claude/skills/pre-impl-check/SKILL.md`
- `.claude/skills/watch-ci/SKILL.md`
- `.claude/skills/session-log/SKILL.md`
- `docs/sessions/.gitkeep`
