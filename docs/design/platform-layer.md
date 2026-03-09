# Design: Platform Layer (`platform/`)

> Companion to ADR-001 and ADR-005. Documents implementation-level decisions made when
> building `platform/`, `platform/databricks.yml`, and `.github/workflows/workload-catalog.yaml`.
>
> **ADR-001** covers *what* tool to use (Jinja2 + SQL vs Terraform).
> **ADR-005** covers *why* group-based access and where grants live.
> **This file** covers *how* the platform layer is actually built — and what was intentionally
> simplified for the mock environment.

---

## Implementation Decisions

### 1. Runtime Path Resolution via `notebookPath()`

**Decision:** The notebook resolves its own location at runtime:

```python
notebook_path = (
    dbutils.notebook.entry_point
    .getDbutils().notebook().getContext().notebookPath().get()
)
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
configs_dir  = f"/Workspace{bundle_root}/configs"
templates_dir = f"/Workspace{bundle_root}/templates"
```

**Why not hardcode?**
Hardcoding `/Workspace/Users/<sp>/mock-platform-catalog/...` ties the notebook to a specific
service principal username and bundle deployment prefix. If the SP changes (e.g., after a
destroy/recreate) or the target changes, the hardcoded path silently breaks. Runtime resolution
is zero-configuration and principal-agnostic.

**Trade-off:** Slightly harder to read than a literal path. Mitigated by `print()` statements
that log the resolved `bundle_root`, `configs_dir`, and `templates_dir` on every run.

---

### 2. No `%pip install jinja2`

**Decision:** Jinja2 is used without an installation step.

**Why:** Jinja2 ships pre-installed on all Databricks Runtime 11+ clusters. Installing it
would add 30–60 seconds of startup time and introduce a network dependency in CI. The
pre-installed version is zero-cost.

**Risk:** If the DBR major version changes the bundled Jinja2 version significantly, template
syntax could behave differently. Mitigated by the templates using only basic variable
substitution (`{{ var }}`), which is stable across Jinja2 2.x/3.x.

**PyYAML is different:** `PyYAML` is not bundled on DBR 14.3 and must be installed. It is
declared in `databricks.yml` under `libraries: [{pypi: {package: PyYAML}}]`, which installs
it at cluster startup without a `%pip` cell.

---

### 3. Widget Parameters: `storage_account_name` and `uc_root_container`

**Decision:** The notebook declares two string widgets:

```python
dbutils.widgets.text("storage_account_name", "")
dbutils.widgets.text("uc_root_container", "")
```

These are always overridden by `base_parameters` from `databricks.yml` during CI runs.
The empty-string default exists only to prevent a `WidgetException` if the notebook is opened
interactively without parameters.

**Where the values come from:** Both are read from `workload-azure` Terraform remote state
in `workload-catalog.yaml`. The workflow reads them as Terraform outputs:

```yaml
- name: Capture workload-azure outputs
  id: azout
  run: |
    echo "STORAGE_ACCOUNT_NAME=$(terraform -chdir=infra/workload-azure output -raw storage_account_name)" >> $GITHUB_OUTPUT
    echo "UC_ROOT_CONTAINER=$(terraform -chdir=infra/workload-azure output -raw uc_root_container)" >> $GITHUB_OUTPUT
```

Then passes them as bundle variables at deploy time (see §10 — Output Passing).

**Why not an `env` widget:** An earlier design used a single `env` string to drive catalog
name selection. The current design uses storage account name and container directly to
construct the managed location (`abfss://container@account.dfs.core.windows.net/...`). The
catalog name comes from `configs/catalog_schema.yaml`, not from the widget.

---

### 4. Bundle Targets: `dev` and `prod` Only

**Decision:**

```yaml
targets:
  dev:
    mode: development
  prod:
    mode: production
```

Two targets — no `staging`. `mode: development` prefixes the job name with the deploying
principal's username, preventing naming collisions in a shared workspace. `mode: production`
produces a clean, unprefixed job name visible in the production workspace UI.

**Why no staging:** Provisioning a third environment multiplies cost and CI/CD complexity.
The portfolio mock demonstrates environment-aware design intent (two targets, separate
catalog names planned for the Data Engineering phase) without the overhead of a third target.

---

### 5. Single-Node Cluster

**Decision:**

```yaml
num_workers: 0
spark_conf:
  spark.master: "local[*, 4]"
  spark.databricks.cluster.profile: "singleNode"
```

