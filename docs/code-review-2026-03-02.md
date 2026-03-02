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

**Observation:** `terraform.tfstate` exists in the repo root, indicating a local Terraform run was executed outside the `infra/` layer. This file is correctly excluded by `.gitignore` but suggests manual execution occurred outside the intended CI/CD path. → [Issue #12](https://github.com/nobhri/azure-dbx-mock-platform/issues/12)

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

**Issue 0 (CRITICAL): `var.catalog_name` referenced but undeclared — RESOLVED (PR #14)**

```hcl
# main.tf:41 — original
name = var.catalog_name
```

`catalog_name` was commented out in `variables.tf` but still referenced as the metastore name in `main.tf:41`. `terraform validate` surfaced this. Replaced with the hardcoded `"mvp-metastore"` (restoring the original intent visible in the commented line above). Fixed in PR #14 (`fix/var-flag-mismatches-issue-6`).

---

**Issue 1 (HIGH): Hardcoded metastore UUID — RESOLVED (PR #3)**

```hcl
# main.tf:43 — original
storage_root = "abfss://${var.uc_root_container}@${var.storage_account_name}.dfs.core.windows.net/30ebd5eb-ba32-4617-b715-1bbad2ad51e0"
```

The UUID was environment-specific. Any redeployment to a different subscription would silently produce a wrong storage path.

**Resolution:** `variable "metastore_id" {}` added to `variables.tf` and `main.tf` updated to reference `var.metastore_id`. Secret `METASTORE_ID` added to the GitHub Actions workflow. Fixed in PR #3 (`feat/metastore-id-variable`).

---

**Issue 2 (LOW): Commented-out catalog/schema resources** → [Issue #9](https://github.com/nobhri/azure-dbx-mock-platform/issues/9)

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

**Status: RESOLVED — PR #14**

Two categories of variable mismatch existed between `variables.tf` and the `-var` flags in `workload-dbx.yaml`: → [Issue #6](https://github.com/nobhri/azure-dbx-mock-platform/issues/6)

**Undeclared variables passed from CI (Terraform errors 1–2):**

`catalog_name` and `schema_names` were commented out (lines 58–68) but still passed as `-var` flags in the Plan, Apply, and Destroy steps. Terraform rejected them with `Value for undeclared variable`.

**Declared variables never passed from CI (Terraform errors 3–5):**

Three variables were declared in `variables.tf` with no default and no corresponding `-var` flag in any workflow step:

| Variable | Declared at | Available source |
|----------|-------------|-----------------|
| `subscription_id` | `variables.tf:2` | `${{ secrets.AZURE_SUBSCRIPTION_ID }}` |
| `azure_tenant_id` | `variables.tf:7` | `${{ secrets.AZURE_TENANT_ID }}` |
| `resource_group_name` | `variables.tf:17` | `rg-mock-data` (matches `workload-azure` default) |

**Resolution:** Removed the two undeclared `-var` flags and added the three missing ones to all steps. `CATALOG_NAME`/`SCHEMAS` env vars replaced with `RG_NAME: rg-mock-data`. Fixed in PR #14 (`fix/var-flag-mismatches-issue-6`). Confirmed by CI run [22561717749](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22561717749) — no `Value for undeclared variable` errors.

**Separate issue — empty secret:** The CI log shows `-var="databricks_account_id="` — the `DATABRICKS_ACCOUNT_ID` GitHub Secret resolves to an empty string. This is a repo configuration issue, not a code fix. Because `databricks_metastore.this` uses `provider = databricks.account`, Terraform refreshes state via the account-scope provider on every operation — **all three steps (Plan, Apply, Destroy) are blocked** until the secret is populated. → [Issue #15](https://github.com/nobhri/azure-dbx-mock-platform/issues/15) *(consolidates closed #8)*

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

**Issue (HIGH): Hardcoded storage account name** → [Issue #7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7)

```yaml
# workload-azure.yaml:29
ADLS_NAME: stdataabcdedata     # HACKME: Parameterize and write it on .env, etc.
```

Azure Storage Account names must be globally unique and lowercase. This value is hardcoded and will cause deployment failures for any second user or environment. The `HACKME` comment confirms this is known.

**Fix:** Move to a GitHub Secret (e.g., `ADLS_STORAGE_NAME`) and reference as `${{ secrets.ADLS_STORAGE_NAME }}`.

### workload-dbx.yaml

**Status: RESOLVED — PR #14**

**Issue (CRITICAL): Variable mismatch between workflow and variables.tf — 5 Terraform errors — RESOLVED** → [Issue #6](https://github.com/nobhri/azure-dbx-mock-platform/issues/6)

The CI apply step originally produced the following errors simultaneously:

```
Error: Value for undeclared variable — "catalog_name"
Error: Value for undeclared variable — "schema_names"
Error: No value for required variable — "subscription_id"   (variables.tf:2)
Error: No value for required variable — "azure_tenant_id"   (variables.tf:7)
Error: No value for required variable — "resource_group_name" (variables.tf:17)
```

**Resolution (PR #14, `fix/var-flag-mismatches-issue-6`):**
- Removed `-var="catalog_name=..."` and `-var='schema_names=[...]'` from all three steps (Plan, Apply, Destroy)
- Added `-var="subscription_id=${{ secrets.AZURE_SUBSCRIPTION_ID }}"`, `-var="azure_tenant_id=${{ secrets.AZURE_TENANT_ID }}"`, `-var="resource_group_name=$RG_NAME"` to all three steps
- Replaced `CATALOG_NAME`/`SCHEMAS` env vars with `RG_NAME: rg-mock-data`
- Also fixed `main.tf:41` which referenced undeclared `var.catalog_name` (caught by `terraform validate`)

Verified by CI run [22561717749](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22561717749) — all 5 variable errors resolved; Apply now progresses past variable validation.

**Partially fixed earlier — PR #5:** `workspace_name` was absent from the `Terraform Destroy` step only; added in PR #5 (`fix/destroy-var-parity`).

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
| ~~Hardcoded metastore UUID~~ | `workload-dbx/main.tf:43` | HIGH | **Fixed — PR #3** |
| Hardcoded ADLS name | `workload-azure.yaml:29` | HIGH | Must be unique globally; acknowledged with HACKME — [Issue #7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7) |
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

1. **FIXME on line 50:** `SCHEMAS_JSON` backslash escaping noted as a potential shell interpolation issue → [Issue #10](https://github.com/nobhri/azure-dbx-mock-platform/issues/10)
2. **Commented-out tasks** add noise and make it harder to understand the current supported surface
3. **Inline bash one-liners** are difficult to test and maintain; complex logic would be clearer in helper scripts
4. **Multiple dotenv sources** (`dotenv: ['.env', '.env.dbx']`) — load order and override precedence should be documented

---

## Issues by Severity

| # | Severity | Issue | Location | GitHub Issue | Status |
|---|----------|-------|----------|--------------|--------|
| 1 | CRITICAL | 5 variable mismatches between workflow `-var` flags and `variables.tf`: 2 undeclared vars passed, 3 required vars never passed; `main.tf:41` referencing undeclared `var.catalog_name` | `workload-dbx.yaml` all steps + `workload-dbx/variables.tf` + `main.tf:41` | [#6](https://github.com/nobhri/azure-dbx-mock-platform/issues/6) | **Fixed — PR #14** |
| 1a | — | `workspace_name` absent from Destroy step only | `workload-dbx.yaml` destroy step | — | **Fixed — PR #5** |
| 2 | HIGH | Hardcoded environment-specific metastore UUID | `workload-dbx/main.tf:43` | — | **Fixed — PR #3** |
| 3 | HIGH | Hardcoded ADLS storage account name | `workload-azure.yaml:29` | [#7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7) | Open |
| 4 | HIGH | `DATABRICKS_ACCOUNT_ID` GitHub Secret is empty — blocks Plan, Apply, and Destroy (account-scope provider refresh fails on all operations) | GitHub repo secrets | [#15](https://github.com/nobhri/azure-dbx-mock-platform/issues/15) | Partially resolved — secret added; new blocker: SP lacks Databricks Account Admin role (see #15 comment) |
| 5 | LOW | Commented-out catalog/schema resources lack explanation | `workload-dbx/main.tf:96–147` | [#9](https://github.com/nobhri/azure-dbx-mock-platform/issues/9) | Open |
| 6 | LOW | `SCHEMAS_JSON` escaping issue | `Taskfile.yml:50` | [#10](https://github.com/nobhri/azure-dbx-mock-platform/issues/10) | Open |
| 7 | LOW | No `tflint` or `checkov` runs in CI/CD (tasks exist but not invoked) | `Taskfile.yml`, all workflows | [#11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11) | Open |
| 8 | LOW | `terraform.tfstate` in repo root suggests manual local execution | Repo root | [#12](https://github.com/nobhri/azure-dbx-mock-platform/issues/12) | Open |

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

1. ~~**Add `variable "metastore_id" {}`** to `workload-dbx/variables.tf` and replace the hardcoded UUID in `main.tf:43`~~ **Done — PR #3**
2. ~~**Fix variable mismatch** in `workload-dbx.yaml`: remove `-var="catalog_name=..."` and `-var='schema_names=[...]'` from all 3 steps; add `-var="subscription_id=..."`, `-var="azure_tenant_id=..."`, `-var="resource_group_name=rg-mock-data"` to all 3 steps. Also fix `main.tf:41` referencing undeclared `var.catalog_name`.~~ **Done — PR #14** → [Issue #6](https://github.com/nobhri/azure-dbx-mock-platform/issues/6)
3. **Grant Databricks Account Admin to the OIDC Service Principal** — `DATABRICKS_ACCOUNT_ID` secret was added (run [22562713330](https://github.com/nobhri/azure-dbx-mock-platform/actions/runs/22562713330)), but `databricks_metastore.this` refresh now fails with `This API is disabled for users without account admin status`. The SP (`AZURE_CLIENT_ID`) must be added to **Databricks Account Console → User Management → Service Principals** with Account Admin role. No code change required. → [Issue #15](https://github.com/nobhri/azure-dbx-mock-platform/issues/15)
4. **Move `ADLS_NAME`** to a GitHub Secret and reference it as `${{ secrets.ADLS_STORAGE_NAME }}` in `workload-azure.yaml` → [Issue #7](https://github.com/nobhri/azure-dbx-mock-platform/issues/7)

### Fix Soon (medium effort)

5. **Add a brief inline comment** above the commented-out catalog/schema block in `workload-dbx/main.tf` explaining the Jinja2 handoff (ADR-001) → [Issue #9](https://github.com/nobhri/azure-dbx-mock-platform/issues/9)
6. **Add `tflint`** as a step in `workload-azure.yaml` and `workload-dbx.yaml` — the Taskfile task already exists → [Issue #11](https://github.com/nobhri/azure-dbx-mock-platform/issues/11)
7. **Extract complex bash** from Taskfile into versioned helper scripts under `scripts/`

### Future Work (already documented in README)

- Jinja2 + Python Notebook catalog/schema management (ADR-001)
- View layer for data consumer access (ADR-004)
- EntraID group sync for RBAC (ADR-005)
- Multi-environment support
- Monitoring and alerting beyond budget guardrails

---

*Generated by Claude Code — claude-sonnet-4-6*
