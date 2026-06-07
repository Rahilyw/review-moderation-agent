# Skillable Deployment — LAB520

> **Session:** LAB520 — Get Started with Models in Microsoft Foundry: From First Inference to Deployed Agent  
> **Purpose:** Unattended Azure provisioning for Skillable lab environments using Service Principal authentication

---

## Why This Exists

The standard `infra/` templates hardcode `principalType: 'User'` on all RBAC role assignments. When Skillable runs deployments under a Service Principal, this can cause failures because the SP identity cannot always resolve a `User` principal via Graph API.

This folder contains modified infrastructure templates and deployment scripts that make `principalType` configurable, enabling SP-driven unattended deployments to correctly assign roles to the lab user.

---

## Folder Contents

```
skillable/
├── README.md                              # This file
├── SETUP.md                               # Detailed deployment guide & troubleshooting
├── deploy.ps1                             # azd-based deployment script (recommended)
├── deploy-arm.ps1                         # ARM-only deployment script (no azd needed)
└── infra/
    ├── abbreviations.json                 # Resource name prefixes
    ├── azuredeploy.json                   # ARM template with principalType support
    ├── azuredeploy.parameters.json        # ARM parameters
    ├── main.bicep                         # Bicep template with principalType parameter
    ├── main.parameters.json               # Bicep parameters (azd env var bindings)
    └── modules/
        ├── ai-services.bicep              # AI Services, project, models, ACR, capability host
        ├── monitoring.bicep               # Log Analytics + Application Insights
        └── role-assignments.bicep         # RBAC roles with configurable principalType
```

### Key Differences from Standard `infra/`

| File | Change |
|------|--------|
| `main.bicep` | Adds `principalType` parameter, passes it to role-assignments module |
| `main.parameters.json` | Binds `AZURE_PRINCIPAL_TYPE` env var |
| `modules/role-assignments.bicep` | Uses `principalType` param instead of hardcoded `'User'` |
| `azuredeploy.json` | Adds `principalType` parameter to ARM template and all attendee role assignments |
| `azuredeploy.parameters.json` | Adds `principalType` field |

---

## Quick Start

### Option A: azd-based (recommended)

Requires Azure CLI + Azure Developer CLI on the Skillable VM.

```powershell
$appId     = "@lab.CloudSubscription.AppId"
$appSecret = "@lab.CloudSubscription.AppSecret"
$tenantId  = "@lab.CloudSubscription.TenantId"
$subId     = "@lab.CloudSubscription.Id"
$region    = "@lab.CloudResourceGroup(ResourceGroup1).Location"
$envName   = "build@lab.LabInstance.Id"
$labUser   = "@lab.CloudPortalCredential(User1).Username"

cd C:\Users\LabUser\AppData\Local\Temp
git clone https://github.com/microsoft/Build26-LAB520.git
cd Build26-LAB520

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

### Option B: ARM-only (no azd required)

Requires only Azure CLI. Uses `az deployment sub create` directly.

```powershell
$appId     = "@lab.CloudSubscription.AppId"
$appSecret = "@lab.CloudSubscription.AppSecret"
$tenantId  = "@lab.CloudSubscription.TenantId"
$subId     = "@lab.CloudSubscription.Id"
$region    = "@lab.CloudResourceGroup(ResourceGroup1).Location"
$envName   = "build@lab.LabInstance.Id"
$labUser   = "@lab.CloudPortalCredential(User1).Username"

cd C:\Users\LabUser\AppData\Local\Temp
git clone https://github.com/microsoft/Build26-LAB520.git
cd Build26-LAB520

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

### Option C: Minimal inline script

If you prefer not to use the deploy scripts, add three lines to your existing lifecycle action before `azd up`:

```powershell
# After cloning the repo and before azd up:
Copy-Item -Path skillable\infra\main.bicep -Destination infra\main.bicep -Force
Copy-Item -Path skillable\infra\main.parameters.json -Destination infra\main.parameters.json -Force
Copy-Item -Path skillable\infra\modules\role-assignments.bicep -Destination infra\modules\role-assignments.bicep -Force

azd env set AZURE_PRINCIPAL_TYPE "User"
```

---

## Prerequisites

| Tool | Required By | Install |
|------|------------|---------|
| Azure CLI (2.67+) | Both options | `winget install -e --id Microsoft.AzureCLI` |
| Azure Developer CLI | Option A only | `winget install -e --id Microsoft.Azd` |
| Git | Cloning repo | `winget install -e --id Git.Git` |
| Python 3.12+ | Lab exercises | `winget install -e --id Python.Python.3.12` |

---

## principalType Values

| Value | Use When |
|-------|----------|
| `User` | `principalId` is a lab user's Object ID (standard Skillable scenario) |
| `ServicePrincipal` | `principalId` is an SP or managed identity |

---

## What Gets Deployed

| Resource | Purpose |
|----------|---------|
| Resource Group (`rg-{envName}`) | Contains all lab resources |
| Log Analytics + App Insights | Monitoring and agent telemetry |
| Azure AI Services (Foundry) | Model hosting account |
| Foundry Project | Project with App Insights connection |
| `gpt-4.1-mini` deployment | Primary model (Labs 3–6) |
| `gpt-4.1` deployment (optional) | Second model (Lab 5 comparison) |
| Azure Container Registry (optional) | Agent container images (Lab 6) |
| Capability Host (optional) | Hosted agent compute (Lab 6) |
| RBAC role assignments | OpenAI User, Contributor, AcrPush for attendee |

---

## Cleanup

```powershell
az group delete --name "rg-build<LabInstanceId>" --yes --no-wait
```

---

## Further Reading

See [SETUP.md](SETUP.md) for detailed deployment walkthroughs, Skillable lifecycle action examples, role assignment details, and troubleshooting.
