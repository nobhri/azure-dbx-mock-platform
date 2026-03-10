# Session Notes

This directory contains per-session working notes created during development of the Databricks Mock Platform.

## Purpose

Each file records what was decided, attempted, or discovered in a single working session. They are **not polished documentation** — they are an honest log of the work as it happened, including dead ends and course corrections.

For external readers, session notes show:
- How architectural decisions evolved over time
- The reasoning behind mid-session pivots
- What problems were encountered and how they were resolved

## Naming Convention

```
YYYY-MM-DD-NNN-slug.md
```

- `YYYY-MM-DD` — date of the session
- `NNN` — zero-padded 3-digit sequence within that date (001, 002, ...)
- `slug` — short description of the session's focus

**Example:** `2026-03-06-007-issue-80-dynamic-metastore-import.md`

**Determining NNN:** Before creating a session file, glob `docs/sessions/YYYY-MM-DD-*.md` to find the highest existing NNN for today, then increment by one. Start at 001 if none exist.

**Uniqueness:** Each session must have a unique NNN. When multiple sessions run in parallel on the same date, the branch name should include the NNN (e.g., `docs/2026-03-10-009-slug`) to surface conflicts early.

## Standard Template

Every session file must use this structure:

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

## Relationship to Other Docs

| Document | Purpose |
|----------|---------|
| [`docs/status.md`](../status.md) | Live snapshot of open issues and architecture state |
| [`docs/adr/`](../adr/) | Durable architectural decisions (ADRs) |
| `docs/sessions/` | Working notes — context behind decisions, not the decisions themselves |

Session notes inform ADRs, not the other way around. If a session note leads to a stable decision, that decision is captured in an ADR or runbook.
