# Skillable Deployment Guide — LAB520

> **Session:** LAB520 — Get Started with Models in Microsoft Foundry  
> **Audience:** Skillable lab environment administrators  
> **Purpose:** Deploy LAB520 infrastructure unattended via Service Principal

---

## What Changed from the Standard Deployment

The standard `infra/` templates hardcode `principalType: 'User'` on all attendee RBAC role assignments. When Skillable runs `azd up` under a Service Principal, Azure ARM may fail to validate the principal type because the deploying identity (SP) cannot always resolve a `User` principal via Graph API.

The skillable templates add a **`principalType` parameter** (default: `User`) that is passed through to all attendee role assignments. Project managed identity roles remain hardcoded to `ServicePrincipal` since they are always managed identities.

### Files in this folder

| File | Purpose |
|------|---------|
| `deploy.ps1` | **azd-based** deployment script (copies skillable infra, runs `azd up`) |
| `deploy-arm.ps1` | **ARM-only** deployment script (no azd dependency, uses `az deployment sub create`) |
| `infra/main.bicep` | Modified Bicep — adds `principalType` parameter |
| `infra/main.parameters.json` | Modified parameters — includes `AZURE_PRINCIPAL_TYPE` env var |
| `infra/modules/role-assignments.bicep` | Modified — accepts `principalType` instead of hardcoded `'User'` |
| `infra/modules/ai-services.bicep` | Unchanged from main (included for standalone use) |
| `infra/modules/monitoring.bicep` | Unchanged from main (included for standalone use) |
| `infra/abbreviations.json` | Unchanged from main (included for standalone use) |
| `infra/azuredeploy.json` | Full ARM template with `principalType` support |
| `infra/azuredeploy.parameters.json` | ARM parameters with `principalType` |

---

## Deployment Options

### Option A: azd-based (recommended)

Uses `deploy.ps1` which copies the skillable Bicep files over the main `infra/` directory, then runs `azd up`. This preserves the post-provision hooks that write the `.env` file and install Python dependencies.

### Option B: ARM-only (no azd required)

Uses `deploy-arm.ps1` with the self-contained ARM template. No `azd` installation needed — only Azure CLI. The `.env` file is written from deployment outputs.

---

## Skillable Lifecycle Action Setup

### Option A: azd-based deployment

Add a **PowerShell** lifecycle action that runs on lab launch:

```powershell
#Variables
$appId = "@lab.CloudSubscription.AppId"
$appSecret = "@lab.CloudSubscription.AppSecret"
$tenantId = "@lab.CloudSubscription.TenantId"
$subId = "@lab.CloudSubscription.Id"
$region = "@lab.CloudResourceGroup(ResourceGroup1).Location"
$envName = "build@lab.LabInstance.Id"
$labUser = "@lab.CloudPortalCredential(User1).Username"

# Clone the repo
cd C:\Users\LabUser\AppData\Local\Temp
git clone https://github.com/microsoft/Build26-LAB520.git
cd Build26-LAB520

# Run the skillable deployment
.\skillable\deploy.ps1 `
    -AppId $appId `
    -AppSecret $appSecret `
    -TenantId $tenantId `
    -SubscriptionId $subId `
    -Region $region `
    -EnvironmentName $envName `
    -LabUsername $labUser `
    -PrincipalType "User"
```

### Option B: ARM-only deployment

```powershell
#Variables
$appId = "@lab.CloudSubscription.AppId"
$appSecret = "@lab.CloudSubscription.AppSecret"
$tenantId = "@lab.CloudSubscription.TenantId"
$subId = "@lab.CloudSubscription.Id"
$region = "@lab.CloudResourceGroup(ResourceGroup1).Location"
$envName = "build@lab.LabInstance.Id"
$labUser = "@lab.CloudPortalCredential(User1).Username"

# Clone the repo
cd C:\Users\LabUser\AppData\Local\Temp
git clone https://github.com/microsoft/Build26-LAB520.git
cd Build26-LAB520

# Run the ARM-only deployment
.\skillable\deploy-arm.ps1 `
    -AppId $appId `
    -AppSecret $appSecret `
    -TenantId $tenantId `
    -SubscriptionId $subId `
    -Region $region `
    -EnvironmentName $envName `
    -LabUsername $labUser `
    -PrincipalType "User"
```

### Inline Script (minimal, no deploy script)

If you prefer a self-contained lifecycle action without using the deploy scripts:

