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
│  Group → Workspace/Catalog assignment: Terraform             │
└──────────────────────────────────────────────────────────────┘
```

> **Current status:** Single workspace, single catalog (MVP). Multi-workspace structure above is the target design. See [Current Status (MVP)](#current-status-mvp) for details.

### Layer Separation (within each Workspace)

```
┌──────────────────────────────────────────────────────┐
│  Azure Layer                                         │
│  Terraform — managed by Infrastructure team          │
│  (VNet, Storage, RBAC, Databricks Workspace)         │
├──────────────────────────────────────────────────────┤
│  Databricks Account Layer                            │
│  Terraform — one-time setup only                     │
│  (Metastore creation, Storage credential binding)    │
├──────────────────────────────────────────────────────┤
│  Catalog / Schema Layer                              │
│  Jinja2 + Python Notebook — Data Platform team       │
│  (Environment-parametrized SQL, run via CI/CD)       │
├──────────────────────────────────────────────────────┤
│  Job / Workflow Layer                                │
│  Asset Bundles — Data Engineering team               │
│  (Idempotent ETL jobs, target-based deployment)      │
├──────────────────────────────────────────────────────┤
│  Table / View DDL Layer                              │
│  Jinja2 DDL (planned) / saveAsTable (MVP)            │
│  (Owned by Data Engineering)                         │
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

### ADR-001: Terraform for Infra/Metastore, SQL for Catalog/Schema

**Context:** Unity Catalog resources can be managed via Terraform or SQL. Which to use where?

**Decision:**

|Resource        |Tool             |Reason                                                  |
|----------------|-----------------|--------------------------------------------------------|
|Azure Resources |Terraform        |Network + security belong to infra team                 |
|Metastore       |Terraform        |One-time setup; state management critical               |
|Catalog / Schema|Jinja2 + SQL     |Data engineers can own it; no Terraform expertise needed|
|Tables          |SQL DDL (planned)|Data layer ownership stays with data team               |

**Trade-offs accepted:**

- SQL-managed catalog has no drift detection out of the box (mitigated by idempotent DDL + system table audit)
- Terraform state for Metastore must be carefully protected (separate backend)

**Rejected alternatives:**

- Full Terraform for everything → requires infra team involvement for every schema change (bottleneck)
- Asset Bundles for catalog → lifecycle mismatch; bundles are for jobs, not governance objects

-----

### ADR-002: OIDC Authentication Only

**Decision:** No stored secrets or service principal credentials in GitHub Actions. All Azure authentication uses OIDC federated identity.

**Reason:** Secrets rotate, leak, and get forgotten. OIDC has no secret to manage, integrates natively with Azure Entra ID, and scope is limited to the specific workflow and branch.

-----

### ADR-003: Idempotency as a First-Class Requirement

**Decision:** All DDL and DML operations must be idempotent. `CREATE IF NOT EXISTS`, `MERGE`, `mode("overwrite")` with explicit schema handling — no implicit assumptions about environment state.

**Reason:** Re-running a failed job should always be safe. This is especially important in a CI/CD pipeline where retry logic is automated.

-----

### ADR-004: Data Consumer Workspace — Access Pattern Options

**Context:** Data consumers need access to production data but should not operate in the platform prod workspace. How to expose data to them?

**Options considered:**

|Pattern                                    |Lineage visibility   |Cost                      |Complexity|
|-------------------------------------------|---------------------|--------------------------|----------|
|Direct access to prod catalog              |Full                 |Low                       |Low       |
|View layer in consumer catalog             |Partial (abstracted) |Low                       |Medium    |
|Materialized View layer in consumer catalog|None (fully isolated)|High (compute for refresh)|High      |

**Decision:** Default to **View layer in consumer catalog** — provides a clean abstraction boundary without the cost overhead of Materialized Views. Direct prod catalog access or full Materialized View isolation are available depending on governance requirements of each dataset.

**Trade-offs accepted:**

- View layer adds a maintenance surface (views must be updated when upstream schema changes)
- Materialized Views are intentionally avoided as default due to cost — reserved for cases where query performance or strict lineage isolation is explicitly required

-----

### ADR-005: Identity & Permission Model — Group-Based Access via EntraID Sync

**Decision:** Permissions are assigned to **EntraID Groups only — never to individual users**. All Workspace and Catalog permissions are granted to groups via Terraform. No `GRANT` to individual user principals anywhere in the platform.

**Reason:** Individual permission grants create drift that is nearly impossible to audit at scale. Group-based assignment ensures access is managed through a single source of truth (EntraID) and offboarding propagates automatically.

**Implementation notes:**

- EntraID Native Sync is preferred over SCIM provisioning (supports nested groups, lower setup complexity)
- Group-to-workspace and group-to-catalog assignments are parametrized in Terraform — adding a new workspace requires only a parameter change

-----

## Production Considerations

> These topics are **not implemented in this mock environment** due to cost and complexity constraints. They are documented here to demonstrate awareness of what a production-grade enterprise deployment requires.

### Network Isolation

#### VNet per Workspace

Each Databricks workspace requires its own VNet (or dedicated subnet range). In a multi-workspace architecture (dev / staging / prod / biz), this means managing multiple VNets and their peering relationships.

#### Hub-and-Spoke Topology

For enterprise environments connected to a corporate network, a hub-and-spoke model is typical:

