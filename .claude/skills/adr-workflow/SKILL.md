---
name: adr-workflow
description: Use when creating a new ADR or making an architecture decision
---

## ADR Workflow

Follow these 5 steps when a new architectural decision is needed:

1. **Context Review** — Read `docs/adr/` to understand existing decisions. Identify the highest existing ADR number.
2. **Discussion** — Present the problem, options, and trade-offs to the user. Agree on the chosen option before writing.
3. **Draft** — Create `docs/adr/NNN-slug.md` using the same structure as existing ADRs (Status, Context, Decision, Consequences).
4. **PR** — Commit the ADR on a `docs/` branch, open a PR with `refs #XX` if an issue exists. Do not merge.
5. **Post-merge** — After PR merges to main and CI passes, update `docs/status.md` and add a summary + link in README under the Architecture Decisions section.
