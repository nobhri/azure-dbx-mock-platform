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

### Step 2 — Catalog visibility grants (run after workload-catalog)

Per ADR-005, permissions are granted to **Entra ID groups via Native Sync** — not to individual
users or Databricks-only groups. When a user logs in with their Microsoft account, Entra ID group
memberships are automatically reflected in Databricks (no SCIM provisioner required).

**Prerequisite:** Create an Entra ID group (e.g., `databricks-platform-users`) and add all
human users who need catalog access. The group name used in the grant must match exactly.

```sql
-- Allow the Entra ID group to see and use the catalog
GRANT USE CATALOG ON CATALOG <catalog_name> TO `databricks-platform-users`;

-- Allow the group to see and use all schemas in the catalog
GRANT USE SCHEMA ON ALL SCHEMAS IN CATALOG <catalog_name> TO `databricks-platform-users`;
```

Replace `<catalog_name>` with the catalog name defined in your platform (e.g., `mock_dev`).

> **Note:** These grants are on the catalog object. If the catalog is dropped and recreated
> (e.g., after `workload-catalog` runs on a fresh environment), the grants must be re-run.
> The catalog uses `CREATE CATALOG IF NOT EXISTS` — if the catalog already exists, it is not
> dropped, and existing grants are preserved.

---

## When to Run

1. `workload-azure` apply ✅
2. `workload-dbx` apply ✅
3. **Step 1 grants (SP)** — run before workload-catalog
4. `workload-catalog` apply ✅
5. **Step 2 grants (Entra ID group)** — run after workload-catalog

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
