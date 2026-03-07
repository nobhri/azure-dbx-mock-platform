# Runbook: Post-Destroy Manual Grants

After each full destroy + recreate cycle, the Service Principal (CI/CD identity) loses two
account-level Unity Catalog privileges. These must be re-granted manually by the **metastore admin**
(human user) — the SP cannot self-grant UC account-level privileges.

---

## Why Manual?

These are account-scope Unity Catalog privileges, not workspace RBAC. Terraform cannot automate
them because:

1. The grant must be executed by a user who is already a metastore admin.
2. The SP is not a metastore admin — it cannot grant itself metastore-scope privileges.
3. There is no Terraform provider resource that runs SQL as a human user.

This is a deliberate platform boundary: human approval is required to re-grant the SP access
after each destroy cycle.

---

## Required Grants

### Step 1 — SP grants (run after workload-dbx, before workload-catalog)

Run as a **human user with metastore admin role** in a Databricks SQL warehouse or notebook:

```sql
-- Required for workload-dbx to create the External Location
GRANT CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>';

-- Required for workload-catalog to create Catalogs via the Jinja2 DDL notebook
GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';
```

Replace `<SP_client_id>` with the value of the `AZURE_CLIENT_ID` GitHub repository secret.

### Step 2 — Create account-level groups (one-time, before or after workload-catalog)

Unity Catalog `GRANT` statements target **account-level groups only** — workspace-local groups
(created via the workspace SCIM API) are not visible to UC. Groups must exist at the Databricks
account level before GRANTs can be applied.

In this mock environment, Databricks-native groups are used (ADR-005: Mock Environment
Simplification). Create the three groups via **Account Console** or **Databricks CLI with an
account-level profile**:

**Account Console:**
Databricks Account Console → User Management → Groups → Add Group

Groups to create:
- `data_platform_admins`
- `data_engineers`
- `data_consumers`

**Databricks CLI (account-level profile required):**
```bash
databricks groups create --display-name data_platform_admins --profile <account-profile>
databricks groups create --display-name data_engineers --profile <account-profile>
databricks groups create --display-name data_consumers --profile <account-profile>
```

> **Note:** The `workload-catalog` job (Step 4) attempts all GRANTs and emits a `WARNING` for
> any group that does not exist yet — it does **not** fail. Re-run `workload-catalog` after
> creating the groups to apply the deferred grants (all GRANT statements are idempotent).

**Add yourself to `data_platform_admins`** so you can see the catalog in the Databricks UI:
```bash
databricks groups add-member --group-name data_platform_admins --user-name <your-email> \
  --profile <account-profile>
```

---

## When to Run

1. `workload-azure` apply ✅
2. `workload-dbx` apply ✅
3. **Step 1 grants (SP)** — run before workload-catalog
4. **Step 2 groups (account-level)** — create before or after workload-catalog; re-run catalog job after creation
5. `workload-catalog` apply ✅ (GRANTs for missing groups emit WARNING, not error; re-run to apply)

---

## Verification

After Step 1 grants:
```sql
SHOW GRANTS ON METASTORE;
-- Confirm SP appears with CREATE EXTERNAL LOCATION and CREATE CATALOG
```

After Step 2 grants:
```sql
SHOW GRANTS ON CATALOG <catalog_name>;
-- Confirm databricks-platform-users appears with USE CATALOG
```

---

## Related Issues

- [issue #19](https://github.com/nobhri/azure-dbx-mock-platform/issues/19) — original discovery
- [issue #21](https://github.com/nobhri/azure-dbx-mock-platform/issues/21) — User Access Administrator role (resolved 2026-03-02)
- [issue #53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) — GRANT CREATE CATALOG documentation
