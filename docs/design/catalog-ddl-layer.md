# Design Decisions — Catalog & Schema DDL Layer (platform/)

> Companion to ADR-001. Documents implementation-level decisions made when building
> `platform/`, `platform/databricks.yml`, and `.github/workflows/workload-catalog.yaml`.
> ADR-001 covers *what* tool to use (Jinja2 + SQL). This file covers *how* it is built.

---

## 1. Runtime Path Resolution via `notebookPath()`

**Decision:** The notebook resolves its own location at runtime:

```python
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
template_path = f"/Workspace{bundle_root}/ddl/catalog_schema.sql.j2"
```

**Why not hardcode?**
Hardcoding `/Workspace/Users/<sp>/mock-platform-catalog/notebooks/...` ties the notebook
to a specific service principal username and deployment path. If the SP changes (e.g., after
a destroy/recreate), or if the bundle target changes the deployment prefix, the hardcoded
path silently breaks. Runtime resolution has zero configuration and is principal-agnostic.

**Trade-off:** Slightly harder to read than a literal path. Mitigated by `print()` statements
that log the resolved paths for each run.

---

## 2. No `%pip install jinja2`

**Decision:** Jinja2 is used without `%pip install` at notebook startup.

**Why:** Jinja2 ships pre-installed on all Databricks Runtime 11+ clusters.
Installing it would add 30–60 seconds of cluster startup time and create a network
dependency in CI. Using the pre-installed version is zero-cost.

**Risk:** If the DBR major version changes the bundled version significantly, the template
syntax could behave differently. Mitigated by the template using only basic variable
substitution (`{{ env }}`), which is stable across all Jinja2 2.x/3.x versions.

---

## 3. Widget Default `"dev"` — Scope and Purpose

**Decision:** `dbutils.widgets.text("env", "dev")` sets a default of `"dev"`.

**Why this is safe:** In CI, `base_parameters: env: ${var.catalog_env}` in `databricks.yml`
always overrides the widget — the default is never reached during automated runs.
The default exists only for the case where a human opens the notebook interactively in the
workspace UI and runs it without setting the widget manually. Without a default, Databricks
raises a `com.databricks.dbutils.WidgetException`.

---

## 4. `mode: development` for dev/staging Targets

**Decision:**
```yaml
targets:
  dev:
    mode: development   # job name: "[dev run] setup_catalog_schema [dev]"
  staging:
    mode: development   # job name: "[staging run] setup_catalog_schema [staging]"
  prod:
    mode: production    # job name: "setup_catalog_schema [prod]"
```

**Why:** Databricks Asset Bundles prefix job names with the deploying principal's username
in `development` mode. This prevents name collisions if multiple engineers or environments
deploy to the same workspace. `prod` uses `mode: production` for clean, unprefixed job
names visible in the production workspace UI.

---

## 5. Single-Node Cluster

**Decision:**
```yaml
num_workers: 0
spark_conf:
  spark.master: "local[*, 4]"
  spark.databricks.cluster.profile: "singleNode"
custom_tags:
  ResourceClass: SingleNode
```

**Why:** `spark.sql()` executes DDL statements serially. There is no distributed computation
in this workload. A multi-worker cluster would be wasted cost and adds ~2 extra minutes of
startup time. `Standard_DS3_v2` (14 GB RAM, 4 vCPU) is sufficient for SQL parsing overhead
and is available in all Azure regions.

---

## 6. No `pull_request` Trigger in workload-catalog.yaml

**Decision:** The workflow has no `pull_request:` trigger — only `push` to main and
`workflow_dispatch`.

**Why (immediate):** Issue #40 — Azure federated credentials are configured only for `push`
and `workflow_dispatch` subjects. A `pull_request` trigger generates a different OIDC subject
(`repo:...:pull_request`) which is not in the federated credential allow-list. Adding a PR
trigger today guarantees an Azure login failure on every PR.

