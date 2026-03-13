# Runbook: Destroy and Recreate All Workloads

**Applies to:** `workload-azure` and `workload-dbx` only.
Guardrails and the tfstate backend are not touched — they persist across cycles.

**When to use:** Cost-saving teardown between active sessions, or environment reset.

---

## Destroy

### Quick option — Orchestrator workflow (recommended)

Trigger **`orchestrator-down.yaml`** (workflow dispatch, no inputs required).

This runs `workload-dbx destroy` → `workload-azure destroy` in the correct order automatically.

### Manual option — individual workflows

If `orchestrator-down` is not available or you need to destroy only one layer:

> **Order is mandatory.** Destroying Azure before DBX orphans Unity Catalog account-scope objects
> (`uc-mi-credential`, `uc-root-location`) in the Metastore and breaks the next apply.

1. Trigger `workload-dbx.yaml` with `destroy=true`
   - Removes: Storage Credential (`uc-mi-credential`), External Location (`uc-root-location`)
   - The UC Metastore is an account-level resource; it may survive even with `force_destroy = true`
     if the destroy job fails before reaching it (handled automatically on next apply)
2. Trigger `workload-azure.yaml` with `destroy=true`
   - Removes: Databricks Workspace, ADLS Gen2, Access Connector, Resource Group

---

## Recreate

### Quick option — Orchestrator workflow (recommended)

Trigger **`orchestrator-up.yaml`** (workflow dispatch, no inputs required).

This runs `workload-azure` → `workload-dbx` → `workload-catalog` → `workload-etl` in order.

> The UC Metastore and its grants persist across destroy/recreate cycles in this platform.
> No manual grant steps are required after a normal recreate.
> If the Metastore was fully destroyed (rare), re-run the one-time setup:
> [initial-metastore-setup.md](./initial-metastore-setup.md)

### Manual option — individual workflows

1. Trigger `workload-azure.yaml` (no destroy flag)
   - Provisions: Resource Group, ADLS Gen2 containers, Access Connector, Databricks Workspace, RBAC
2. Trigger `workload-dbx.yaml` (no destroy flag)
   - Provisions: UC Metastore (or re-imports existing), Workspace assignment, Storage Credential, External Location
   - The CI workflow auto-discovers and imports the metastore if one already exists in the account
     (handles failed-destroy recovery). No manual UUID management required.
3. Trigger `workload-catalog.yaml`
   - Creates Catalog and Schemas via Jinja2 + SQL notebook
4. Trigger `workload-etl.yaml`
   - Deploys and runs the ETL pipeline

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

---

## Notes

- Guardrails (`guardrails.yaml`) and the tfstate Storage Account (`bootstrap.yaml`) are never
  destroyed in this cycle — they persist and remain valid after recreate.
- The UC Metastore is an account-level resource. Even with `force_destroy = true`, it may survive
  if a destroy run fails mid-way. The CI workflow detects this and auto-imports it on the next apply
  via the Databricks Account REST API — no manual UUID tracking required.
- The `METASTORE_ID` GitHub secret is no longer used and can be removed.
- Initial metastore grants (SP privileges + account-level groups) persist with the Metastore and do
  not need to be re-applied after a normal destroy/recreate cycle.
