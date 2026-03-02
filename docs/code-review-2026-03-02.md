# Code Review — 2026-03-02

**Scope:** Full codebase review — documentation consistency, Terraform structure, security, file organization
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Status:** MVP phase

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Documentation Consistency](#documentation-consistency)
3. [Terraform Analysis](#terraform-analysis)
4. [GitHub Actions Workflows](#github-actions-workflows)
5. [Security Assessment](#security-assessment)
6. [Taskfile](#taskfile)
7. [Issues by Severity](#issues-by-severity)
8. [Strengths](#strengths)
9. [Recommendations](#recommendations)

---

## Directory Structure

```
azure-dbx-mock-platform/
├── README.md
├── GETTING_STARTED.md
├── CLAUDE.md
├── Taskfile.yml
├── .gitignore
├── .env.example
├── .github/workflows/
│   ├── bootstrap.yaml
│   ├── guardrails.yaml
│   ├── workload-azure.yaml
│   └── workload-dbx.yaml
└── infra/
    ├── bootstrap/
    │   ├── main.tf
    │   └── variables.tf
    ├── guardrails/
    │   ├── main.tf
    │   └── variables.tf
    ├── workload-azure/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── providers.tf
    └── workload-dbx/
        ├── main.tf
        ├── variables.tf
        └── providers.tf
```

**Observation:** `terraform.tfstate` exists in the repo root, indicating a local Terraform run was executed outside the `infra/` layer. This file is correctly excluded by `.gitignore` but suggests manual execution occurred outside the intended CI/CD path.

---

## Documentation Consistency

### README.md vs. Implementation

| ADR | Documented Behaviour | Actual Implementation | Match |
|-----|---------------------|-----------------------|-------|
| ADR-001: Terraform for infra/metastore; SQL for catalog/schema | Catalog/schema via Jinja2 + Python Notebook | Catalog/schema resources are commented out in `workload-dbx/main.tf` | Partial — MVP state is consistent with ADR intent but transition path is unclear |
| ADR-002: OIDC authentication, no stored secrets | OIDC via `auth_type = "azure-cli"`, no PATs | All providers use OIDC; workflows use `azure/login` with OIDC | Full match |
| ADR-003: Idempotency first-class | Repeatable Terraform + DDL | `lifecycle { ignore_changes = [...] }` on metastore; `force_destroy` on storage | Full match |
| ADR-004: View layer for data consumers | Access via views, not raw tables | No view layer implemented yet (noted as future work) | Documented gap |
| ADR-005: Group-based RBAC via EntraID sync | No inline user grants | No user-level grants in Terraform | Full match |

**GETTING_STARTED.md** is accurate and up-to-date. Prerequisites, OIDC setup steps, and deployment sequence match the actual workflow files.

---

## Terraform Analysis

### infra/bootstrap/main.tf

**Status: Clean**

- Creates tfstate Resource Group, Storage Account, and three separate containers (`guardrails`, `azure`, `dbx`)
- TLS 1.2 enforced
- Public network access enabled — required for GitHub Actions runners; documented trade-off

### infra/guardrails/main.tf

**Status: Clean**

- Subscription-level budget with 80% threshold alert
- Configurable start/end dates
- Alert email parameterized via variable

### infra/workload-azure/main.tf

**Status: Clean**

- Resource Group, ADLS Gen2 (HNS enabled, TLS 1.2), Access Connector (Managed Identity), Databricks Workspace
- RBAC: Managed Identity → Storage Blob Data Contributor
- No hardcoded values; all resource names derived from `var.prefix`
- Storage containers (`landing`, `uc-root`, `bronze`, `silver`) consistently named

### infra/workload-azure/outputs.tf

**Status: Clean**

- Exports `workspace_resource_id`, `workspace_name`, `access_connector_id`, `storage_account_name`, `uc_root_container`
- Consumed correctly by `workload-dbx` layer and the GitHub Actions workflow

### infra/workload-dbx/main.tf

**Status: Issues Found**

**Issue 1 (HIGH): Hardcoded metastore UUID**

```hcl
# main.tf:43
storage_root = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/30ebd5eb-ba32-4617-b715-1bbad2ad51e0"
# TODO: parameterize hardcoded metastore ID.
```

The UUID `30ebd5eb-ba32-4617-b715-1bbad2ad51e0` is environment-specific. Any redeployment to a different subscription will silently produce a wrong storage path. The `TODO` acknowledges this.

**Fix:** Add `variable "metastore_id" {}` and replace the hardcoded UUID.

---

**Issue 2 (LOW): Commented-out catalog/schema resources**

```hcl
# main.tf:96–147 — catalog, schema, grant resources all commented out
```

Consistent with ADR-001 (Jinja2 manages catalog/schema), but the commented code creates ambiguity about what was tried vs. what was intentionally deferred. A brief inline comment explaining the Jinja2 handoff would improve clarity.

---

**Issue 3 (LOW): Lifecycle ignore_changes reduces IaC guarantees**

```hcl
lifecycle {
  ignore_changes = [storage_root, owner]
}
```

Acceptable for metastore (which is hard to recreate), but worth noting: Terraform will not detect drift on these fields.

### infra/workload-dbx/variables.tf

**Status: Issues Found**

`catalog_name` and `schema_names` are commented out (lines 53–63) but are referenced in `Taskfile.yml` and passed as `-var` flags in `workload-dbx.yaml`. Without variable declarations, there is no type checking or default validation.

**Fix:** Either uncomment the variable declarations with appropriate defaults or remove the `-var` references from the workflow.

### infra/workload-dbx/providers.tf

**Status: Clean**

- Dual-provider pattern (`databricks.account`, `databricks.workspace`) is correct
- Both use `auth_type = "azure-cli"` — no stored credentials
- Provider aliasing is consistently applied across resource blocks

---

## GitHub Actions Workflows

### bootstrap.yaml

**Status: Clean**

- `workflow_dispatch` only — correct for a one-time operation
- Proper OIDC authentication
- Uses `-chdir` pattern consistently

### guardrails.yaml

**Status: Clean**

- Triggers on push to `main` and manual dispatch
- Budget start date calculated dynamically to current month
- Remote state backend configured correctly

### workload-azure.yaml

**Status: Issues Found**

**Issue (HIGH): Hardcoded storage account name**

```yaml
# workload-azure.yaml:29
ADLS_NAME: stdataabcdedata     # HACKME: Parameterize and write it on .env, etc.
```

Azure Storage Account names must be globally unique and lowercase. This value is hardcoded and will cause deployment failures for any second user or environment. The `HACKME` comment confirms this is known.

**Fix:** Move to a GitHub Secret (e.g., `ADLS_STORAGE_NAME`) and reference as `${{ secrets.ADLS_STORAGE_NAME }}`.

### workload-dbx.yaml

**Status: Issues Found**

**Issue (CRITICAL): Destroy step missing required variables**

The `Terraform Apply` step passes:
```yaml
-var="subscription_id=..."
-var="azure_tenant_id=..."
-var="resource_group_name=..."
-var="workspace_name=..."
-var="access_connector_id=..."
# ... and others
```

The `Terraform Destroy` step does **not** include these variables. Terraform will error with `variable not set` during destroy runs.

**Fix:** Mirror all `-var` flags from the apply step into the destroy step, or extract them to a shared `env` block.

---

## Security Assessment

### Positive Findings

| Control | Implementation |
|---------|---------------|
| No stored credentials | All secrets use GitHub Secrets; no PATs or service principal passwords in repo |
| OIDC authentication | `azure/login` with OIDC in all workflows; `auth_type = "azure-cli"` in providers |
| `.gitignore` coverage | `.env`, `*.tfvars`, `*.tfstate*`, `.terraform/` all excluded |
| TLS enforcement | `min_tls_version = "TLS1_2"` on all Storage Accounts |
| Private storage containers | `container_access_type = "private"` on all containers |
| Group-based RBAC | No inline user grants; EntraID group sync is the intended path (ADR-005) |

### Risks

| Risk | Location | Severity | Notes |
|------|----------|----------|-------|
| Hardcoded metastore UUID | `workload-dbx/main.tf:43` | HIGH | Environment-specific; breaks portability |
| Hardcoded ADLS name | `workload-azure.yaml:29` | HIGH | Must be unique globally; acknowledged with HACKME |
| Public network access on tfstate Storage Account | `bootstrap/main.tf` | LOW | Required for GitHub Actions runners; documented trade-off |
| No IP allowlist on Databricks workspace | `workload-azure/main.tf` | LOW | Documented in README as known production gap |

No credentials, tokens, or secrets were found anywhere in the codebase.

---

## Taskfile

**Status: Functional with concerns**

- 673 lines; includes tasks for `tf:init`, `tf:plan`, `tf:apply`, `tf:destroy`, Azure checks, Databricks checks, and state backend operations
- Lease-breaking safeguards are a good operational pattern
- Descriptive `desc` fields on all tasks

**Concerns:**

1. **FIXME on line 50:** `SCHEMAS_JSON` backslash escaping noted as a potential shell interpolation issue
2. **Commented-out tasks** add noise and make it harder to understand the current supported surface
3. **Inline bash one-liners** are difficult to test and maintain; complex logic would be clearer in helper scripts
4. **Multiple dotenv sources** (`dotenv: ['.env', '.env.dbx']`) — load order and override precedence should be documented

---

## Issues by Severity

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | CRITICAL | Destroy step missing required `-var` flags | `workload-dbx.yaml` destroy step |
| 2 | HIGH | Hardcoded environment-specific metastore UUID | `workload-dbx/main.tf:43` |
| 3 | HIGH | Hardcoded ADLS storage account name | `workload-azure.yaml:29` |
| 4 | MEDIUM | `catalog_name` / `schema_names` variables referenced but not declared | `workload-dbx/variables.tf` |
| 5 | LOW | Commented-out catalog/schema resources lack explanation | `workload-dbx/main.tf:96–147` |
| 6 | LOW | `SCHEMAS_JSON` escaping issue | `Taskfile.yml:50` |
| 7 | LOW | No `tflint` or `checkov` runs in CI/CD (tasks exist but not invoked) | `Taskfile.yml`, all workflows |
| 8 | LOW | `terraform.tfstate` in repo root suggests manual local execution | Repo root |

---

## Strengths

- **ADR-driven design** — decision records in README accurately reflect the implementation; trade-offs are explicitly documented
- **OIDC everywhere** — no long-lived credentials anywhere in the codebase
- **State isolation** — three separate tfstate files reduce blast radius
- **Layer separation** — bootstrap → guardrails → workload-azure → workload-dbx is a clean dependency chain
- **CI/CD discipline** — production execution is CI/CD-only; no manual apply path to main
- **Concurrency controls** — `concurrency: group:` in all workflow files prevents race conditions on shared state
- **Cost governance** — budget guardrails implemented at subscription level
- **Idempotency** — `lifecycle` blocks, `force_destroy`, and OIDC auth all support repeatable execution (ADR-003)
- **Documentation quality** — README, GETTING_STARTED, and CLAUDE.md are accurate, well-structured, and maintainable

---

## Recommendations

### Fix Now (low effort, high impact)

1. **Add `variable "metastore_id" {}`** to `workload-dbx/variables.tf` and replace the hardcoded UUID in `main.tf:43`
2. **Mirror `-var` flags** from the apply step to the destroy step in `workload-dbx.yaml`
3. **Move `ADLS_NAME`** to a GitHub Secret and reference it as `${{ secrets.ADLS_STORAGE_NAME }}` in `workload-azure.yaml`
4. **Uncomment or remove** `catalog_name` / `schema_names` variable declarations in `workload-dbx/variables.tf`

### Fix Soon (medium effort)

5. **Add a brief inline comment** above the commented-out catalog/schema block in `workload-dbx/main.tf` explaining the Jinja2 handoff (ADR-001)
6. **Add `tflint`** as a step in `workload-azure.yaml` and `workload-dbx.yaml` — the Taskfile task already exists
7. **Extract complex bash** from Taskfile into versioned helper scripts under `scripts/`

### Future Work (already documented in README)

- Jinja2 + Python Notebook catalog/schema management (ADR-001)
- View layer for data consumer access (ADR-004)
- EntraID group sync for RBAC (ADR-005)
- Multi-environment support
- Monitoring and alerting beyond budget guardrails

---

*Generated by Claude Code — claude-sonnet-4-6*
