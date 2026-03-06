# Runbook: Destroy and Recreate All Workloads

**Applies to:** `workload-azure` and `workload-dbx` only.
Guardrails and the tfstate backend are not touched — they persist across cycles.

**When to use:** Cost-saving teardown between active sessions, or environment reset.

---

## Destroy Order (mandatory)

> Order is mandatory. Destroying Azure before DBX orphans Unity Catalog account-scope objects
> (`uc-mi-credential`, `uc-root-location`) in the Metastore and breaks the next apply.

1. Trigger `workload-dbx.yaml` with `destroy=true`
   - Removes: UC Metastore, Storage Credential (`uc-mi-credential`), External Location (`uc-root-location`)
2. Trigger `workload-azure.yaml` with `destroy=true`
   - Removes: Databricks Workspace, ADLS Gen2, Access Connector, Resource Group

---

## Recreate Order (mandatory)

1. Trigger `workload-azure.yaml` (no destroy flag)
   - Provisions: Resource Group, ADLS Gen2 containers, Access Connector, Databricks Workspace, RBAC
2. Trigger `workload-dbx.yaml` (no destroy flag)
   - Provisions: UC Metastore, Workspace assignment, Storage Credential, External Location
   - **Must complete before workload-catalog** — External Location created here is required by catalog
   - The CI workflow auto-discovers and imports the metastore if one already exists in the account
     (handles failed-destroy recovery). No manual UUID management required.
3. Run post-destroy grants — see [post-destroy-grants.md](./post-destroy-grants.md)
4. Trigger `workload-catalog` — creates Catalog and Schemas via Jinja2 + SQL notebook

---

## Orphaned UC Objects Recovery

If `workload-azure` was destroyed before `workload-dbx` (wrong order), the Metastore survives but
its objects are no longer in Terraform state. The next `workload-dbx` apply fails:

```
Error: cannot create storage credential: Storage Credential 'uc-mi-credential' already exists
```

**Recovery steps:**

1. Databricks Account Console → Unity Catalog → External Locations → delete `uc-root-location`
2. Databricks Account Console → Unity Catalog → Storage Credentials → delete `uc-mi-credential`
3. Trigger `workload-dbx.yaml` (no destroy flag) — apply will now succeed
4. Run post-destroy grants — see [post-destroy-grants.md](./post-destroy-grants.md)

---

## Notes

- Guardrails (`guardrails.yaml`) and the tfstate Storage Account (`bootstrap.yaml`) are never
  destroyed in this cycle — they persist and remain valid after recreate.
- The Metastore is destroyed by a successful `workload-dbx` destroy (`force_destroy = true` ensures
  notebook-created catalogs are cascade-deleted). If a destroy run fails mid-way, the metastore may
  survive — the CI workflow detects this and auto-imports it on the next apply via the Databricks
  Account REST API (no manual UUID tracking required).
- The `METASTORE_ID` GitHub secret is no longer used and can be removed.
