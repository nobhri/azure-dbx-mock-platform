# Session: 2026-03-08-001 — Fix post-destroy-grants runbook

**Date:** 2026-03-08
**Branch:** docs/fix-post-destroy-grants
**PR:** [#98](https://github.com/nobhri/azure-dbx-mock-platform/pull/98)

---

## Goal

Fix incorrect CLI commands in `docs/runbooks/post-destroy-grants.md` Step 2 (account-level group
setup and member addition).

---

## Changes

### `docs/runbooks/post-destroy-grants.md`

**Group creation command was wrong:**
- Before: `databricks groups create --display-name <name> --profile <account-profile>`
  - This targets the workspace SCIM API — creates workspace-local groups, not account-level groups.
- After: `databricks account groups create --display-name <name> --profile account`
  - The `account` subcommand is required to target the Databricks Account API.

**Member-add command did not exist:**
- Before: `databricks groups add-member --group-name ... --user-name ... --profile ...`
  - This command does not exist in the Databricks CLI.
- After: Account SCIM API via `curl`:
  1. Fetch Azure AD token scoped to Databricks (`az account get-access-token --resource 2ff814a6-...`)
  2. `PATCH /api/2.0/accounts/<ACCOUNT_ID>/scim/v2/Groups/<GROUP_ID>` with PatchOp payload

**CLI profile setup added:**
- Full prerequisite steps: `az login`, `databricks configure --profile account` (Token left blank),
  manual edit of `~/.databrickscfg` to add `account_id` and `auth_type = azure-cli`, connectivity
  test with `databricks account workspaces list --profile account`.

**Structure:**
- Reorganised as Option A (Account Console GUI — recommended) / Option B (CLI + SCIM API).
- Account Console is now the primary recommendation — simpler and less error-prone.

---

## Issues

No new issues opened or closed this session.