- A shared hub VNet handles connectivity to on-premises or corporate networks (via ExpressRoute or VPN Gateway)
- Each workspace VNet is a spoke, peered to the hub
- All egress traffic routes through the hub for inspection and control

This adds significant setup effort but is usually non-negotiable in large organizations with existing network governance.

#### VNet Injection Scope — A Common Oversight

VNet Injection controls where compute nodes (clusters, Serverless) are deployed — it does not cover the Databricks Control Plane (Workspace UI, API, Job scheduler), which is a Databricks-managed SaaS endpoint. To restrict access to the Control Plane, a separate measure is required: either an IP Allowlist or Azure Private Link for the Control Plane endpoint. Treating VNet Injection alone as "network isolation complete" is a common oversight.

#### CI/CD Impact

Network isolation has a direct impact on CI/CD execution. GitHub-hosted runners operate from dynamic IPs and cannot reach a network-isolated workspace by default. Two options:

- **GitHub-hosted runner + IP allowlist**: Assign a static IP to the runner (via a NAT Gateway or similar) and add it to the Workspace IP access list
- **Self-hosted runner**: Deploy a runner inside the VNet — full network access, but adds operational overhead for runner maintenance

Neither option is free. Factor this in when deciding how aggressively to isolate the workspace network.

-----

### Storage Account Architecture

Storage Account architecture is the most consequential infrastructure decision in a Unity Catalog deployment — and the right answer depends on organizational requirements.

**Decision tree:**

```
Q: Can all Unity Catalog data live in a single Storage Account?
│
├─ Yes (cost simplicity, single team, uniform redundancy acceptable)
│   └─ Single Storage Account + VNet Injection
│       ✓ One Private Endpoint to manage
│       ✓ Simpler NCC configuration if using Serverless compute
│       ✗ No per-team cost attribution at Storage layer
│       ✗ Redundancy level (LRS / ZRS / GRS) unified across all data
│
└─ No (team-level cost separation needed, or Prod requires higher redundancy)
    └─ Multiple Storage Accounts
        ✓ Cost attribution per team or environment
        ✓ GRS for Prod, LRS for dev/staging (cost optimization)
        ✗ Private Endpoint required per Storage Account
        ✗ NCC configuration multiplies with each account
        ✗ Operational overhead increases significantly
```

**Recommendation:** Default to a single Storage Account unless there is a clear organizational requirement for cost separation or differential redundancy. The operational cost of managing multiple Private Endpoints and NCC configurations is frequently underestimated.

-----

### Serverless Compute & Network Configuration (NCC)

If Serverless compute is used (increasingly common as the default for jobs and SQL warehouses), **Network Connectivity Configuration (NCC)** must be explicitly set up to allow Serverless nodes to reach the Storage Account via Private Endpoint.

This is a common oversight: classic compute (with VNet Injection) reaches Storage through the injected VNet, but Serverless compute runs outside the customer VNet by default. Without NCC, Serverless jobs will fail to access Storage even if the rest of the network config is correct.

In a multi-Storage-Account setup, NCC configuration must be repeated for each account — another reason to prefer a single Storage Account where possible.

-----

## Current Status (MVP)

### Done

- Azure infrastructure provisioned via Terraform
- Databricks Workspace + Unity Catalog Metastore configured

### In Progress

- Asset Bundles with environment-specific targets (`dev`, `staging`, `prod`)
- SDLC variable parametrization across environments
- MVP ETL pipeline using `saveAsTable`
- Catalog/Schema management via Jinja2 + Python Notebook (replacing Terraform-managed catalog)
- GitHub Actions Workflow Dispatch for `dev`/`staging`
- ADR documentation
- README finalization for public release

### Known Issues

- Terraform `destroy` for managed catalog resources fails due to dependency ordering — workaround is documented, manual cleanup required in some cases
- `go-task` runner abstraction became complex; CI/CD integration needs simplification
- **Destroy order matters:** Always destroy `workload-dbx` before `workload-azure`. Destroying Azure first leaves Unity Catalog account-scope objects (`uc-mi-credential`, `uc-root-location`) orphaned — they must be deleted manually before re-applying. See [code-review-2026-03-03.md](docs/code-review-2026-03-03.md) for recovery steps.
- **Deploying this yourself:** Two GitHub repository secrets must be set before CI will succeed:
  - `ADLS_STORAGE_NAME` — name of the Storage Account used as Unity Catalog root storage
  - `TFSTATE_SA_UNIQ` — unique suffix of the Terraform state Storage Account name (`st<UNIQ>tfstate`)

-----

## Blog Series

Detailed write-ups on specific decisions:

- [ ] Terraform vs SQL for Unity Catalog Management — a real trade-off analysis
- [ ] Why I banned local `databricks bundle run`
- [ ] Asset Bundles parameter propagation: the bug and the fix
- [ ] Designing idempotent Databricks jobs
- [ ] OIDC authentication for Databricks on Azure — no secrets, no stress
- [ ] Terraform destroy and the cost incident: what I learned

*(Links will be added as articles are published)*

-----

## Author

**Nobuaki Hirai** — Data Platform Architect / Data Engineer  
Working at the intersection of cloud infrastructure, data governance, and organizational constraints.

[GitHub](https://github.com/nobhri)  · [LinkedIn](https://linkedin.com/)


---

## License

MIT