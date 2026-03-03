# Getting Started

> For architecture design and decision records, see [README.md](./README.md).

---

## Prerequisites

- Azure subscription
- GitHub repository (public or private; **no secrets in repo**)
- Azure CLI and permissions to create App Registrations
- The following GitHub **Repo Secrets**:

| Secret | Description |
| --- | --- |
| `AZURE_TENANT_ID` | Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_CLIENT_ID` | App registration client ID (created below) |
| `TFSTATE_SA_UNIQ` | Short unique suffix for state Storage Account name |
| `DATABRICKS_ACCOUNT_ID` | Databricks Account ID (for Unity Catalog setup) |
| `METASTORE_ID` | UUID of the existing Unity Catalog metastore |

---

## Repository Structure

```
infra/
  bootstrap/            # One-time: creates tfstate Storage Account (local/ephemeral state)
  guardrails/           # Azure Budget + Alerts (remote backend, persistent)
  workload-azure/       # Azure layer: RG, ADLS, Access Connector, Workspace
  workload-dbx/         # Databricks layer: UC Metastore, Catalog, Schemas, Grants
.github/workflows/
  bootstrap.yaml
  guardrails.yaml
  workload-azure.yaml
  workload-dbx.yaml
```

**State separation:**

| State file | Scope | Lifecycle |
|---|---|---|
| `guardrails.tfstate` | Budget + Alerts | Persistent |
| `azure.tfstate` | Azure layer | Deploy/destroy cycle |
| `dbx.tfstate` | Databricks layer | Deploy/destroy cycle |

Each state file locks independently, allowing concurrent workflow runs.

---

## One-time: Set up OIDC for GitHub Actions

Run the following once (Azure Cloud Shell or local Azure CLI):

```bash
# ====== Variables (replace with your own values) ======
TENANT_ID="<your-tenant-id>"
SUB_ID="<your-subscription-id>"
APP_NAME="gha-oidc-terraform"
REPO="owner/repo"              # e.g., your-username/azure-dbx-mock-platform
BRANCH="refs/heads/main"
TFSTATE_SA_ID="/subscriptions/<sub>/resourceGroups/rg-tfstate/providers/Microsoft.Storage/storageAccounts/<storage-account-name>"

# ====== App registration & Service Principal ======
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
SP_OBJ_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)

# ====== Federated Credential (GitHub OIDC) ======
FC_JSON=$(printf '{"name":"github-%s-main","issuer":"https://token.actions.githubusercontent.com","subject":"repo:%s:ref:%s","audiences":["api://AzureADTokenExchange"]}' "$REPO" "$REPO" "$BRANCH")
az ad app federated-credential create --id "$APP_ID" --parameters "$FC_JSON"

# ====== RBAC assignments ======
# Contributor at subscription scope
az role assignment create \
  --assignee-object-id "$SP_OBJ_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Contributor" \
  --scope "/subscriptions/$SUB_ID"

# Storage Blob Data Contributor on the tfstate Storage Account
az role assignment create \
  --assignee-object-id "$SP_OBJ_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" \
  --scope "$TFSTATE_SA_ID"

# User Access Administrator (required for workload-azure to assign RBAC)
RG="rg-mock-data"
az role assignment create \
  --assignee-object-id "$SP_OBJ_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "User Access Administrator" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG"

