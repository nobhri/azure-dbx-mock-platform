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
Simplification).

> **Recommended:** Use the **Account Console GUI** — it is the simplest and least error-prone
> method for both group creation and member addition.

#### Option A — Account Console (recommended)

**Create groups:**
Databricks Account Console → User Management → Groups → Add Group

Groups to create:
- `data_platform_admins`
- `data_engineers`
- `data_consumers`

**Add yourself to `data_platform_admins`** so you can see the catalog in the Databricks UI:
Databricks Account Console → User Management → Groups → `data_platform_admins` → Add members

#### Option B — Databricks CLI (account-level profile required)

The `databricks account` subcommand must be used — the workspace-level `databricks groups`
command targets the wrong API and will not create account-level groups.

**Prerequisites — configure an account-level CLI profile:**

```bash
# 1. Log in to Azure CLI
az login

# 2. Create a CLI profile (leave Token blank — Azure CLI auth is used)
databricks configure --profile account
#  Host: https://accounts.azuredatabricks.net
#  Token: (press Enter — leave empty)

# 3. Edit ~/.databrickscfg and add account_id + auth_type to the [account] section:
#  [account]
#  host        = https://accounts.azuredatabricks.net
#  account_id  = <YOUR_DATABRICKS_ACCOUNT_ID>
#  auth_type   = azure-cli

# 4. Verify connectivity
databricks account workspaces list --profile account
```

**Create groups:**
```bash
databricks account groups create --display-name data_platform_admins --profile account
databricks account groups create --display-name data_engineers --profile account
databricks account groups create --display-name data_consumers --profile account
```

**Add yourself to `data_platform_admins`:**

The Databricks CLI does not yet implement the account-level member-add operation. Use the
Account SCIM API directly:

```bash
# 1. Obtain a Databricks-scoped Azure AD token
TOKEN=$(az account get-access-token \
  --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d \
  --query accessToken -o tsv)
# Note: 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d is the Databricks Azure AD application ID.

# 2. Patch the group via SCIM API
#    Replace <ACCOUNT_ID>, <GROUP_ID>, and <USER_ID> with the actual values.
#    USER_ID is the Databricks user ID (numeric), visible in Account Console → User Management.
curl -X PATCH \
  https://accounts.azuredatabricks.net/api/2.0/accounts/<ACCOUNT_ID>/scim/v2/Groups/<GROUP_ID> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/scim+json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [
      {
        "op": "add",
        "path": "members",
        "value": [{"value": "<USER_ID>"}]
      }
    ]
  }'
```

> **Note:** The `workload-catalog` job (Step 4) attempts all GRANTs and emits a `WARNING` for
> any group that does not exist yet — it does **not** fail. Re-run `workload-catalog` after
> creating the groups to apply the deferred grants (all GRANT statements are idempotent).

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
