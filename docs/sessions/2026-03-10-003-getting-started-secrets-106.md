# Session 2026-03-10-002 — Fix GETTING_STARTED.md secrets table (Issue #106)

## Goal
Fix the prerequisites / secrets table in GETTING_STARTED.md:
- Remove stale `METASTORE_ID` (dynamic discovery introduced in PR #81)
- Add missing `ADLS_STORAGE_NAME` (used by `workload-azure.yaml`)
- Add missing `ALERT_EMAIL` (used by `guardrails.yaml`)

## Changes
- `GETTING_STARTED.md` — prerequisites table: added `ADLS_STORAGE_NAME` and `ALERT_EMAIL`; kept table accurate
- `GETTING_STARTED.md` — OIDC setup code block: replaced `METASTORE_ID` with `ADLS_STORAGE_NAME` and `ALERT_EMAIL`

## Verification
Secrets confirmed by grepping all `.github/workflows/*.yaml` files:
- `ADLS_STORAGE_NAME` → `workload-azure.yaml` `ADLS_NAME` env var
- `ALERT_EMAIL` → `guardrails.yaml` env var
- `METASTORE_ID` → not referenced in any workflow (removed by PR #81)

## PR
refs #106
