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
3. **Update `METASTORE_ID` GitHub secret** — copy the new UUID from the `metastore_id` output in the CI Apply logs
   - GitHub → Settings → Secrets and variables → Actions → `METASTORE_ID`
   - A fresh metastore is created on every recreate; the UUID always changes
4. Run post-destroy grants — see [post-destroy-grants.md](./post-destroy-grants.md)
5. Trigger `workload-catalog` — creates Catalog and Schemas via Jinja2 + SQL notebook

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
- The Metastore is destroyed and recreated by `workload-dbx` destroy/apply. This is expected;
  `force_destroy = true` on the metastore ensures notebook-created catalogs are cascade-deleted.
- After recreate, the `METASTORE_ID` GitHub secret **must** be updated with the new UUID from the
  `workload-dbx` Apply output. The metastore UUID changes on every destroy/recreate cycle.
