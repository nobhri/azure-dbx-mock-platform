# Session 2026-03-13-002 — runbook-grants-refactor

**Branch:** docs/2026-03-13-002-runbook-grants-refactor
**Issue:** #53, #106
**PR:** (fill in when created)
**Outcome:** completed

## Objective

- Rename `post-destroy-grants.md` to `initial-metastore-setup.md` and update content to reflect
  that these grants are one-time (tied to the Metastore, not the destroy cycle)
- Update GETTING_STARTED.md step 5 to link to the renamed runbook and remove misleading
  "re-run after every recreate" language
- Update "Destroy and Recreate" section in GETTING_STARTED.md to reference orchestrator workflows
  and remove the post-destroy-grants link
- Update `destroy-recreate.md` to document the orchestrator-up/down workflows and clarify that
  grants are not needed after a normal recreate

## What was done

1. Created `docs/runbooks/initial-metastore-setup.md` (renamed from `post-destroy-grants.md`):
   - New title and intro: one-time setup after first Metastore deploy
   - Added note that grants persist with the Metastore across destroy/recreate cycles
   - Preserved all existing content (SP grants, group creation options A/B, verification SQL)

2. Deleted `docs/runbooks/post-destroy-grants.md` (renamed to above)

3. Updated `GETTING_STARTED.md`:
   - Step 5 renamed to "Initial Metastore Setup (one-time)" with updated framing
   - Step 5 link updated to `initial-metastore-setup.md`
   - "Destroy and Recreate" subsection simplified: one runbook link, orchestrator note, no re-grant mention
   - Common Pitfalls links updated to new runbook filename
   - Also incorporated all PR #167 restructure changes (this branch is based on main)

4. Updated `docs/runbooks/destroy-recreate.md`:
   - Added orchestrator-down as recommended destroy method
   - Added orchestrator-up as recommended recreate method
   - Updated recreate steps to include workload-catalog and workload-etl
   - Clarified grants are not needed after normal recreate; link to initial-metastore-setup only if metastore was fully destroyed
   - Removed references to post-destroy-grants.md

## Decisions

- "Initial Metastore Setup" framing chosen over "Post-Destroy Grants" because the grants are
  one-time and tied to the Metastore lifecycle, not the workload destroy cycle.

## Artifacts

- `docs/runbooks/initial-metastore-setup.md` (new — replaces post-destroy-grants.md)
- `docs/runbooks/post-destroy-grants.md` (deleted)
- `docs/runbooks/destroy-recreate.md` (updated)
- `GETTING_STARTED.md` (updated)
- `docs/sessions/2026-03-13-002-runbook-grants-refactor.md` (this file)
