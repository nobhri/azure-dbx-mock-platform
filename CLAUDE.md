# CLAUDE.md

## Project
Databricks Mock Platform — architecture decision showcase for portfolio.

## Stack
Azure, Terraform, Databricks, Asset Bundles, Unity Catalog, Jinja2, GitHub Actions, PySpark, SQL

## Conventions
- Language: English for all code, comments, and commit messages
- Commits: conventional commits (feat:, fix:, docs:, refactor:)
- Terraform: infra layer only (Azure + Metastore)
- Catalog/Schema: Jinja2 + Python Notebook (not Terraform)

## Git
- Branch naming: feature/, fix/, docs/
- Always create a new branch before making any changes
- Never commit directly to main
- Always create PR to main, never push to main directly
- Always work inside a git worktree, never in the main working tree
- At session start, create a worktree before touching any files:
    `git worktree add ../azure-dbx-mock-platform-worktrees/<branch-name> -b <branch-name>`
- Each worktree gets its own branch; all worktrees target main via PR

## Command Style
- Never chain git or gh commands with `&&`, `;`, or `|`
- Run each git/gh command separately: `git add .` then `git commit -m "..."` then `git push`
- Other commands may use `&&` when needed
- This ensures --allowedTools patterns match correctly

## Issue References
- In PR descriptions and commit messages, use `refs #XX` or `relates to #XX`
- NEVER use `fixes`, `closes`, or `resolves` followed by issue numbers
- Issues are closed manually by the human after CI/CD verification

## Autonomy Level
- All git operations (fetch, worktree, add, commit, push, status, diff, log, merge) run without asking
- Viewing GH Actions runs (`gh run view/list`), PRs (`gh pr view/list`), and issues (`gh issue view/list`) runs without asking
- You must STOP and ask before creating a PR (`gh pr create`) or issue (`gh issue create`)
- Never merge, approve, or delete anything
- Never run `gh workflow run` or `gh api` to trigger workflows
- Never run `gh pr merge` or `gh pr review --approve`

## Forbidden Commands
- Never run: rm -rf, git push --force, terraform destroy
- Never modify .git/ directory directly
- Never touch files outside this repository

## Security
- Never read, cat, or access: .env, *.tfvars, any file containing credentials
- Never run: env, printenv, echo $ARM_CLIENT_SECRET, or similar
- Use variable names as placeholders, never actual values

## Key Design Decisions
- See `docs/adr/` for full ADR rationale; README has 2-3 sentence summaries with links
- Do not move Catalog/Schema management back to Terraform
- Prod execution: CI/CD only, no manual runs

## Session Start Checklist
Run these steps in order before touching any files:

1. Read `docs/status.md`
2. Glob `docs/sessions/YYYY-MM-DD-*.md` to determine the next NNN for today
3. Fetch and create worktree from latest main (prevents merge conflicts):
   `git fetch origin main`
   `git worktree add .claude/worktrees/<branch> -b <branch> origin/main`
   - Branch name should include the NNN (e.g., `docs/2026-03-10-009-slug`) to ensure uniqueness
4. Create the session file from the template in `docs/sessions/README.md`

## Session End Checklist
Before finishing:

1. Ensure the session file has **Outcome** and all **Artifacts** filled in
2. Update `docs/status.md` if any issues were opened, closed, or changed severity

## Common Mistakes
- **Using `fixes #XX` or `closes #XX` in commits**: This auto-closes issues on merge. Use `refs #XX` instead. Issues are closed manually after CI/CD verification.
- **Duplicate session NNN**: Always glob before picking the next NNN. Parallel sessions on the same date must each check for the highest existing number independently.
- **Forgetting status.md update**: If you opened or changed an issue, update `docs/status.md` before finishing the session.
- **Skipping worktree creation**: Never edit files in the main working tree. All changes go through a worktree branch → PR → main.
- **Branching from stale HEAD**: Always pass `origin/main` as the base when creating a worktree. Branching from local HEAD without fetching first causes merge conflicts when main has moved.

## Task Types
- **Architecture**: changes that affect ADRs, infra design, or cross-layer contracts → read relevant ADRs first
- **Implementation**: code/config changes within an established decision → read the ADR that governs the layer
- When in doubt, treat the task as Architecture and review ADRs before writing any code

## Architecture Awareness
Read these docs before starting each task type:
- **Infrastructure** (Terraform, Azure): ADR-001, ADR-002, ADR-003
- **Catalog / Schema**: ADR-001, ADR-004, ADR-005
- **ETL / PySpark**: ADR-006, ADR-007
- **CI/CD**: `.github/workflows/` for the affected workflow + any referenced ADRs
- All ADRs live in `docs/adr/`; summaries with links are in README

## Issue Rules
- Open issues track work not yet merged to main and verified by CI
- Close issues only after the relevant CI run on main succeeds
- Use `refs #XX` in commits and PR descriptions — never `fixes`, `closes`, or `resolves`
- Closing is a manual human action after CI confirmation

## Docs Location
- `docs/adr/` — durable architecture decisions (ADR-001 through ADR-007)
- `docs/design/` — production considerations and design notes
- `docs/sessions/` — per-session working notes (not polished docs)
- `docs/status.md` — live snapshot of open issues and architecture state
