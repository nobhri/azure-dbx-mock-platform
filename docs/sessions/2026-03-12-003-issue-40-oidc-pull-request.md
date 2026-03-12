# Session 2026-03-12-003 — issue-40-oidc-pull-request

**Branch:** fix/2026-03-12-003-issue-40-oidc-pull-request
**Issue:** #40
**PR:** #160
**Outcome:** completed

## Objective

Add OIDC federated credential for the `pull_request` subject to the Entra ID app registration so that PR CI can authenticate to Azure and run `terraform plan`.

## What was done

- Updated `GETTING_STARTED.md` OIDC setup section to include a second `az ad app federated-credential create` call for the `pull_request` subject alongside the existing `main` branch credential
- Added a Common Pitfalls entry for `AADSTS700213: No matching federated identity record found` pointing to the fix
- User requested CLI option instead of Azure Portal steps — delivered as `az` CLI command in the existing script block
- Fixed a bug caught during live testing: credential `name` field cannot contain `/` (Azure rejects it as an invalid URI segment); added `REPO_SLUG=$(echo "$REPO" | tr '/' '-')` and used it for `name` while keeping `$REPO` for `subject`; same latent bug existed in the pre-existing main-branch credential line and was fixed at the same time

## Decisions

- Docs-only change: the actual credential must be added manually in Azure; no code change needed in CI workflows
- CLI approach preferred over Azure Portal steps (user request)

## Lessons / Notes

- Azure federated credential `name` must be a valid URI last segment — no slashes. The `subject` field uses the full `repo:owner/repo:...` format (slashes are fine there). Always derive a slug when building the name from a repo path.

## Artifacts

- `GETTING_STARTED.md` — updated OIDC setup section and Common Pitfalls
- PR #160
