# Session 2026-03-10-001 — Fix wrong group name in post-destroy-grants.md (#107)

**Date:** 2026-03-10
**Branch:** fix/post-destroy-grants-107
**Issue:** [#107](https://github.com/nobhri/azure-dbx-mock-platform/issues/107)

## Change

Fixed wrong group name in the Verification section of `docs/runbooks/post-destroy-grants.md`.

The SQL comment after `SHOW GRANTS ON CATALOG` referenced `databricks-platform-users`, which was
a stale/incorrect group name. The correct account-level group created by the platform layer is
`data_platform_admins`.

**File:** `docs/runbooks/post-destroy-grants.md` line 155
**Before:** `-- Confirm databricks-platform-users appears with USE CATALOG`
**After:** `-- Confirm data_platform_admins appears with USE CATALOG`

## Status at session end

No issues opened or closed. Issue #107 is pending human review and manual close after PR merge.
