# Databricks Mock Platform

> A portfolio-grade reference architecture demonstrating how to design and operate a Databricks Data Platform — with a focus on **architectural decision-making**, not just tool usage.

-----

## What This Is

This repository is not a tutorial. It is an opinionated, constraint-aware implementation of a Databricks Data Platform on Azure.

**What it demonstrates:**

1. **Layered ownership thinking** — not "how do I use Terraform" but "what should Terraform own and why"
1. **Constraint-aware design** — decisions are made for a team with mixed tooling maturity, not an ideal greenfield org
1. **Decision documentation habit** — ADRs exist so future maintainers (and hiring managers) can understand the *why*, not just the *what*
1. **CI/CD discipline** — execution path policy is explicit and enforced, not just recommended
1. **Trade-off literacy** — each major choice includes what was rejected and why

The design intentionally reflects a common scenario: **a low-to-mid maturity organization** where infrastructure, data platform, and data engineering teams have different tooling capabilities and different incentives. The goal is to find the minimum viable architecture that is still principled.

-----

## Architecture Overview

### Workspace & Catalog Structure (Target State)

```
┌──────────────────────────────────────────────────────────────┐
│  Platform Workspaces (Terraform-managed)                     │
│                                                              │
│  dev workspace      ──→  dev catalog                         │
│  staging workspace  ──→  staging catalog                     │
│  prod workspace     ──→  prod catalog                        │
├──────────────────────────────────────────────────────────────┤
│  Data Consumer Workspace (Terraform-managed)                 │
│                                                              │
│  consumer workspace ──→  prod catalog (direct)               │
│                    or ──→  consumer catalog (View layer)     │
│                    or ──→  consumer catalog (MV layer)       │
│                             ↑ see ADR-004                    │
├──────────────────────────────────────────────────────────────┤
│  Identity & Access (EntraID-based)                           │
│                                                              │
│  EntraID Groups ──sync──→ Databricks                         │
│  Permissions assigned to Groups only — never to individuals  │
│  Group → Workspace/Catalog assignment: Platform Layer (SQL)  │
│                             ↑ see ADR-005                    │
└──────────────────────────────────────────────────────────────┘
```

