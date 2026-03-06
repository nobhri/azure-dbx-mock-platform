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

Run the following as a **human user with metastore admin role** in a Databricks SQL warehouse or
notebook connected to the Unity Catalog metastore:

```sql
-- Required for workload-dbx to create the External Location
GRANT CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>';

-- Required for workload-catalog to create Catalogs via the Jinja2 DDL notebook
GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';
```

Replace `<SP_client_id>` with the value of the `AZURE_CLIENT_ID` GitHub repository secret.

---

## When to Run

Run these grants **after** `workload-dbx` apply completes successfully and **before** triggering
`workload-catalog`. The full sequence:

1. `workload-azure` apply ✅
2. `workload-dbx` apply ✅
3. **These grants ← you are here**
4. `workload-catalog` apply

---

## Verification

After running grants, verify with:

```sql
SHOW GRANTS ON METASTORE;
```

Confirm `<SP_client_id>` appears with `CREATE EXTERNAL LOCATION` and `CREATE CATALOG` privileges.

---

## Related Issues

- [issue #19](https://github.com/nobhri/azure-dbx-mock-platform/issues/19) — original discovery
- [issue #21](https://github.com/nobhri/azure-dbx-mock-platform/issues/21) — User Access Administrator role (resolved 2026-03-02)
- [issue #53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53) — GRANT CREATE CATALOG documentation
