---
name: session-log
description: Use after completing a task to write a session log
disable-model-invocation: true
---

## Session Log

Save path: `docs/sessions/YYYY-MM-DD-NNN-<slug>.md`

Determine NNN by globbing `docs/sessions/YYYY-MM-DD-*.md` for today and incrementing the highest existing number (start at 001 if none exist).

### Template

```markdown
# Session YYYY-MM-DD-NNN — <slug>

**Branch:** <branch-name>
**Issue:** #<number> (omit if not applicable)
**PR:** #<number> (fill in when created; omit until then)
**Outcome:** completed | partial | blocked

## Objective
What we set out to do.

## What was done
Summary of actions taken.

## Decisions
Any choices made and rationale. Omit this section if no decisions were made.

## Lessons / Notes
Insights for future sessions. Omit this section if nothing notable.

## Artifacts
- Files changed, issues created, PRs opened
```

**Rules:**
- Fill in **Outcome** and **Artifacts** before ending the session
- Update `docs/status.md` if any issues were opened, closed, or changed severity
