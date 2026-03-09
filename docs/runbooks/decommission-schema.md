# Runbook: Decommission a Catalog or Schema

> **Rationale:** For why soft-delete is recommended over DROP CASCADE, see
> `docs/design/platform-layer.md` §Production Simplifications — S4, and ADR-005
> §Production Consideration: Catalog/Schema Decommissioning.

---

## When to use this runbook

Use when a schema (or catalog) needs to be retired from production. Do **not** use
`DROP ... CASCADE` directly — it is unrecoverable if run against production accidentally.

---

## Mock environment

The mock environment has `force_destroy = true` on the metastore (PR #50). A successful
`terraform destroy` of `workload-dbx` cascade-deletes the metastore and all managed
catalogs. Individual catalog/schema decommissioning is not required in the mock.

This runbook applies to production deployments.

---

## Procedure (production)

### Step 1 — Revoke all group access

Run in a Databricks SQL warehouse connected to the target catalog:

```sql
REVOKE ALL PRIVILEGES ON SCHEMA `<catalog>`.`<schema>` FROM `data_platform_admins`;
REVOKE ALL PRIVILEGES ON SCHEMA `<catalog>`.`<schema>` FROM `data_engineers`;
REVOKE ALL PRIVILEGES ON SCHEMA `<catalog>`.`<schema>` FROM `data_consumers`;
```

### Step 2 — Mark as deprecated

```sql
COMMENT ON SCHEMA `<catalog>`.`<schema>` IS 'DEPRECATED <yyyy-mm-dd> -- do not use';
```

### Step 3 — Verify no active usage

Query system tables to check for recent access before dropping:

```sql
SELECT user_identity, action_name, request_params, event_time
FROM system.access.audit
WHERE request_params LIKE '%<schema>%'
  AND event_time > DATEADD(DAY, -30, CURRENT_TIMESTAMP())
ORDER BY event_time DESC;
```

If recent `SELECT` or `MODIFY` activity is found, investigate the source before proceeding.

### Step 4 — DROP after review period

After a review period (minimum 30 days recommended for production), execute with explicit
approval:

```sql
DROP SCHEMA `<catalog>`.`<schema>` CASCADE;
```

---

## Decommissioning a full catalog

If all schemas under a catalog are retired, apply the same pattern at catalog level:

```sql
-- Step 1: Revoke catalog-level access
REVOKE ALL PRIVILEGES ON CATALOG `<catalog>` FROM `data_platform_admins`;
REVOKE ALL PRIVILEGES ON CATALOG `<catalog>` FROM `data_engineers`;
REVOKE ALL PRIVILEGES ON CATALOG `<catalog>` FROM `data_consumers`;

-- Step 2: Mark deprecated
COMMENT ON CATALOG `<catalog>` IS 'DEPRECATED <yyyy-mm-dd> -- do not use';

-- Step 3: Verify (see schema procedure above, scoped to catalog)

-- Step 4: DROP after review period
DROP CATALOG `<catalog>` CASCADE;
```

---

## Design rationale (summary)

- DROP CASCADE in CI/CD pipelines is too high-risk for production data
- Soft delete (REVOKE + COMMENT) allows recovery if unexpected dependencies surface
- REVOKE fits naturally into the existing GRANT pipeline as its inverse
- Databricks system tables automatically record when access was revoked — no custom audit
  log required
- The review period surfaces dependencies not captured in documentation
