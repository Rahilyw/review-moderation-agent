# Skillable ARM Deployment Guide — LAB520

> **Session:** LAB520 — Get Started with Models in Microsoft Foundry: From First Inference to Deployed Agent  
> **Audience:** Skillable lab environment administrators  
> **Purpose:** Pre-provision Azure resources for each attendee using the ARM template before the session starts

This guide covers deploying Azure infrastructure using the **ARM template** (`azuredeploy.json`). For the Bicep-based deployment used by `azd`, see [Bicep Deployment](#bicep-deployment-alternative) at the bottom.

---

## What Gets Deployed

The ARM template creates all Azure resources in a single subscription-scoped deployment:

| Resource | Name Pattern | Purpose |
|----------|-------------|---------|
| Resource Group | `rg-{environmentName}` | Contains all lab resources |
| Log Analytics Workspace | `log-{token}` | Monitoring backend |
| Application Insights | `appi-{token}` | Agent telemetry (Lab 6) |
| Azure AI Services (Foundry) | `ai-{token}` | Model hosting account |
| Foundry Project | `{environmentName}-project` | Project with App Insights connection |
| Model Deployment | `gpt-4.1-mini` | Primary model (Labs 3–6) |
| Model Deployment (optional) | `gpt-4.1` | Second model (Lab 5 comparison) |
| Azure Container Registry | `ai{token}` | Agent container images (Lab 6) |
| Capability Host | `agents` | Hosted agent compute (Lab 6) |
| RBAC Role Assignments | — | OpenAI User, Contributor, AcrPush for attendee; CogServices User + AcrPull for project identity |

---

## Prerequisites

Before running the deployment:

- [ ] Azure CLI v2.67.0+ installed (`az version`)
- [ ] Logged in to Azure (`az login`)
- [ ] Subscription selected (`az account set --subscription "<id>"`)
- [ ] Resource providers registered (see [Register Providers](#step-1-register-resource-providers))
- [ ] Attendee's Azure AD Object ID available (for RBAC)

---

## ARM Template Deployment

### Step 1: Register Resource Providers

These must be registered on the target subscription before the first deployment:

```bash
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
az provider register --namespace Microsoft.ContainerRegistry
```

Verify all four show `Registered`:

```bash
az provider show --namespace Microsoft.CognitiveServices --query registrationState -o tsv
az provider show --namespace Microsoft.OperationalInsights --query registrationState -o tsv
az provider show --namespace Microsoft.Insights --query registrationState -o tsv
az provider show --namespace Microsoft.ContainerRegistry --query registrationState -o tsv
```

### Step 2: Get the Attendee's Object ID

Each attendee needs RBAC role assignments. Get their Azure AD Object ID:

```bash
# For the currently signed-in user
az ad signed-in-user show --query id -o tsv

# For a specific user by email
az ad user show --id "attendee@example.com" --query id -o tsv
```

### Step 3: Validate the Template (Dry Run)

Always validate before deploying:

```bash
az deployment sub validate \
  --location northcentralus \
  --template-file infra/azuredeploy.json \
  --parameters infra/azuredeploy.parameters.json \
  --parameters principalId="<attendee-object-id>"
```

Expected output: `"provisioningState": "Succeeded"`

### Step 4: Deploy

```bash
az deployment sub create \
  --name lab520-deployment \
  --location northcentralus \
  --template-file infra/azuredeploy.json \
  --parameters infra/azuredeploy.parameters.json \
  --parameters principalId="<attendee-object-id>"
```

Deployment takes approximately 3–5 minutes.

### Step 5: Retrieve Outputs

After deployment, capture the values the attendee needs for their `.env` file:

```bash
az deployment sub show \
  --name lab520-deployment \
  --query properties.outputs \
  -o json
```

Key outputs:

| Output | Maps to `.env` Variable |
|--------|------------------------|
| `AZURE_AI_PROJECT_ENDPOINT` | `PROJECT_ENDPOINT` |
| `MODEL_DEPLOYMENT_NAME` | `MODEL_DEPLOYMENT_NAME` |
| `AZURE_CONTAINER_REGISTRY_NAME` | `AZURE_CONTAINER_REGISTRY_NAME` |

### Step 6: Write the Attendee's `.env` File

On the Skillable VM, create `C:\Labs\Build26-LAB520\.env` with the deployment outputs:

```powershell
$outputs = az deployment sub show --name lab520-deployment --query properties.outputs -o json | ConvertFrom-Json

@"
PROJECT_ENDPOINT=$($outputs.AZURE_AI_PROJECT_ENDPOINT.value)
MODEL_DEPLOYMENT_NAME=$($outputs.MODEL_DEPLOYMENT_NAME.value)
AZURE_CONTAINER_REGISTRY_NAME=$($outputs.AZURE_CONTAINER_REGISTRY_NAME.value)
"@ | Set-Content -Path "C:\Labs\Build26-LAB520\.env"
```

---

## Template Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `environmentName` | string | `foundry-lab` | Used for resource group name and resource naming |
| `location` | string | `northcentralus` | Azure region for all resources |
| `principalId` | string | *(empty)* | Attendee's Azure AD Object ID for RBAC |
| `modelName` | string | `gpt-4.1-mini` | Primary model to deploy |
| `modelVersion` | string | `2025-04-14` | Primary model version |
| `modelFormat` | string | `OpenAI` | Model format |
| `modelSkuName` | string | `GlobalStandard` | SKU for model deployments |
| `modelCapacity` | int | `10` | Tokens-per-minute (thousands) for primary model |
| `deploySecondModel` | bool | `false` | Deploy `gpt-4.1` for Lab 5 comparison |
| `secondModelName` | string | `gpt-4.1` | Second model name |
| `secondModelVersion` | string | `2025-04-14` | Second model version |
| `secondModelCapacity` | int | `10` | Capacity for second model |
| `enableHostedAgents` | bool | `true` | Deploy ACR + capability host for Lab 6 |

### Override Parameters Inline

Deploy with a second model and custom environment name:

```bash
az deployment sub create \
  --name lab520-attendee42 \
  --location northcentralus \
  --template-file infra/azuredeploy.json \
  --parameters infra/azuredeploy.parameters.json \
  --parameters environmentName="lab520-attendee42" \
               principalId="<object-id>" \
               deploySecondModel=true
```

---

## Batch Deployment (Multiple Attendees)

For provisioning multiple attendee environments, loop over a list of Object IDs:

```powershell
$attendees = @(
    @{ Name = "attendee01"; ObjectId = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
    @{ Name = "attendee02"; ObjectId = "ffffffff-1111-2222-3333-444444444444" }
)

foreach ($attendee in $attendees) {
    $envName = "lab520-$($attendee.Name)"
    Write-Host "Deploying $envName..."

    az deployment sub create `
        --name $envName `
        --location northcentralus `
        --template-file infra/azuredeploy.json `
        --parameters infra/azuredeploy.parameters.json `
        --parameters environmentName=$envName `
                     principalId=$($attendee.ObjectId) `
        --no-wait
}

Write-Host "All deployments submitted. Check status with:"
Write-Host "  az deployment sub list --query ""[?contains(name,'lab520')].{Name:name,State:properties.provisioningState}"" -o table"
```

---

## Cleanup

Remove an attendee's resources after the session:

```bash
az group delete --name rg-foundry-lab --yes --no-wait
```

Or for a custom environment name:

```bash
az group delete --name rg-lab520-attendee01 --yes --no-wait
```

Purge soft-deleted AI Services (required to reuse the same name):

```bash
az cognitiveservices account purge \
  --name <ai-services-name> \
  --resource-group <rg-name> \
  --location northcentralus
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `QuotaExceeded` on model deployment | Insufficient TPM quota in region | Request quota increase or reduce `modelCapacity` |
| `RoleAssignmentExists` | Re-deploying with same principal | Safe to ignore — role assignment is idempotent |
| `ResourceProviderNotRegistered` | Provider not registered on subscription | Run `az provider register --namespace <provider>` |
| `InvalidTemplate` on capability host | API version not available in region | Ensure `northcentralus` is used; capability host is region-limited |
| Deployment timeout | Large-scale concurrent deployments | Retry failed deployments; reduce parallelism |

---

## Bicep Deployment Alternative

The lab also includes a Bicep-based deployment designed for use with the Azure Developer CLI (`azd`). This is the path attendees follow if they run `setup.ps1` themselves.

### Files

| File | Purpose |
|------|---------|
| `infra/main.bicep` | Main Bicep template (subscription-scoped) |
| `infra/main.parameters.json` | Parameters file (uses `azd` environment variables) |
| `infra/modules/ai-services.bicep` | AI Services, project, model deployments, ACR, capability host |
| `infra/modules/monitoring.bicep` | Log Analytics + Application Insights |
| `infra/modules/role-assignments.bicep` | RBAC role assignments for the attendee |

### Deploy with azd

```bash
cd C:\Labs\Build26-LAB520
azd init
azd env set AZURE_LOCATION northcentralus
azd provision
```

### Deploy with Azure CLI (Bicep directly)

```bash
az deployment sub create \
  --name lab520-bicep \
  --location northcentralus \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json \
  --parameters environmentName="foundry-lab" \
               location="northcentralus" \
               principalId="<attendee-object-id>"
```

### When to Use Which

| Scenario | Use |
|----------|-----|
| Skillable VM pre-provisioning (admin deploys for attendees) | **ARM template** (`azuredeploy.json`) — standalone, no tooling dependencies |
| Attendee self-service setup during the lab | **Bicep + azd** (`setup.ps1` → `azd provision`) — integrated with `.env` auto-population |
| CI/CD pipeline deployment | **ARM template** — portable JSON, no Bicep CLI needed |
| Iterating on infrastructure changes | **Bicep** — modular, easier to read and maintain |