```powershell
$appId = "@lab.CloudSubscription.AppId"
$appSecret = "@lab.CloudSubscription.AppSecret"
$tenantId = "@lab.CloudSubscription.TenantId"
$subId = "@lab.CloudSubscription.Id"
$region = "@lab.CloudResourceGroup(ResourceGroup1).Location"
$envName = "build@lab.LabInstance.Id"

# Login
az login --service-principal -u $appId -p $appSecret -t $tenantId --skip-subscription-discovery
$userId = az ad user show --id "@lab.CloudPortalCredential(User1).Username" --query id --output tsv

# Clone and deploy
cd C:\Users\LabUser\AppData\Local\Temp
git clone https://github.com/microsoft/Build26-LAB520.git
cd Build26-LAB520

# Copy skillable infra over main infra
Copy-Item -Path skillable\infra\main.bicep -Destination infra\main.bicep -Force
Copy-Item -Path skillable\infra\main.parameters.json -Destination infra\main.parameters.json -Force
Copy-Item -Path skillable\infra\modules\role-assignments.bicep -Destination infra\modules\role-assignments.bicep -Force

# Run azd
azd auth login --client-id $appId --client-secret $appSecret --tenant-id $tenantId
azd env new $envName --location $region --subscription $subId
azd env set AZURE_PRINCIPAL_ID $userId
azd env set AZURE_PRINCIPAL_TYPE "User"
azd up -e $envName --no-prompt
```

---

## principalType Parameter

| Value | When to Use |
|-------|-------------|
| `User` | The `principalId` is a user's Object ID (from `az ad user show`). **This is the standard Skillable scenario** — the SP deploys but assigns roles to the lab user. |
| `ServicePrincipal` | The `principalId` is an SP or managed identity. Use when the SP itself needs the roles, or when no lab user exists. |

### How it flows through the templates

```
deploy.ps1 / deploy-arm.ps1
  └─> principalType parameter
        └─> main.bicep (param principalType)
              └─> role-assignments.bicep (param principalType)
                    └─> roleAssignment.properties.principalType = principalType
```

The project's managed identity roles (Cognitive Services User, AcrPull) are **always** `ServicePrincipal` — these are unaffected by the parameter.

---

## Role Assignments Summary

| Role | Assigned To | principalType | Condition |
|------|------------|---------------|-----------|
| Cognitive Services OpenAI User | Lab user / SP | Configurable | `principalId` is not empty |
| Cognitive Services Contributor | Lab user / SP | Configurable | `principalId` is not empty |
| AcrPush | Lab user / SP | Configurable | `enableHostedAgents` AND `principalId` not empty |
| Cognitive Services User | Project managed identity | `ServicePrincipal` (hardcoded) | `enableHostedAgents` |
| AcrPull | Project managed identity | `ServicePrincipal` (hardcoded) | `enableHostedAgents` |

---

## Prerequisites for Skillable VM

The Skillable VM image should have these tools pre-installed:

| Tool | Required For | Install Command |
|------|-------------|-----------------|
| Azure CLI | Both options | `winget install -e --id Microsoft.AzureCLI` |
| Azure Developer CLI | Option A only | `winget install -e --id Microsoft.Azd` |
| Git | Cloning repo | `winget install -e --id Git.Git` |
| Python 3.12+ | Lab exercises | `winget install -e --id Python.Python.3.12` |

---

## Cleanup

Remove lab resources after the session:

```powershell
# Using the environment name from deployment
az group delete --name "rg-build<LabInstanceId>" --yes --no-wait

# Purge soft-deleted AI Services (allows name reuse)
az cognitiveservices account purge `
    --name <ai-services-name> `
    --resource-group "rg-build<LabInstanceId>" `
    --location northcentralus
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `PrincipalNotFound` on role assignment | SP cannot resolve the user principal | Ensure `principalType` matches the actual principal. For lab users, use `User`. |
| `RoleAssignmentExists` | Re-deploying with same principal | Safe to ignore — idempotent. |
| `AuthorizationFailed` on deployment | SP lacks Owner/Contributor on subscription | Grant the SP `Owner` role on the subscription. |
| `az ad user show` returns empty | SP lacks Graph API permissions | Grant `User.Read.All` to the SP, or pre-populate `principalId` directly. |
| `azd auth login` fails | azd not installed | Use `deploy-arm.ps1` instead (ARM-only, no azd needed). |
| `QuotaExceeded` on model deployment | Insufficient TPM quota in region | Reduce `modelCapacity` or request quota increase. |
