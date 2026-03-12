# Runbook: Add OIDC Federated Credential for Pull Requests

**Issue:** #40
**Severity:** MEDIUM
**When to use:** Initial setup or after recreating the Entra ID app registration

---

## Problem

GitHub Actions tokens for `pull_request` events carry the OIDC subject:

```
repo:nobhri/azure-dbx-mock-platform:pull_request
```

If this subject is not listed as a federated credential on the app registration, Azure login fails with:

```
AADSTS700213: No matching federated identity record found for presented
assertion subject 'repo:nobhri/azure-dbx-mock-platform:pull_request'
```

This prevents `terraform plan` from running on PRs — reviewers cannot see the plan before merging.

---

## Fix (Azure Portal)

1. Go to **Azure Portal → Entra ID → App registrations**
2. Find the service principal used by CI (e.g., `sp-dbx-mock-platform` or similar)
3. Open **Certificates & secrets → Federated credentials**
4. Click **+ Add credential**
5. Fill in:
   - **Federated credential scenario:** `GitHub Actions deploying Azure resources`
   - **Organization:** `nobhri`
   - **Repository:** `azure-dbx-mock-platform`
   - **Entity type:** `Pull request`
   - **Name:** `github-pr` (or any descriptive name)
6. Click **Add**

---

## Verify

After adding the credential, trigger a PR that touches `infra/workload-azure/**` or `infra/workload-dbx/**`. The `Azure login (OIDC)` step should succeed and `terraform plan` output should appear in the workflow run.

---

## Existing Credentials

The app registration should already have credentials for:

| Subject | Event |
|---------|-------|
| `repo:nobhri/azure-dbx-mock-platform:ref:refs/heads/main` | Push to main |
| `repo:nobhri/azure-dbx-mock-platform:environment:...` | (if environment-scoped) |

The `pull_request` credential added here is **read-only** (plan-only) — no additional Azure RBAC permissions are needed beyond what the SP already has.
