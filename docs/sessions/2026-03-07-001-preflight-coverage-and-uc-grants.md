# Session 2026-03-07-001 — Preflight Coverage Review and UC Grant Design

## Part 1: Preflight Test Coverage Review

### Runs Reviewed

| Run ID | Trigger | Metastore state | Preflight result | Outcome |
|--------|---------|----------------|-----------------|---------|
| 22767883393 | workflow_dispatch | Assigned + uc-root-location exists | "Preflight passed" ✅ | Bundle run succeeded |
| 22768507420 | workflow_dispatch | **No metastore assigned** | "Preflight passed" ❌ (false pass) | Bundle run failed: `METASTORE_DOES_NOT_EXIST` |

### Finding: Preflight Fix Not in Main (Issue #84)

The fix commit (`e5e381e`) was pushed to `fix/68-catalog-preflight` **after** PR #79
was already merged. Only the buggy first commit made it into `main`. As a result:

- When `databricks external-locations list` returns an error (CLI exit non-zero),
  `COUNT` is empty → `[ "" -eq 0 ]` returns exit 2 (`integer expression expected`)
  → treated as `false` in `if` context → body skipped → "Preflight passed" printed
- The workflow continues to `bundle run` and fails 5 minutes later with
  `AnalysisException: METASTORE_DOES_NOT_EXIST`

The fix (PR #84) captures the CLI exit code explicitly:
```bash
if ! RAW=$(databricks external-locations list --output json 2>&1); then
  echo "::error::Preflight failed: $RAW"
  exit 1
fi
```

### Test Coverage Summary (as of this session)

| Scenario | Run | Status |
|----------|-----|--------|
| uc-root-location exists → pass | 22767883393 | ✅ Tested |
| No metastore assigned → **should fail, actually passed** | 22768507420 | ❌ Bug confirmed |
| uc-root-location missing (metastore assigned) | — | Not yet tested |

The third scenario (metastore assigned but external location absent) has not been
triggered in CI. It would require `workload-dbx` apply to succeed (metastore assigned)
but `uc-root-location` to be missing (e.g., manually deleted from UC).

---

## Part 2: UC Catalog/Schema Visibility — Role Assignment Design

### Problem

After `workload-catalog` creates the catalog and schemas (via CI/CD SP), the human
user (metastore admin) cannot see the catalog or schemas in the Databricks UI.

### Root Cause

Unity Catalog uses privilege-based visibility. Metastore admin grants management
capability but does NOT auto-grant `USE CATALOG` or `USE SCHEMA` on catalogs owned
by other principals. The SP is the catalog owner; the human user needs explicit grants.

### Design Decision: Entra ID Group via Native Sync (per ADR-005)

**ADR-005** specifies: *"EntraID Groups are synced into Databricks via Native Sync (not SCIM provisioning)."*

Initial advice in this session incorrectly framed the option as "SCIM sync". Native Sync is a
different (simpler) mechanism:

| Mechanism | How it works | Setup required |
|-----------|-------------|----------------|
| SCIM | External Entra ID Enterprise App pushes group memberships on a schedule | SCIM app configuration |
| **Native Sync** | Databricks reads Entra ID group memberships from the user's token at login time | **None** — automatic when user authenticates with Microsoft account |

Native Sync requires no external provisioner. When a user logs into Databricks using their
Microsoft (Entra ID) account, their Entra ID group memberships are reflected automatically.
The group name used in UC grants must match the Entra ID group name exactly.

### Implementation Plan (tracked in issue #85)

1. Create group in **Entra ID** (e.g., `databricks-platform-users`)
2. Add human user(s) to the group in Entra ID
3. After `workload-catalog` runs, execute as metastore admin:

```sql
GRANT USE CATALOG ON CATALOG <catalog_name> TO `databricks-platform-users`;
GRANT USE SCHEMA ON ALL SCHEMAS IN CATALOG <catalog_name> TO `databricks-platform-users`;
```

4. Update `docs/runbooks/post-destroy-grants.md` to include these grants as a step
   after `workload-catalog` completes.

### Note on Destroy/Recreate

These grants are on the catalog object, which is created by `workload-catalog`.
When `workload-catalog` re-runs after a destroy cycle, the catalog is recreated
by the notebook (it uses `CREATE CATALOG IF NOT EXISTS`). The grants persist if
the catalog object is the same name and survives; they are lost if the catalog is
dropped and recreated. The runbook should note this.
