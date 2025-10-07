# azure-dbx-mock-platform




A **minimal, end-to-end data platform** on **Azure Databricks**, built to be **deployed/destroyed repeatedly** via Terraform and **Databricks Asset Bundles**, with **cost guardrails** baked in.

---

## 🚀 What you get

- **Azure resources**
  - Databricks Workspace (minimal)
  - ADLS Gen2 (landing + UC root)
  - Databricks Access Connector (Managed Identity)
  - Remote Terraform state storage (Storage Account + containers)
- **Governance**
  - Unity Catalog enabled (Metastore created & attached)
  - Catalog & Schemas (e.g., `mock.staging`, `mock.serving`)
  - Minimal grants (`data_engineer`, `viewer`)
  - Subscription **Budget + Alerts**
- **Data pipeline**
  - `ingestion.py` generates mock data → **ADLS landing**
  - **Delta Live Tables (DLT)**: bronze → silver
  - SQL Warehouse (small, auto-stop)
  - **Lakeview** dashboard (KPI, category counts, time series)
- **CI/CD**
  - GitHub Actions for **bootstrap / guardrails / workload / bundles**
  - OIDC auth (no client secret required)

---

## 🏗️ High-Level Architecture

> Metastore/Catalogs live at the **Databricks Account (Unity Catalog)** layer.  
> The Workspace **attaches** to the Metastore; it does **not contain** it.

```mermaid
flowchart LR

subgraph AZURE[Azure]
  A[Resource Group]
  SA[ADLS Gen2]
  WS[Databricks Workspace]
  AC[Access Connector]
  TFSA[tfstate Storage Account]
end

subgraph ACCOUNT[Databricks Account]
  UC[Metastore]
  C1[Catalog: mock]
  S1[Schema: staging]
  S2[Schema: serving]
end

subgraph WORKSPACE[Databricks Workspace Runtime]
  J[Job: ingestion.py]
  P[DLT: bronze → silver]
  WH[SQL Warehouse]
  D[Lakeview Dashboard]
end

A --> WS
A --> SA
A --> AC
A --> TFSA

WS -- metastore assignment --> UC
UC --> C1
C1 --> S1
C1 --> S2

J -. "writes to" .-> SA
P -. "reads from" .-> SA
P --> S1
S1 --> S2
S2 --> WH
WH --> D
````

---

## 📂 Repository Structure

```
/infra
  /bootstrap        # One-time: tfstate Storage + Action Group (local/ephemeral state run via Actions)
  /guardrails       # Budgets, alerts, (optional) policies; remote state; never destroyed
  /workload         # Workspace, ADLS, Access Connector, UC (attach), catalogs, schemas, grants
/dlt                # DLT pipeline sources (bronze → silver)
/ingest             # ingestion.py (mock data → ADLS landing)
/bundles            # Databricks Asset Bundles (Jobs, Pipelines, Dashboards)
/sql                # optional SQL init (grants, etc.)
/.github/workflows
  bootstrap.yaml
  guardrails.yaml
  workload.yaml
  bundles.yaml
README.md
```

---

## ⚙️ Prerequisites

* **Azure** subscription
* **GitHub** repository (public is fine; no secrets committed)
* **OIDC app** in Entra ID for GitHub Actions (see below)
* GitHub **Repo Secrets**:

  * `AZURE_TENANT_ID`
  * `AZURE_SUBSCRIPTION_ID`
  * `AZURE_CLIENT_ID` (from the OIDC app)
  * `TFSTATE_SA_UNIQ` (short unique suffix for state SA name)

---

## 🔐 One-time: Set up OIDC for GitHub Actions

Run once (Azure Cloud Shell recommended):

```bash
# ====== Variables (replace with your own values) ======
TENANT_ID="<your-tenant-id>"
SUB_ID="<your-subscription-id>"
APP_NAME="gha-oidc-terraform"
REPO="owner/repo"              # e.g., nobu/mock-dbx
BRANCH="refs/heads/main"       # or use environment scoping
TFSTATE_SA_ID="/subscriptions/<sub>/resourceGroups/rg-tfstate/providers/Microsoft.Storage/storageAccounts/stXXXXtfstate"

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

echo "APP_ID (client-id): $APP_ID"
echo "TENANT: $TENANT_ID  SUB: $SUB_ID"

```

Add these values to GitHub Repo Secrets:
`AZURE_CLIENT_ID=$APP_ID`, `AZURE_TENANT_ID=$TENANT_ID`, `AZURE_SUBSCRIPTION_ID=$SUB_ID`, and your `TFSTATE_SA_UNIQ`.

---

## 🛠️ Deploy: Step-by-step

1. **Bootstrap** (one-time)

   * Trigger `bootstrap.yaml` (workflow_dispatch).
   * Creates tfstate storage (RG/SA/containers) and optional Action Group.
   * Uses **ephemeral local state** inside the runner.

2. **Guardrails**

   * Run `guardrails.yaml` (main or manual).
   * Deploys **Subscription Budget & Alerts** (and optional policies) via **remote azurerm backend**.
   * **Never destroyed**.

3. **Workload**

   * Run `workload.yaml` (PR → plan / main → apply / manual → destroy).
   * Creates Workspace, ADLS, Access Connector, **attaches UC Metastore**, creates Catalog/Schemas/Grants.
   * Also provisions minimal WH and placeholders for ingestion & DLT.

4. **Bundles**

   * Run `bundles.yaml` to deploy **Jobs (ingestion.py), DLT pipeline, Dashboard**.

5. **Validate**

   * Lakeview dashboard shows mock data flowing (counts/KPI/time series).
   * `viewer` group users can view without extra steps.

6. **Destroy (Workload only)**

   * Trigger `workload.yaml` with `destroy=true`.
   * Guardrails & tfstate storage remain.

---

## 💸 Cost Guardrails (recommended defaults)

* **Azure Budgets** at **subscription scope** (e.g., JPY monthly threshold; email alerts).
* **Cluster Policies**: max 2 workers, **10-min auto-termination**.
* **SQL Warehouse**: smallest size, **5-min auto-stop**.

> Ongoing cost should stay at **a few hundred JPY/month** (mainly storage + budget objects).

---

## ✅ Definition of Done (DoD)

* `clone → bootstrap → guardrails → workload → bundles → dashboard visible`
* Adding a user to `viewer` gives immediate dashboard access
* `workload destroy` cleans all ephemeral resources; guardrails stay intact
* Fully operated via **GitHub Actions + OIDC** (no local Terraform required)

---

## 🧩 Notes & Tips

* **Providers split**:

  * `azurerm` → Azure resources (Workspace, ADLS, Access Connector, tfstate SA)
  * `databricks` (two aliases) →

    * **account** scope: Metastore & assignment
    * **workspace** scope: Catalog, Schemas, Grants, Jobs, Pipelines
* **SCIM sync** (optional later): Entra ID → Databricks user/group provisioning for smoother UC grants.
* **.gitignore**: ignore `*.tfvars`, `.auto.tfvars`, `.env*`, `.ipynb_checkpoints/`, `.venv/`, `.databricks/`, `.bundle/`, `.terraform/`, `*.tfstate*`, `*.dbc`.

---

## 📜 License

MIT (or choose what fits your needs).

```

Want me to drop this into a canvas-ready file or tailor the names (catalog/schema/group names, budgets, region) to your exact defaults?
```
