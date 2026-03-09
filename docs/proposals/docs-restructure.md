# Proposal: docs/ Directory Restructure

**Status:** Closed — implemented in PR #71
**Date:** 2026-03-06
**Layer:** Docs/Process
**Related ADRs:** none
**Author:** Claude Code (session docs/code-review-2026-03-06-update)

---

## Problem Statement

The `docs/` directory has grown organically through daily code-review sessions. Three problems have
materialized in practice:

1. **Naming collision** — Two sessions on 2026-03-06 both tried to write `code-review-2026-03-06.md`.
   The second session worked around it with an `-update` suffix (PRs #67 and #69), leaving an
   inconsistent naming convention with no collision prevention.

2. **Unclear taxonomy** — Code-review files mix RCA, issue status snapshots, activity audits, and
   architectural notes — all in one flat directory with no signal about content type.

3. **Redundant `gh` CLI calls** — Each Claude Code session re-fetches `gh issue list` to reconstruct
   state that could be pre-materialized in a single repo-visible file.

---

## Proposed Directory Tree

```
docs/
├── adr/                              # Architecture Decision Records (portfolio-readable)
│   ├── 001-terraform-scope.md
│   ├── 002-oidc-auth.md
│   ├── 003-idempotency.md
│   ├── 004-consumer-access.md
│   └── 005-group-permissions.md
├── design/                           # Tactical implementation decisions (not ADR-level)
│   └── catalog-ddl-layer.md          # renamed from design-decisions-catalog-ddl-layer.md
├── runbooks/                         # Operational step-by-step procedures
│   ├── destroy-recreate.md           # extracted from GETTING_STARTED.md
│   └── post-destroy-grants.md        # manual SQL grants required after recreate
├── sessions/                         # Per-session investigation notes
│   └── YYYY-MM-DD-NNN-slug.md        # NNN = sequence number; prevents parallel-session collisions
├── proposals/                        # Proposed changes (this file lives here)
│   └── docs-restructure.md
└── status.md                         # Pre-materialized issue/PR snapshot
```

---

## Rationale by Directory

### `adr/`

ADRs already exist as inline sections in `README.md` (ADR-001 through ADR-005). Extracting them to
individual files:

- Makes each ADR linkable and diffable independently.
- Lets hiring managers scan architectural decisions without reading the full README.
- Keeps `README.md` high-level — one-line reference + link per ADR, not full prose.
- ADRs are stable: written once, amended rarely. They are not session notes.

### `design/`

Tactical implementation decisions that are too detailed for an ADR but too stable for a session note.
`design-decisions-catalog-ddl-layer.md` already exists and fits here with a rename. New design notes
(e.g., bundle variable passing strategy, future OIDC rotation) go here when they stabilize beyond a
single session investigation.

### `runbooks/`

`GETTING_STARTED.md` currently mixes one-time setup steps (OIDC, secrets) with recurring operational
procedures (destroy/recreate, post-destroy grants). The recurring parts belong in runbooks:

- `destroy-recreate.md` — full destroy/recreate sequence from issue #19 comment and MEMORY.md.
- `post-destroy-grants.md` — the manual SQL grants (CREATE EXTERNAL LOCATION, CREATE CATALOG) that
  must be re-applied after each full destroy. Currently spread across issues #19, #21, #53, and
  MEMORY.md.

GETTING_STARTED.md retains one-time setup only and links to `docs/runbooks/` for recurring procedures.

### `sessions/`

Replaces `code-review-YYYY-MM-DD.md` with a collision-safe naming scheme.

**Naming convention:** `sessions/YYYY-MM-DD-NNN-slug.md`

- `NNN` is a zero-padded 3-digit sequence number (001, 002, ...).
- Claude determines the next number by globbing `sessions/YYYY-MM-DD-*.md` at session start.
- Parallel worktrees starting at different times will naturally get different `NNN` values since
  directory state differs.
- Example: `sessions/2026-03-06-001-metastore-drift.md` and
  `sessions/2026-03-06-002-catalog-fix-chain.md`.

Session files contain: investigation notes, RCA, what was tried and why, links to issues and PRs.
They do **not** restate issue status (that lives in `status.md` and GitHub Issues).

### `proposals/`

A staging area for proposed structural or process changes before they are merged or acted on.
Avoids mixing "here is what we decided" (ADRs) with "here is what we are considering" (proposals).
Once a proposal is acted on, it can be archived in-place with a status update at the top.

### `status.md`

A single pre-materialized snapshot of open issues with severity, last known good state, and pending
human actions.

- Updated at the end of each docs PR as a standard step.
- Replaces ad-hoc issue status tables scattered inside session files.
- Claude reads `status.md` at session start instead of running `gh issue list` — zero `gh` API
  calls for context bootstrap.
- Content mirrors what is already tracked in `MEMORY.md` issue table but is repo-visible (no
  user-local Claude memory required).

---

## Decision Boundary

| Information type                        | Lives in           | Not in               |
|-----------------------------------------|--------------------|----------------------|
| Architectural rationale (why Terraform) | `adr/`             | README inline prose  |
| Tactical implementation decisions       | `design/`          | Sessions             |
| Recurring operational procedures        | `runbooks/`        | GETTING_STARTED.md   |
| Per-session investigation / RCA         | `sessions/`        | Issues/PRs           |
| Bug tracking, fix review, PR threads    | GitHub Issues/PRs  | Any local file       |
| Current open issue snapshot             | `status.md`        | Session files        |
| One-time setup (OIDC, secrets)          | GETTING_STARTED.md | Runbooks             |
| Project conventions for Claude          | CLAUDE.md          | Any docs/ file       |

---

## Migration of Existing Files

All migrations are rename-only (`git mv`). File contents are preserved.

| Old path                                     | New path                                           |
|----------------------------------------------|----------------------------------------------------|
| `docs/code-review-2026-03-02.md`             | `docs/sessions/2026-03-02-001-initial-review.md`   |
| `docs/code-review-2026-03-03.md`             | `docs/sessions/2026-03-03-001-post-pr-batch.md`    |
| `docs/code-review-2026-03-04.md`             | `docs/sessions/2026-03-04-001-destroy-bool-fix.md` |
| `docs/code-review-2026-03-05.md`             | `docs/sessions/2026-03-05-001-activity-audit.md`   |
| `docs/code-review-2026-03-06.md`             | `docs/sessions/2026-03-06-001-metastore-drift.md`  |
| `docs/code-review-2026-03-06-update.md`      | `docs/sessions/2026-03-06-002-catalog-fix-chain.md`|
| `docs/design-decisions-catalog-ddl-layer.md` | `docs/design/catalog-ddl-layer.md`                 |

---

## Implementation Steps

When this proposal is approved, execute in order:

1. Create new directories: `docs/adr/`, `docs/design/`, `docs/runbooks/`, `docs/sessions/`.
2. Rename existing files using `git mv` per the migration table above.
3. Extract ADR-001 through ADR-005 from `README.md` into `docs/adr/001-*.md` through
   `docs/adr/005-*.md`; replace inline ADR prose in README with one-line references and links.
4. Write `docs/status.md` with current issue snapshot (mirrors MEMORY.md issue table, but
   repo-visible).
5. Extract destroy/recreate procedure from `GETTING_STARTED.md` into
   `docs/runbooks/destroy-recreate.md` and `docs/runbooks/post-destroy-grants.md`; leave
   "see runbooks/" references in GETTING_STARTED.md.
6. Update `CLAUDE.md` to note the new session naming convention and `status.md` as session-start
   reference.
7. Update `MEMORY.md` to note new session naming convention.

---

## Verification Checklist

- [x] `ls docs/` shows new subdirectory structure (`adr/`, `design/`, `runbooks/`, `sessions/`, `proposals/`)
- [x] `git log --oneline --name-status` shows renames (R100), not deletions + additions, for migrated files
- [x] `docs/proposals/docs-restructure.md` exists and is readable standalone
- [x] `docs/status.md` reflects current open issues and pending human actions
- [x] `README.md` ADR section links to `docs/adr/` files and still renders correctly
- [x] `GETTING_STARTED.md` destroy section links to `docs/runbooks/destroy-recreate.md`
- [x] `CLAUDE.md` updated with session naming convention
- [x] `MEMORY.md` updated with session naming convention note