**Why (principled):** For a DDL layer, a Terraform-style "plan on PR, apply on merge" model
would be ideal, but Databricks CLI has no equivalent of `terraform plan` that shows a diff
of workspace objects. The operational value of a PR-triggered dry-run is low without a
meaningful diff output.

**Consequence:** No automated validation on PRs for `platform/**` changes. Mitigated by the
idempotency guarantee (re-running any target is always safe).

---

## 7. Databricks Token via `az account get-access-token` (Not a PAT)

**Decision:**
```yaml
- name: Acquire Databricks token via Azure CLI
  run: |
    TOKEN=$(az account get-access-token \
      --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d \
      --query accessToken -o tsv)
    echo "DATABRICKS_TOKEN=$TOKEN" >> $GITHUB_ENV
```

**Why:** Per ADR-002, no stored secrets. The Databricks resource ID
`2ff814a6-3304-4ab8-85cb-cd0e6f879c1d` is the well-known Azure AD application ID for the
Databricks service. Any OIDC-authenticated Azure session can request a short-lived token for
this resource. The token is in-memory for the duration of the job — never stored, never
rotated manually.

**Alternative rejected:** Databricks PAT stored as GitHub secret. Rotates, leaks, and
requires manual management. Violates ADR-002.

---

## 8. `source: WORKSPACE` in the Notebook Task

**Decision:**
```yaml
notebook_task:
  notebook_path: ./notebooks/00_setup_catalog_schema.py
  source: WORKSPACE
```

**Why:** `databricks bundle deploy` uploads the notebook file to the workspace under the
bundle's deployment path. When the job runs, it must reference the deployed copy — which
lives at a workspace path, not in a git repository. `source: WORKSPACE` is required.

`source: GIT` would instruct Databricks to pull the notebook directly from a git remote
at job runtime, bypassing the bundle deployment entirely. That would create a split execution
model (some artifacts from bundle, notebook from git) and would require git credentials on
the cluster.

---

## 9. SQL Splitting Strategy (Split on `;`, Skip Comments)

**Decision:**
```python
statements = [s.strip() for s in sql_rendered.split(";") if s.strip() and not s.strip().startswith("--")]
```

**Why:** `spark.sql()` accepts one statement at a time. The Jinja2 template renders a
multi-statement SQL file. Splitting on `;` is sufficient because the template is fully
controlled and contains no semicolons in string literals or comments. Comment-only chunks
(the file header) are skipped before execution.

**Alternative rejected:** Using a SQL parser library. Over-engineered for a template with
4 controlled statements. Would require `%pip install` and is harder to read.

---

## 10. prod Deploy Only on Push to main; dispatch Excludes prod

**Decision:** `workflow_dispatch` exposes `dev` and `staging` only. `prod` is only reachable
via a merge to `main`.

```yaml
workflow_dispatch:
  inputs:
    target:
      type: choice
      options: [ "dev", "staging" ]   # prod intentionally absent
```

**Why:** Production state should only change through a reviewed merge to main. This enforces
the CD principle: the main branch is the source of truth for production. To deploy to prod
manually, an engineer would need to edit the workflow file — which itself requires a PR,
providing an audit trail.

**Trade-off:** No escape hatch for production hotfixes via dispatch. Acceptable for a
portfolio/mock platform; a real production system might add a `prod` option gated on a
required approver.

---

## Prerequisite: GRANT CREATE CATALOG (Out-of-Band)

**This cannot be automated.** After each `workload-dbx` apply (metastore created/recreated),
a human metastore admin must run:

```sql
GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';
```

**Why it cannot be automated:** The Databricks SP that runs the CI job cannot grant itself
account-level Unity Catalog privileges. Account-level grants require a metastore admin
(human user). Same pattern as issue #19 (CREATE EXTERNAL LOCATION).

See issue #53 and the destroy/recreate procedure for the full checklist.