**Why:** `spark.sql()` executes DDL statements serially. There is no distributed computation
in this workload. A multi-worker cluster would waste cost and add ~2 minutes of startup.
`Standard_DS3_v2` (14 GB RAM, 4 vCPU) covers the SQL parsing overhead and is available in
all Azure regions.

---

### 6. No `pull_request` Trigger

**Decision:** `workload-catalog.yaml` has `on: push` (main) and `workflow_dispatch` only — no
`pull_request` trigger.

**Why (immediate — issue #40):** Azure federated credentials are configured only for `push`
and `workflow_dispatch` OIDC subjects. A `pull_request` event generates a different subject
(`repo:...:pull_request`) that is not in the federated credential allow-list. A PR trigger
would fail Azure login on every PR.

**Why (principled):** For a DDL layer, a Terraform-style "plan on PR, apply on merge" model
would be ideal, but the Databricks CLI has no equivalent of `terraform plan` that diffs
workspace objects. Without a meaningful diff output, a PR-triggered dry-run adds CI time
for little operational value.

**Consequence:** No automated validation on PRs for `platform/**` changes. Mitigated by
the idempotency guarantee — re-running any target is always safe.

---

### 7. Databricks Token via `az account get-access-token` (Not a PAT)

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
Databricks service. Any OIDC-authenticated Azure session can request a short-lived token
for this resource. The token is in-memory for the duration of the job — never stored, never
rotated manually.

**Rejected:** Databricks PAT stored as GitHub Secret. Rotates, can leak, requires manual
management. Violates ADR-002.

---

### 8. `source: WORKSPACE` in the Notebook Task

**Decision:**

```yaml
notebook_task:
  notebook_path: ./notebooks/setup_platform.py
  source: WORKSPACE
```

**Why:** `databricks bundle deploy` uploads the notebook to the workspace under the bundle's
deployment path. The job must reference that deployed copy — which lives at a workspace path,
not in the git remote. `source: WORKSPACE` is required.

`source: GIT` would pull the notebook from git at job runtime, bypassing the bundle
deployment. That creates a split execution model (bundle artifacts from deploy, notebook
from git) and requires git credentials on the cluster.

---

### 9. `render_and_execute` Helper

**Decision:** A shared Python function handles template rendering and SQL execution:

```python
def render_and_execute(template_file, template_vars, warn_on_principal_missing=False):
    # Load template, render with Jinja2, strip comment lines,
    # split on ";", execute each statement via spark.sql()
    ...
```

**Why a helper:** The notebook has four distinct SQL phases (CREATE CATALOG, CREATE SCHEMA,
GRANT PERMISSIONS). Without a helper, each phase duplicates the load-render-strip-split-execute
logic. The helper also encapsulates the `warn_on_principal_missing` behavior uniformly.

**SQL splitting:** Comment lines are stripped before splitting on `;` to avoid executing
comment-only chunks. A full SQL parser library is not used — it would be over-engineered for
templates that contain no semicolons in string literals.

**`warn_on_principal_missing`:** Used for the GRANT step. If a group does not yet exist at
the account level, the grant is skipped with a WARNING rather than failing the job. The job
succeeds; the skipped grants are applied by re-running workload-catalog after the groups are
created. All GRANT statements are idempotent.

> **Production note:** The silent-skip behavior is acceptable for a mock environment where
> group creation is manual. In production, this should be hardened — either fail fast on
> missing principals, or add a post-run assertion that all expected grants are applied.

---

### 10. Push → `prod`; Dispatch → `dev` (No Dispatch Inputs)

**Decision:**

```yaml
on:
  push:
    branches: [ "main" ]
    paths: [ "platform/**" ]
  workflow_dispatch: {}
```

```yaml
- name: Set bundle target
  run: |
    if [ "${{ github.event_name }}" = "push" ]; then
      echo "TARGET=prod" >> $GITHUB_OUTPUT
    else
      echo "TARGET=dev" >> $GITHUB_OUTPUT
    fi
```

`workflow_dispatch` has no inputs — it always deploys to `dev`. `prod` is only reachable
via a merge to `main`.

**Why:** Production state should change only through a reviewed merge to main, enforcing the
CD principle: main branch = source of truth for production. A manual dispatch is always a
safe `dev` run. An engineer who needs to deploy to prod in an emergency must merge to main —
providing an audit trail.

**Trade-off:** No escape hatch for production hotfixes via dispatch. Acceptable for a
portfolio/mock platform.

---

### 11. Group Creation is Out-of-Band

**Decision:** The platform notebook does NOT create groups. Step 3 is a prerequisite notice
only — it prints which account-level groups are expected and warns the operator to create them
before the GRANT step will fully apply.

**Why groups cannot be auto-created by the notebook:** Unity Catalog GRANT requires
account-level groups (not workspace SCIM groups). Creating account-level groups requires
Account Admin permission. The SP has Account Admin, but automating group creation in a public
repository would require committing group membership data (email addresses). This violates
the membership-separation principle in ADR-005: *"Group membership (who belongs to each group)
is managed outside the repository."*

**Operational consequence:** Before the first workload-catalog run (or after a full
destroy/recreate), account-level groups must be created manually:

```bash
databricks groups create --display-name data_platform_admins --profile <account-profile>
databricks groups create --display-name data_engineers       --profile <account-profile>
databricks groups create --display-name data_consumers       --profile <account-profile>
```

> **Production note:** In production this step should be automated via CLI or SDK in CI/CD,
> triggered once per environment setup — not left as a manual prerequisite.

---

### 12. Output Passing: workload-azure → workload-catalog

**Decision:** `workload-catalog.yaml` reads Terraform remote state from `workload-azure`
directly, using a `terraform init` + `terraform output` step:

```yaml
- name: Init workload-azure backend to read outputs
  run: |
    terraform -chdir=infra/workload-azure init \
      -backend-config="resource_group_name=$TFSTATE_RG_NAME" \
      -backend-config="storage_account_name=$TFSTATE_SA_NAME" \
      -backend-config="container_name=workload-tfstate" \
      -backend-config="key=azure.tfstate"

- name: Capture workload-azure outputs
  id: azout
  run: |
    echo "STORAGE_ACCOUNT_NAME=$(terraform -chdir=infra/workload-azure output -raw storage_account_name)" >> $GITHUB_OUTPUT
    echo "UC_ROOT_CONTAINER=$(terraform -chdir=infra/workload-azure output -raw uc_root_container)" >> $GITHUB_OUTPUT
```

The same mechanism is used by `workload-dbx`. Three workflows in this repo read from the same
`workload-azure` Terraform remote state: `workload-dbx`, `workload-catalog`, and the
`workload-catalog` preflight check. This output-passing pattern is "free" in a single-repo
design — all three workflows share the same Azure identity and the same backend configuration.
If the repo were split (see §Production Simplifications — Repo Separation), this shared state
access would become an explicit cross-repo coupling problem.

---

## Production Simplifications

These items are intentionally simplified for the mock environment. Each represents a known gap
between the current design and a production-grade platform.

For the full reasoning behind the tool and permission boundaries, see ADR-001 and ADR-005.
For the decommissioning procedure, see [`runbooks/decommission-schema.md`](../runbooks/decommission-schema.md).
For the post-destroy grant procedure, see [`runbooks/post-destroy-grants.md`](../runbooks/post-destroy-grants.md).

---

### S1. Single Workspace vs Dedicated Workspace per Environment

**Mock design:** One workspace. Environment isolation is the *intent* — the bundle has `dev`
and `prod` targets, and catalog naming is environment-aware by design. In the mock, both
targets deploy to the same workspace and the same catalog (`mock`). The SDLC lookup function
(planned in `proposals/sdlc-catalog-lookup.md`) will connect bundle targets to distinct
catalog names in the Data Engineering phase; it is not yet implemented.

**Current catalog:** `catalog_schema.yaml` hardcodes `catalog.name: mock`. There is no
environment-specific catalog separation today.

**ADR-005 Mock Simplification:** ADR-005 explicitly documents: *"Single Catalog: `mock` only.
No environment-specific Catalog separation (e.g., `mock_dev`, `mock_staging`, `mock_prod`)."*

**Production reality:** Dedicated workspace per environment. Each workspace has its own
identity boundary, network configuration, and catalog binding. Workspace-level RBAC and
governance are cleanly separated.

**Why the mock doesn't implement this:** Provisioning and maintaining multiple workspaces
multiplies Azure cost and CI/CD complexity. Demonstrating the SDLC pattern (catalog switching
via bundle targets) is the design intent; the mock single-workspace design does not block
migration when the platform scales.

---

### S2. System Tables for Catalog / Schema Change Tracking

**Current DDL state:** DDL is idempotent (`CREATE IF NOT EXISTS`). Deletions are not detected
at apply time — explicitly accepted in ADR-001: *"DDL `IF NOT EXISTS` is idempotent but will
not detect deletions."* This is an accepted trade-off for the MVP phase.

**When system tables become relevant:** Once schemas are modified over time (column additions,
type changes, object drops), audit-level tracking is needed for:
- Detecting drift between declared DDL and actual UC state
- Auditing who changed what and when (compliance, incident response)
- Triggering alerts on unexpected schema changes

**Enablement conditions (now actionable — platform layer live as of 2026-03-09):**
- System tables must be enabled at the account level: `system.access`, `system.information_schema`
- The UC metastore is already in place
- A scheduled job or CI/CD step would query `system.information_schema.columns` and compare
  against Jinja2 template expectations

Note: ADR-005 Consequences already states: *"What happened (execution evidence): Databricks
system tables (`system.access.audit`) — built-in audit logging that automatically records all
GRANT operations."* System tables are available now; the drift-detection query job is the
remaining gap.

---

### S3. Infra / Platform Repo Separation and Cross-Repo Output Passing

**Current state:** Single repository. Three workflows read `workload-azure` Terraform outputs
via shared remote state: `workload-dbx`, `workload-catalog`, and the `workload-catalog`
preflight check. This is free under a single-repo, single-identity design (see §12 above).

**Production reality:** Infrastructure (Azure resources) and platform (Databricks
configuration, Unity Catalog) are often owned by different teams in separate repos.
With three consumers of `workload-azure` outputs, a split creates three output-passing
dependencies, not two:

| Consumer | Outputs needed |
|----------|---------------|
| workload-dbx | storage account name, workspace URL |
| workload-catalog | storage account name, UC root container, workspace URL |
| workload-catalog preflight | workspace URL (for Databricks CLI auth) |

**Cross-repo output passing options:**

| Mechanism | Trade-offs |
|-----------|-----------|
| Shared Terraform remote state | Both repos need read access to the same backend; tight coupling at state layer |
| GitHub Secrets / Variables (manual) | Requires human update after each infra apply; error-prone |
| Cross-repo GitHub Actions triggers with output artifacts | Complex workflow orchestration; artifact lifetime management |
| Published artifact / API endpoint | Most decoupled; highest implementation cost |

**Relationship to ADR-005 (updated 2026-03-07):** ADR-005 moved all metastore-scoped GRANTs
from Terraform to the Platform Layer (SQL/SDK). This reinforces the Terraform responsibility
boundary — the infra side no longer issues account-level UC grants — making the infra/platform
split cleaner when it eventually happens.

---

### S4. Single Service Principal vs Separated SP per Layer

**Current state:** One SP handles all CI/CD operations:
- Azure resource provisioning (Terraform in `workload-azure`)
- Databricks workspace + metastore configuration (Terraform in `workload-dbx`)
- Platform layer execution (Python notebook via Asset Bundles in `workload-catalog`)

The notebook (`setup_platform.py`) runs as this SP and issues catalog- and schema-scoped
GRANTs via `spark.sql()`. These are Unity Catalog SQL GRANTs at the catalog/schema scope —
not account-level API calls. The SP's Account Admin role allows it to see and govern UC
objects; the GRANTs themselves are standard UC SQL.

**Production reality — least-privilege design:**

| SP | Scope |
|----|-------|
| Infra SP | Azure RBAC (Contributor on RG, Storage Blob Data Contributor) |
| Platform SP | Databricks workspace admin, Unity Catalog GRANT at catalog/schema scope |
| Data SP | Job execution, catalog read/write only |

**ADR-005 SP exception rule:** The SP is an explicit exception to the group-only GRANT rule —
*"the SP is granted directly as it is not a human user and has no EntraID group membership."*
In a separated-SP design, the Platform SP would hold the metastore-admin role and issue grants;
the Data SP would be a narrower identity with catalog-level permissions only.

**Coupling to S3 (repo separation):**
- Single SP + single repo: Terraform remote state is readable by all workflows under the same
  identity — output passing is free.
- Separated SPs + separated repos: the infra SP's outputs are no longer directly accessible to
  the platform SP. An explicit output-passing mechanism (see S3) is required.
- Separating SPs also requires separate federated credential configurations in Entra ID and
  separate GitHub secret sets per repo.

**Note on group creation:** Group creation is currently manual (see §11). In a
separated-SP design, the Platform SP would need explicit Account Admin permission to
create account-level groups via the SDK — or group provisioning would be handled by a
separate IdP-driven process (EntraID Native Sync, per ADR-005).
