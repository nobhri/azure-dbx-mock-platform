# Session 2026-03-06-004 — Issue #64: Restore import block (correct UUID now in secret)

## What Happened

PR #72 (session 002) removed the import block, believing the metastore was
truly destroyed. This was incorrect.

## Root Cause Correction

The metastore `4f069ca3-af7f-4149-b0d0-525906a66fee` (name: `metastore_azure_japaneast`)
**survived** because every previous `workload-dbx` destroy run was failing at the
import block (METASTORE_ID secret contained extra content, not a plain UUID).
Terraform never reached the actual destroy step — the metastore was intact in the
Databricks account the whole time.

After PR #72 removed the import block, Terraform tried to **create** a new metastore
→ hit the 1-per-region limit:

```
Error: cannot create metastore: This account with id *** has reached the limit
for metastores in region japaneast.
```

## Fix (this PR)

Restored the import block with an updated comment that correctly explains the
design: the metastore is account-scoped and persists across workspace destroy/
recreate cycles. The METASTORE_ID secret is now set to the correct bare UUID
(`4f069ca3-af7f-4149-b0d0-525906a66fee`), so the import will succeed.

## Correct Mental Model

| Scenario | Import block behaviour |
|----------|-----------------------|
| Metastore in state AND in account | No-op (skipped by Terraform) |
| Metastore NOT in state, IS in account | Imports into state ✅ (designed for this) |
| Metastore NOT in state, NOT in account | Fails ❌ (must remove block and create fresh) |

In this project the metastore is never truly absent from the account unless:
- A successful `terraform destroy` ran with `force_destroy = true`
- The metastore was deleted manually from the Databricks Account Console

## Post-Merge

No additional human action required beyond what is already set:
- `METASTORE_ID` secret = `4f069ca3-af7f-4149-b0d0-525906a66fee` ✅
- After apply succeeds, run post-destroy grants (see runbook)
