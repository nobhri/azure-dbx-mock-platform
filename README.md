# azure-dbx-mock-platform

A **minimal, end-to-end data platform** on **Azure Databricks**, designed for **repeatable deploy/destroy cycles** using **Terraform** and **GitHub Actions** (OIDC-based, no secrets).
It includes **cost guardrails**, **Unity Catalog governance**, and a minimal **data pipeline foundation**.

---

## 🚀 What You Get

### **Azure resources**

* Resource Group for the data platform
* ADLS Gen2 with `landing`, `uc-root`, `bronze`, and `silver` containers
* Databricks Access Connector (Managed Identity)
* Databricks Workspace (Premium or Trial tier)
* Remote Terraform state backend (Storage Account + containers)

### **Governance**

* Unity Catalog enabled (Metastore created and attached)
* Catalog & Schemas (`mock.staging`, `mock.serving`)
* Minimal grants (`account users` with `USE_CATALOG`, `USE_SCHEMA`)
* Subscription Budget + Email Alerts

### **Data Pipeline**

* `ingestion.py` generates random mock data → writes to ADLS landing
* Delta Live Tables (DLT) pipeline: bronze → silver
* Lakeview dashboard for KPI & counts

### **CI/CD**

* GitHub Actions workflows for:

  * `bootstrap` → state backend setup
  * `guardrails` → budget + alerts
  * `workload-azure` → Azure layer
  * `workload-dbx` → Databricks layer
* OIDC auth (no client secret required)

---

## 🏗️ Architecture Overview

> Unity Catalog and Metastore live at the **Databricks Account** level.
> The **Workspace** is attached to the Metastore and operates under it.

```mermaid
flowchart LR
subgraph AZURE[Azure]
  RG[Resource Group]
  SA[ADLS Gen2]
  WS[Databricks Workspace]
  AC[Access Connector (Managed Identity)]
  TFSTATE[Storage Account for TF State]
end

subgraph DATABRICKS_ACCOUNT[Databricks Account]
  META[Metastore (Unity Catalog)]
  CAT[Catalog: mock]
  SCH1[Schema: staging]
  SCH2[Schema: serving]
end

RG --> SA
RG --> AC
RG --> WS
RG --> TFSTATE
WS -- "attached to" --> META
META --> CAT
CAT --> SCH1
CAT --> SCH2
```

---

## 📂 Repository Structure

```
infra/
  bootstrap/            # One-time: creates tfstate storage (local/ephemeral)
  guardrails/           # Azure Budget + Alerts (remote backend, persistent)
  workload-azure/       # Azure layer: RG, ADLS, Access Connector, Workspace
  workload-dbx/         # Databricks layer: UC Metastore, Catalog, Schemas, Grants
.github/workflows/
  bootstrap.yaml
  guardrails.yaml
  workload-azure.yaml
  workload-dbx.yaml
scripts/
  setup-oidc.sh         # OIDC App + RBAC bootstrap
  maintenance.md        # Manual state lock/lease commands
```

---

## ⚙️ Prerequisites

* Azure subscription
* GitHub repository (public or private; **no secrets in repo**)
* Azure CLI and permissions to create App Registrations
* The following GitHub **Repo Secrets**:

| Secret                  | Description                                |
| ----------------------- | ------------------------------------------ |
| `AZURE_TENANT_ID`       | Entra ID tenant ID                         |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID                      |
| `AZURE_CLIENT_ID`       | App registration client ID (created below) |
| `TFSTATE_SA_UNIQ`       |short unique suffix for state SA name.      |
| `DATABRICKS_ACCOUNT_ID` | Databricks Account ID (for UC setup)       |

---

## 🔐 One-time: Set up OIDC for GitHub Actions

Run the following **once** (in Azure Cloud Shell or local Azure CLI):

