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
- Use git worktrees (`.claude/worktrees/<branch-name>`) for parallel sessions (e.g. tmux with multiple Claude Code terminals)
- Each worktree gets its own branch; all worktrees target main via PR

## Autonomy Level
- You may edit, commit, push, and create PRs without asking
- You may view GitHub Actions run status and logs
- You must STOP and wait for human review at PR creation
- Never merge, approve, or delete anything
- Never run `gh workflow run` or `gh api` to trigger workflows
- Never run `gh pr merge` or `gh pr review --approve`
- Your job ends at `gh pr create`

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

## Session Lifecycle
- At session start: read `docs/status.md` before running any `gh` commands
- At session end: update `docs/status.md` if any issues were opened, closed, or changed severity

## Session File Naming
- Session notes go in `docs/sessions/YYYY-MM-DD-NNN-slug.md`
- NNN is a zero-padded 3-digit sequence (001, 002, ...)
- Determine next NNN by globbing `docs/sessions/YYYY-MM-DD-*.md` at session start; start at 001 if none exist
- Example: `docs/sessions/2026-03-07-001-oidc-fix.md`