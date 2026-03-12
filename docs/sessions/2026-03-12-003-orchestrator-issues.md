# Session 2026-03-12-003 — orchestrator-issues

**Branch:** docs/2026-03-12-003-orchestrator-issues
**Issue:** #162, #163
**PR:** #TBD
**Outcome:** completed

## Objective

Review the orchestrator workflow design document, finalize open decisions,
and create GitHub Issues for implementation.

## What was done

1. Reviewed the orchestrator workflow design proposal
2. Resolved all open decisions:
   - Naming: `orchestrator-up.yaml` / `orchestrator-down.yaml` (avoided `platform-` prefix due to `platform/` directory collision)
   - Post-destroy grants: noted in issue as known manual step (no automation needed now)
   - PR strategy: single PR for all changes
   - March 31 VNet change: tracked as separate issue
3. Created Issue #162 — orchestrator workflows for cost-optimized deploy/destroy
4. Created Issue #163 — VNet default change verification after March 31
5. Updated status.md and session file

## Decisions

- **Workflow naming:** `orchestrator-up` / `orchestrator-down` chosen over `platform-up` / `platform-down` to avoid confusion with the `platform/` directory at repo root
- **Single PR:** All workflow changes (workflow_call additions + new orchestrator files) in one PR since they are tightly coupled
- **Post-destroy grants:** Documented as a note in the issue, not automated — recent cycles have not hit errors

## Artifacts

- Issue #162: Add orchestrator workflows for cost-optimized deploy and destroy sequences
- Issue #163: Verify NAT Gateway and Serverless behavior after March 31 VNet default change
- Updated `docs/status.md`