```bash
# ====== Variables (replace with your own values) ======
TENANT_ID="<your-tenant-id>"
SUB_ID="<your-subscription-id>"
APP_NAME="gha-oidc-terraform"
REPO="owner/repo"              # e.g., nobhri/azure-dbx-mock-platform
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

# (Optional) Allow the SP to create RBAC role assignments (needed for workload-azure)
# Get objectId of the SP (same as above)
# Grant "User Access Administrator" at RG or SA scope
RG="rg-mock-data"
SA="<your-storage-account>"
az role assignment create \
  --assignee-object-id "$SP_OBJ_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "User Access Administrator" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG"

# If you prefer narrower scope:
# SCOPE=$(az storage account show -n "$SA" -g "$RG" --query id -o tsv)
# az role assignment create --assignee-object-id "$SP_OBJ_ID" \
#   --assignee-principal-type ServicePrincipal \
#   --role "User Access Administrator" \
#   --scope "$SCOPE"

echo "APP_ID (client-id): $APP_ID"
echo "TENANT: $TENANT_ID  SUB: $SUB_ID"
```

Then add these to your GitHub **Repo Secrets**:

```
AZURE_TENANT_ID=$TENANT_ID
AZURE_SUBSCRIPTION_ID=$SUB_ID
AZURE_CLIENT_ID=$APP_ID
TFSTATE_SA_NAME=<your tfstate SA name>
DATABRICKS_ACCOUNT_ID=<your Databricks Account ID>
```

---

## 🛠️ Deployment Steps

### 1️⃣ Bootstrap (one-time)

* Run `bootstrap.yaml` (manual trigger)
* Creates tfstate RG + Storage Account + containers
* Uses **local/ephemeral state**

### 2️⃣ Guardrails

* Run `guardrails.yaml` (main branch)
* Deploys **Budget + Alert Rules** to subscription
* Backend: `guardrails-tfstate/guardrails.tfstate`
* Remains persistent (not destroyed)

### 3️⃣ Workload — Azure Layer

* Run `workload-azure.yaml`
* Deploys:

  * Resource Group, ADLS containers
  * Access Connector (Managed Identity)
  * Databricks Workspace
  * RBAC: Access Connector MI → Blob Data Contributor
* Backend: `workload-tfstate/azure.tfstate`

### 4️⃣ Workload — Databricks Layer

* Run `workload-dbx.yaml`
* Deploys:

  * Metastore (account scope)
  * Workspace assignment
  * Storage Credential (MI)
  * External Location (`abfss://uc-root@<sa>.dfs.core.windows.net/`)
  * Catalog, Schemas, Grants
* Backend: `workload-tfstate/dbx.tfstate`

### 5️⃣ Destroy (optional)

* Trigger each workflow manually with `destroy=true`
* Guardrails + tfstate backend remain intact

---

## 💸 Cost Guardrails (Recommended Defaults)

* **Subscription Budget**: JPY 2000/month (customizable)
* **Alert**: Email notification when >80% usage
* **Compute policies**:

  * Cluster: ≤2 workers, 10-min auto-terminate
  * SQL Warehouse: smallest tier, 5-min auto-stop

> Expected ongoing cost ≈ **a few hundred yen/month** (mostly storage + budget object).

---

## 🧩 Implementation Notes

* **Providers split**

  * `azurerm` → Azure resources
  * `databricks` (two aliases):

    * `account` → Metastore
    * `workspace` → Catalogs, Schemas, Grants
* **State separation**

  * Guardrails → `guardrails.tfstate`
  * Azure layer → `azure.tfstate`
  * Databricks layer → `dbx.tfstate`
  * Each key locks independently, allowing concurrent workflows
* **Common pitfalls**

  * 403 on role assignment → SP lacks **User Access Administrator**
  * Budget date must be >= current month’s start
  * ADLS name must be globally unique & lowercase

---

## 🧾 .gitignore Recommendations

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

## ✅ Definition of Done

* Clone → Bootstrap → Guardrails → Workload-Azure → Workload-DBX → UC attached
* Dashboard and DLT can be added later
* Destroy cleans ephemeral layers; guardrails stay
* Entire workflow runs via GitHub Actions (no local Terraform needed)

---

## 📜 License

MIT 

---

Would you like me to generate the corresponding `bootstrap.yaml` and `guardrails.yaml` workflows next, in the same format as your `workload-azure` and `workload-dbx` ones?
