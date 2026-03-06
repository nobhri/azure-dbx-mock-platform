# ADR-001: Terraform for Infra/Metastore, SQL for Catalog/Schema

**Status:** Accepted
**Date:** 2026-02-01

---

## Context

Unity Catalog resources — Catalogs, Schemas, Grants — can be managed either via Terraform
(`databricks_catalog`, `databricks_schema`, `databricks_grant`) or via SQL DDL run from a notebook
or SQL warehouse. Both approaches work. The question is which tool should own which layer, and why.

The design constraint is a **low-to-mid maturity organization** where infrastructure, data platform,
and data engineering teams have different tooling capabilities and different incentives.

---

## Decision

| Resource        | Tool              | Reason                                                   |
|-----------------|-------------------|----------------------------------------------------------|
| Azure Resources | Terraform         | Network + security belong to infra team                  |
| Metastore       | Terraform         | One-time setup; state management is critical             |
| Catalog / Schema| Jinja2 + SQL      | Data engineers can own it; no Terraform expertise needed |
| Tables          | SQL DDL (planned) | Data layer ownership stays with data team                |

Terraform owns Azure resources (VNet, Storage, RBAC, Databricks Workspace) and the UC Metastore
(account-scope, one-time setup). Catalog and Schema are managed via Jinja2-parametrized SQL
notebooks, owned and run by the Data Platform team via CI/CD.

---

## Trade-offs Accepted

- SQL-managed catalog has no drift detection out of the box — mitigated by idempotent DDL and
  system table audit.
- Terraform state for the Metastore must be carefully protected (separate remote backend).
- Two different mental models in the same codebase; developers must understand the boundary.

---

## Rejected Alternatives

**Full Terraform for everything** — requires infra team involvement for every schema change.
This is a bottleneck: data engineers cannot ship schema changes without filing an infra ticket.
Eliminated because it misaligns tool ownership with team ownership.

**Asset Bundles for catalog** — lifecycle mismatch. Bundles are designed for jobs and workflows,
not for persistent governance objects like Catalogs and Schemas. Using bundles for catalog
management would force a destroy/recreate pattern on objects that should be long-lived.

**Raw SQL notebooks without Jinja2** — environment parametrization (dev/staging/prod catalog names)
requires string interpolation. Without Jinja2, notebooks would need either hardcoded environment
names or Databricks widget inputs, both of which break CI/CD-clean execution.

---

## Consequences

- The Data Platform team can ship schema changes via PR + CI/CD with no infra involvement.
- Adding a new environment requires updating Jinja2 templates and CI/CD variables, not Terraform
  resources — a data engineer can do this.
- Drift between actual UC state and expected state is detected at apply time (DDL `IF NOT EXISTS`
  is idempotent but will not detect deletions). This is an accepted trade-off for the MVP phase.
