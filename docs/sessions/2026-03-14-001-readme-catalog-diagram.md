# Session 2026-03-14-001 — readme-catalog-diagram

**Branch:** docs/2026-03-14-001-readme-catalog-diagram
**Issue:** N/A
**PR:** (fill in when created)
**Outcome:** completed

## Objective

Fix the Workspace & Catalog Structure diagram in README.md:
1. Move catalogs outside workspace subgraph boxes — catalogs are Unity Catalog / metastore-scoped, not workspace-scoped.
2. Remove the consumer catalog — per ADR-004 intent, the consumer workspace reads gold views directly from the prod catalog.

## What was done

- Updated the `flowchart LR` mermaid diagram under "Workspace & Catalog Structure (Target State)"
- Separated workspaces into a "Platform Workspaces" subgraph and catalogs into a "Unity Catalog — Metastore-scoped" subgraph
- Removed consumer catalog; consumer workspace now reads gold-layer views directly from the prod catalog
- Updated the ADR-004 summary text in README to be consistent with the new diagram

## Decisions

- Catalogs rendered in their own UC subgraph to accurately represent that they are metastore-scoped, not workspace-internal.
- Consumer workspace reads gold views directly from prod catalog — no intermediate consumer catalog.

## Artifacts

- `README.md` — diagram and ADR-004 summary updated
- `docs/sessions/2026-03-14-001-readme-catalog-diagram.md` — this file
