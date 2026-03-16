---
name: pre-impl-check
description: Use before starting any implementation task to review relevant ADRs
---

## Pre-Implementation Check

Before writing any code or config, read the ADRs that govern the affected layer:

| Task type | ADRs to read |
|-----------|-------------|
| Infrastructure (Terraform, Azure networking) | ADR-001, ADR-002, ADR-003 |
| Catalog / Schema management | ADR-001, ADR-004, ADR-005 |
| ETL / PySpark transforms | ADR-006, ADR-007 |
| CI/CD workflow changes | the affected `.github/workflows/*.yaml` + any ADR it references |

**Output format** — before starting implementation, state:
- Which ADRs were read
- Whether the planned change is consistent with those decisions
- Any constraint or consequence from an ADR that shapes the implementation
- If the change conflicts with an existing ADR, stop and use `/adr-workflow` first
