# Session 2026-03-12-002 — issue-53-getting-started

**Branch:** docs/2026-03-12-002-issue-53-getting-started
**Issue:** #53
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Document the `GRANT CREATE CATALOG ON METASTORE` prerequisite in `GETTING_STARTED.md`.
The `post-destroy-grants.md` runbook already covers both grants (CREATE EXTERNAL LOCATION and
CREATE CATALOG) in Step 1. The gap is in `GETTING_STARTED.md`: no mention of the manual grants
required between `workload-dbx` apply and `workload-catalog` apply.

## What was done

- Added a "Step 4.5 — Manual Grants" subsection to Deployment Steps in GETTING_STARTED.md,
  calling out both SP grants with a link to the runbook.
- Added a Common Pitfalls entry for `workload-catalog` failing when `CREATE CATALOG` grant is missing.
- Updated the existing `workload-dbx` pitfall entry to reference both grants together.

## Decisions

- Kept runbook as the canonical source; GETTING_STARTED.md links to it rather than duplicating SQL.

## Artifacts

- `GETTING_STARTED.md` — updated Deployment Steps and Common Pitfalls
- PR opened (see PR field above)
