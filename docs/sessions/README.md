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
- `NNN` — zero-padded sequence within that date (001, 002, ...)
- `slug` — short description of the session's focus

**Example:** `2026-03-06-007-issue-80-dynamic-metastore-import.md`

## Relationship to Other Docs

| Document | Purpose |
|----------|---------|
| [`docs/status.md`](../status.md) | Live snapshot of open issues and architecture state |
| [`docs/adr/`](../adr/) | Durable architectural decisions (ADRs) |
| `docs/sessions/` | Working notes — context behind decisions, not the decisions themselves |

Session notes inform ADRs, not the other way around. If a session note leads to a stable decision, that decision is captured in an ADR or runbook.
