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

## Boundaries
- NEVER approve or merge pull requests
- NEVER run `gh pr review` or `gh pr merge`
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
- See README ADR sections for rationale
- Do not move Catalog/Schema management back to Terraform
- Prod execution: CI/CD only, no manual runs