echo "APP_ID (client-id): $APP_ID"
echo "TENANT: $TENANT_ID  SUB: $SUB_ID"
```

Then add these to your GitHub **Repo Secrets**:

```
AZURE_TENANT_ID=$TENANT_ID
AZURE_SUBSCRIPTION_ID=$SUB_ID
AZURE_CLIENT_ID=$APP_ID
TFSTATE_SA_UNIQ=<short unique suffix>
DATABRICKS_ACCOUNT_ID=<your Databricks Account ID>
METASTORE_ID=<your Unity Catalog metastore UUID>
```

---

## Deployment Steps

### 1. Bootstrap (one-time)

- Trigger `bootstrap.yaml` manually (workflow dispatch)
- Creates the Terraform state Resource Group, Storage Account, and containers
- Uses local/ephemeral state — not stored remotely

### 2. Guardrails

- Trigger `guardrails.yaml` on main branch
- Deploys Azure Budget + Alert Rules at subscription scope
- State: `guardrails-tfstate/guardrails.tfstate`
- **Not destroyed** in teardown — persists across deploy/destroy cycles

### 3. Workload — Azure Layer

- Trigger `workload-azure.yaml`
- Deploys: Resource Group, ADLS Gen2 containers, Access Connector (Managed Identity), Databricks Workspace, RBAC assignments
- State: `workload-tfstate/azure.tfstate`

### 4. Workload — Databricks Layer

- Trigger `workload-dbx.yaml`
- Deploys: Unity Catalog Metastore, Workspace assignment, Storage Credential, External Location, Catalog, Schemas, Grants
- State: `workload-tfstate/dbx.tfstate`

### 5. Destroy (optional)

> **Order is mandatory.** Destroying in the wrong order orphans Unity Catalog objects in the Metastore and breaks the next apply. See [Orphaned UC objects recovery](#orphaned-uc-objects-recovery) if this has already happened.

**Destroy order (reverse dependency):**

1. Trigger `workload-dbx.yaml` with `destroy=true` — removes UC Metastore, Storage Credential, External Location
2. Trigger `workload-azure.yaml` with `destroy=true` — removes Databricks Workspace, ADLS, Access Connector, Resource Group

Guardrails and the tfstate backend remain intact across destroy/recreate cycles.

**Recreate order:**

1. Trigger `workload-azure.yaml` (no destroy flag) — provisions Azure layer
2. Trigger `workload-dbx.yaml` (no destroy flag) — provisions Databricks layer
3. **Manual step — re-grant CREATE EXTERNAL LOCATION** (see below)

**Why a manual grant after recreate?**

After each full destroy/recreate cycle, the Service Principal must be re-granted `CREATE EXTERNAL LOCATION` on the Metastore. This cannot be automated because only the human metastore admin can execute the grant — the SP cannot self-grant UC privileges.

Run the following as a human user (metastore admin) in a Databricks notebook or SQL warehouse:

```sql
GRANT CREATE EXTERNAL LOCATION ON METASTORE TO '<SP_client_id>';
```

Replace `<SP_client_id>` with the value of the `AZURE_CLIENT_ID` GitHub Secret.

---

### Orphaned UC objects recovery

If `workload-azure` was destroyed before `workload-dbx` (wrong order), the Unity Catalog Metastore survives but its objects (`uc-mi-credential`, `uc-root-location`) are no longer tracked in Terraform state. The next `workload-dbx` apply will fail with:

```
Error: cannot create storage credential: Storage Credential 'uc-mi-credential' already exists
```

**Recovery steps:**

1. In **Databricks Account Console** → Unity Catalog → External Locations → delete `uc-root-location`
2. In **Databricks Account Console** → Unity Catalog → Storage Credentials → delete `uc-mi-credential`
3. Trigger `workload-dbx.yaml` (no destroy flag) — apply will now succeed
4. Re-grant `CREATE EXTERNAL LOCATION` as described above

---

## Cost Guardrails

- **Subscription Budget**: JPY 2,000/month (customizable)
- **Alert**: Email notification at >80% usage
- **Cluster policy**: ≤2 workers, 10-min auto-terminate
- **SQL Warehouse**: smallest tier, 5-min auto-stop

> Expected ongoing cost ≈ a few hundred yen/month (storage + budget object only, when compute is idle)

---

## Common Pitfalls

- `403` on role assignment → Service Principal lacks **User Access Administrator**
- Budget deployment fails → date must be >= current month's start
- ADLS name conflict → Storage Account names must be globally unique and lowercase
- **Storage Account names are hardcoded in two places — replace before deploying:**
  - Terraform state backend Storage Account
  - Unity Catalog root storage Storage Account
- `Storage Credential 'uc-mi-credential' already exists` on workload-dbx apply → UC objects orphaned from a previous destroy (wrong order) — follow [Orphaned UC objects recovery](#orphaned-uc-objects-recovery)
- `workload-dbx` apply fails after recreate with permission errors → re-grant `CREATE EXTERNAL LOCATION ON METASTORE` as metastore admin (see step 5 above)
- **Do not run `terraform` from the repo root** — always use `-chdir=infra/<module>` (or let CI do it). Running terraform at the root creates a local `terraform.tfstate` in the repo root that is out of sync with the remote backend. The file is excluded by `.gitignore` but indicates an accidental manual run outside the intended module directory.

---

## .gitignore Recommendations

```
*.tfvars
*.auto.tfvars
.terraform/
*.tfstate*
*.tfstate.backup
.env*
.ipynb_checkpoints/
.venv/
.bundle/
.databricks/
```

---

## Definition of Done

- Clone → Bootstrap → Guardrails → Workload-Azure → Workload-DBX → Unity Catalog attached
- Entire workflow runs via GitHub Actions — no local Terraform execution required
- Destroy cleans ephemeral layers; guardrails and state backend remain intact