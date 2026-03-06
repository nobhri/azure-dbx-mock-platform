# ADR-003: Idempotency as a First-Class Requirement

**Status:** Accepted
**Date:** 2026-02-01

---

## Context

CI/CD pipelines fail and are retried. Jobs fail mid-run and are re-triggered. In a Databricks
environment, this means DDL operations (`CREATE TABLE`, `CREATE SCHEMA`) and DML operations
(`INSERT`, `UPDATE`) may be re-executed against existing state. How should the platform handle
re-execution?

---

## Decision

All DDL and DML operations in this platform must be **idempotent by construction**:

- `CREATE CATALOG IF NOT EXISTS <name>`
- `CREATE SCHEMA IF NOT EXISTS <catalog>.<name>`
- `MERGE INTO` for upsert patterns (not `INSERT`)
- `mode("overwrite")` with explicit schema handling for Spark writes — not `mode("append")`
  unless append is the intentional semantic
- No operations that assume a clean slate (no `DROP TABLE` followed by `CREATE TABLE`)

Idempotency is treated as a **correctness property**, not an optimization.

---

## Rationale

In a CI/CD pipeline, re-running a failed job should always be safe — without manual cleanup, without
human intervention, and without checking what state the environment was in before the failure.

If a job is non-idempotent, every failure requires a human to assess the blast radius and potentially
clean up before the retry. This:

1. Blocks automated retries (you cannot safely retry without inspection)
2. Creates an on-call burden disproportionate to the failure severity
3. Makes partial failures much harder to reason about

---

## Trade-offs Accepted

- `IF NOT EXISTS` guards do not detect deletions — if a schema is deleted outside of CI/CD,
  the next apply will recreate it but the deletion will not be caught. This is acceptable for the
  MVP; a system-table audit log can detect this pattern post-hoc.
- `mode("overwrite")` has higher compute cost than incremental writes for large tables. The trade-off
  is accepted: correctness and simplicity over cost optimization in the MVP phase.
- Idempotent MERGE patterns require a well-defined primary key on every managed table. This is a
  design constraint that must be enforced at schema design time.

---

## Rejected Alternatives

**Truncate-and-reload without `IF NOT EXISTS`** — non-idempotent. A failure between `DROP TABLE`
and `CREATE TABLE` leaves the environment in a broken state that requires manual recovery.

**`INSERT` without deduplication** — produces duplicates on retry. Rejected because data correctness
in staging and prod cannot depend on "the job never runs twice".

---

## Consequences

- All notebooks and SQL templates must include `IF NOT EXISTS` guards on object creation.
- All Spark writes must specify an explicit write mode; implicit defaults are not acceptable.
- The idempotency requirement is documented here so reviewers can flag violations in PR review
  without needing to re-derive the policy from first principles each time.
