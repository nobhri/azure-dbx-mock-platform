---
name: watch-ci
description: Use after PR merge to monitor main branch CI
disable-model-invocation: true
---

## Watch CI

Monitor the main branch CI run after a PR merges:

```mermaid
flowchart TD
    A[gh run list --branch main --limit 5] --> B{Run found?}
    B -- No --> A
    B -- Yes --> C[gh run view RUN_ID]
    C --> D{Status?}
    D -- in_progress --> C
    D -- success --> E[CI passed — notify user\nIssue can now be closed manually]
    D -- failure --> F[gh run view RUN_ID --log-failed]
    F --> G[Diagnose failure\nopen fix branch]
    G --> H[Commit fix → PR → merge]
    H --> A
```

**Rules:**
- Never trigger a re-run via `gh workflow run` or `gh api`
- Only observe; fixes go through a new PR
- Report the run URL and job summary to the user when done
