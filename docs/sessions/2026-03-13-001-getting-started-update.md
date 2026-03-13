# Session 2026-03-13-001 — getting-started-update

**Branch:** docs/2026-03-13-001-getting-started-update
**Issue:** #106
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Update GETTING_STARTED.md to reflect the current state of the repo:
- Move GitHub Secrets summary to a later section (not prerequisites)
- Update repository structure to include platform/, etl/, and all workflow files
- Update OIDC section with correct GitHub Secret names
- Update Deployment Steps to reflect all workflows and step-by-step ordering requirement
- Add orchestrator option after initial setup
- Update Common Pitfalls (remove solved storage account hardcode issue)
- Delete .gitignore Recommendations section
- Update Definition of Done

## What was done

Rewrote GETTING_STARTED.md with the above changes. Key structural changes:
- Prerequisites table replaced with a lean list (only truly upfront requirements)
- Repository structure updated to include infra/workload-catalog, platform/, etl/
- Deployment Steps expanded to 8 steps (bootstrap → guardrails → azure → dbx → manual grants → catalog → etl → orchestrator option)
- GitHub Secrets Reference moved to an appendix section after deployment steps
- Removed .gitignore Recommendations section (users can check the actual file)
- Updated Definition of Done

## Artifacts

- `GETTING_STARTED.md` updated
- `docs/sessions/2026-03-13-001-getting-started-update.md` (this file)