> **Current status:** Single workspace, single catalog (MVP). Multi-workspace structure above is the target design. See [Current Status (MVP)](#current-status-mvp) for details.

### Layer Separation (within each Workspace)

```
┌──────────────────────────────────────────────────────┐
│  Azure Layer                                         │
│  Terraform — managed by Infrastructure team          │
│  (VNet, Storage, RBAC, Databricks Workspace)         │
│  ↑ see ADR-001 (Terraform scope), ADR-002 (OIDC)    │
├──────────────────────────────────────────────────────┤
│  Databricks Account Layer                            │
│  Terraform — one-time setup only                     │
│  (Metastore creation, Storage credential binding)    │
│  ↑ see ADR-001 (Terraform scope)                     │
├──────────────────────────────────────────────────────┤
│  Catalog / Schema / Permission Layer                 │
│  Jinja2 + Python Notebook — Data Platform team       │
│  (DDL + GRANT, config-driven, run via CI/CD)         │
│  ↑ see ADR-001 (not Terraform), ADR-005 (groups)    │
├──────────────────────────────────────────────────────┤
│  Job / Workflow Layer                                │
│  Asset Bundles — Data Engineering team               │
│  (Idempotent ETL jobs, target-based deployment)      │
│  ↑ see ADR-003 (idempotency)                         │
├──────────────────────────────────────────────────────┤
│  Table / View DDL Layer                              │
│  Jinja2 DDL (planned) / saveAsTable (MVP)            │
│  (Owned by Data Engineering)                         │
│  ↑ see ADR-004 (consumer access patterns)            │
└──────────────────────────────────────────────────────┘
```

### Why This Layering?

Each layer has a different **rate of change**, **team ownership**, and **failure blast radius**. Mixing them into a single tool or pipeline creates hidden coupling that eventually breaks — usually in production, usually at the worst time.

See the [Architecture Decision Records](#architecture-decision-records-adr) section for the reasoning behind each boundary.

-----

## Tech Stack

|Category     |Tools                                                  |
|-------------|-------------------------------------------------------|
|Cloud        |Azure (Subscription, VNet, Storage, Entra ID)          |
|IaC          |Terraform                                              |
|Data Platform|Databricks (Unity Catalog, Asset Bundles, Delta Lake)  |
|Governance   |Unity Catalog — Metastore, Catalog, Schema, Permissions|
|Templating   |Jinja2 (SQL parametrization)                           |
|Orchestration|GitHub Actions                                         |
|Auth         |OIDC (GitHub Actions → Azure, no stored secrets)       |
|Languages    |PySpark, SQL, Python, HCL                              |
|Task Runner  |go-task (local command abstraction)                    |

-----

## CI/CD Design

### Execution Path Policy

```
                        ┌──────────────┐
                        │  Developer   │
                        └──────┬───────┘
                               │ git push / PR
                               ▼
                     ┌─────────────────┐
                     │  GitHub Actions  │
                     └────────┬────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           [dev]          [staging]          [prod]
      Workflow Dispatch  Workflow Dispatch  main merge only
      (manual OK)        (manual OK)       (no manual trigger)
```

**Key constraints enforced by design:**

- `prod` deployments are triggered only via merge to main — no manual runs, no exceptions
- `dev` and `staging` allow `workflow_dispatch` for exploratory testing, but still go through GitHub Actions (not local bundle run)
- Local `databricks bundle run` is disallowed in the current MVP phase — all execution history lives in GitHub Actions
- Planned next phase: `dev` local runs enabled via VS Code extension, scoped to per-developer namespaces (isolated catalog/schema per developer)

**Why ban local bundle run in Phase 1?**

Because local runs bypass the audit trail, can accidentally target non-dev environments depending on profile config, and create a class of "it works on my machine" incidents that are hard to debug. Establishing the CI/CD-first discipline first — then selectively relaxing it — is safer than trying to add guardrails retroactively.

**Why allow it in Phase 2 (dev only)?**

The VS Code Databricks extension enables deployment into a personal developer namespace (isolated catalog/schema per developer), which eliminates the environment collision risk. With that isolation in place, local runs in `dev` become low-risk and improve developer experience without compromising `staging` or `prod` integrity.

-----

## Architecture Decision Records (ADR)

Each ADR explains a key design choice, what was rejected, and why. Full rationale is in
[`docs/adr/`](docs/adr/).

### ADR-001: Terraform for Infra/Metastore, SQL for Catalog/Schema

Terraform owns Azure resources and the UC Metastore; Catalog and Schema are managed via
Jinja2-parametrized SQL notebooks owned by the Data Platform team. This boundary separates
infrastructure (slow-changing, infra team) from governance objects (frequently changing, data team),
eliminating the bottleneck of requiring infra involvement for schema changes. The trade-off is that
SQL-managed catalog has no Terraform drift detection, mitigated by idempotent DDL.

See [ADR-001](docs/adr/001-terraform-scope.md) for full rationale.

-----

### ADR-002: OIDC Authentication Only — No Stored Secrets

No stored secrets or service principal client secrets are used in GitHub Actions — all Azure
authentication uses OIDC federated identity. OIDC has no secret to leak, rotate, or forget; scope
is limited to the specific workflow and branch. This eliminates an entire class of
credential-management incidents at the cost of a one-time setup in Entra ID.

See [ADR-002](docs/adr/002-oidc-auth.md) for full rationale.

-----

### ADR-003: Idempotency as a First-Class Requirement

All DDL and DML operations must be idempotent by construction: `CREATE IF NOT EXISTS`, `MERGE`,
`mode("overwrite")` with explicit schema handling — no implicit assumptions about environment state.
This ensures that re-running a failed CI/CD job is always safe, with no manual cleanup required.
Idempotency is treated as a correctness property, not an optimization.

See [ADR-003](docs/adr/003-idempotency.md) for full rationale.

-----

### ADR-004: Data Consumer Workspace — View Layer Access Pattern

Data consumers are isolated from the platform prod workspace via a View layer in a dedicated
consumer catalog — a clean abstraction boundary without the cost overhead of Materialized Views.
Direct prod catalog access and full Materialized View isolation remain available depending on
governance requirements of each dataset. Materialized Views are intentionally avoided as the default
due to compute cost.

See [ADR-004](docs/adr/004-consumer-access.md) for full rationale.

-----

### ADR-005: Identity & Permission Model — Group-Based Access via EntraID Sync

Permissions are assigned to Groups only — never to individual users. All Metastore-scoped grants
(Workspace, Catalog, Schema) are managed via Jinja2 + SQL Notebook in the Platform Layer.
Group-based assignment ensures access is managed through a single source of truth and offboarding
propagates automatically. In production, groups are sourced from EntraID via Native Sync; in this
mock environment, Databricks-native groups are used as a simplification. EntraID Native Sync is
preferred over SCIM for its support of nested groups and lower setup complexity.

See [ADR-005](docs/adr/005-group-permissions.md) for full rationale.

-----

## Production Considerations

These topics are not implemented in this mock environment due to cost and complexity constraints.
They are documented to demonstrate awareness of what a production-grade enterprise deployment
requires. Topics covered: VNet-per-workspace and hub-and-spoke topology, Storage Account
architecture (single vs multiple), and Serverless compute Network Connectivity Configuration (NCC).

See [`docs/design/production-considerations.md`](docs/design/production-considerations.md) for
the full write-up.

-----

## Current Status (MVP)

### Done

- Azure infrastructure provisioned via Terraform
- Databricks Workspace + Unity Catalog Metastore configured
- Catalog/Schema management via Jinja2 + Python Notebook (workload-catalog confirmed accessible 2026-03-08)
- Asset Bundles with environment-specific targets (`dev`, `staging`, `prod`)
- SDLC variable parametrization across environments
- GitHub Actions Workflow Dispatch for `dev`/`staging`
- ADR documentation (5 ADRs)

### In Progress

- MVP ETL pipeline using `saveAsTable`
- README finalization for public release

### Known Issues

- **Destroy order matters:** Always destroy `workload-dbx` before `workload-azure`. Destroying Azure first leaves Unity Catalog account-scope objects (`uc-mi-credential`, `uc-root-location`) orphaned. `force_destroy = true` on the metastore (PR [#50](https://github.com/nobhri/azure-dbx-mock-platform/pull/50)) now cascade-deletes notebook-created catalogs automatically — manual UC cleanup is no longer required when the correct destroy order is followed.
- **Post-destroy manual grants required:** After each full destroy + recreate cycle, the metastore admin must re-run both grants manually (the SP cannot self-grant account-level UC privileges):
  - `GRANT CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>';`
  - `GRANT CREATE CATALOG ON METASTORE TO '<SP_client_id>';` — required for the catalog/schema DDL workflow (see [issue #53](https://github.com/nobhri/azure-dbx-mock-platform/issues/53))
- **PR CI always fails Azure login:** OIDC federated credentials are not configured for the `pull_request` event subject — `terraform plan` cannot run on PRs. Fix: add `repo:nobhri/azure-dbx-mock-platform:pull_request` as a federated credential in Entra ID. See [issue #40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40).
- **Deploying this yourself:** Two GitHub repository secrets must be set before CI will succeed:
  - `ADLS_STORAGE_NAME` — name of the Storage Account used as Unity Catalog root storage
  - `TFSTATE_SA_UNIQ` — unique suffix of the Terraform state Storage Account name (`st<UNIQ>tfstate`)

-----

## Blog Series

Detailed write-ups on specific decisions:

- [x] **[Why I Built a Mock Data Platform — and What the CI/CD Taught Me](https://platform-notes.hashnode.dev/why-i-built-a-mock-data-platform-and-what-the-ci-cd-taught-me)**
  *A design journal for Terraform + Databricks + GitHub Actions: Part 1 — Workspace & Metastore*
  Repo snapshot: [blog/cicd-part1](https://github.com/nobhri/azure-dbx-mock-platform/tree/blog/cicd-part1)

- [ ] Terraform vs SQL for Unity Catalog Management — a real trade-off analysis
- [ ] Why I banned local `databricks bundle run`
- [ ] Asset Bundles parameter propagation: the bug and the fix
- [ ] Designing idempotent Databricks jobs
- [ ] OIDC authentication for Databricks on Azure — no secrets, no stress
- [ ] Terraform destroy and the cost incident: what I learned

-----

## Author

**Nobuaki Hirai** — Data Platform Architect / Data Engineer  
Working at the intersection of cloud infrastructure, data governance, and organizational constraints.

[GitHub](https://github.com/nobhri)  · [LinkedIn](https://linkedin.com/)


---

## License

MIT