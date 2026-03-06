# ADR-002: OIDC Authentication Only — No Stored Secrets

**Status:** Accepted
**Date:** 2026-02-01

---

## Context

GitHub Actions workflows need to authenticate to Azure (for Terraform) and to the Databricks
workspace (for bundle deploy/run). Authentication options include:

1. Stored secrets (client secret, SP credentials) in GitHub repository secrets
2. OIDC federated identity (no secret, short-lived token exchange)

---

## Decision

No stored secrets or service principal client secrets are used in GitHub Actions. All Azure
authentication uses **OIDC federated identity** via GitHub's `actions/azure-login` action with
`federated-credential`.

Databricks authentication is derived from the Azure token (the SP that has Workspace Admin and
Account Admin roles).

---

## Rationale

Secrets have four failure modes:

1. **Rotation neglect** — secrets that should be rotated every 90 days often aren't.
2. **Leak surface** — secrets in CI logs, error messages, or env dumps are not recoverable.
3. **Scope creep** — SP client secrets often have broader scope than needed because narrowing
   them is friction.
4. **Offboarding gap** — when a team member who created the secret leaves, rotation is often
   missed.

OIDC eliminates all four: there is no secret to rotate, nothing to leak, scope is limited to the
specific workflow subject (`repo:owner/repo:ref:refs/heads/main`), and offboarding the SP means
revoking the federated credential — which immediately blocks all workflows without a rotation step.

---

## Trade-offs Accepted

- OIDC requires one-time setup (Entra ID app registration + federated credential). More complex
  than pasting a secret.
- PR-triggered workflows (`pull_request` event) require a separate federated credential with
  `pull_request` subject. Without it, Azure login fails on PR CI runs. This is a known operational
  gap — tracked in [issue #40](https://github.com/nobhri/azure-dbx-mock-platform/issues/40).
- OIDC tokens are short-lived (1 hour). Long-running workflows must be split or re-authenticated.

---

## Rejected Alternatives

**Stored client secret in GitHub Secrets** — eliminated. Secrets have the failure modes described
above and provide no audit trail of their use beyond GitHub audit log.

**Azure Managed Identity on self-hosted runner** — valid option for enterprise environments with
a self-hosted runner inside the VNet. Rejected here because self-hosted runners add operational
overhead (maintenance, patching, scaling) that is out of scope for the MVP.

---

## Consequences

- CI/CD pipelines have no long-lived credentials to protect.
- Adding a new target environment requires adding a federated credential subject — a deliberate
  friction point that prevents unauthorized environment targets.
- The PR CI gap (issue #40) is the main operational debt of this decision and requires a one-time
  Entra ID update to resolve.
