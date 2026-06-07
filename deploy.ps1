#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Skillable deployment script for LAB520 — deploys via azd with Service Principal auth.

.DESCRIPTION
    This script is designed for Skillable's unattended lab provisioning. It:
    1. Logs in with a Service Principal (az + azd)
    2. Resolves the lab user's Object ID for RBAC assignments
    3. Copies the skillable-specific infra files over the main infra
    4. Runs azd up from the repo root
    5. Writes the .env file for the lab user

    The key difference from the standard deployment: role assignments use a
    configurable principalType parameter instead of hardcoded 'User', allowing
    the SP-driven deployment to correctly assign roles to the lab user.

.PARAMETER AppId
    Service Principal App ID. In Skillable: @lab.CloudSubscription.AppId

.PARAMETER AppSecret
    Service Principal secret. In Skillable: @lab.CloudSubscription.AppSecret

.PARAMETER TenantId
    Azure AD Tenant ID. In Skillable: @lab.CloudSubscription.TenantId

.PARAMETER SubscriptionId
    Azure Subscription ID. In Skillable: @lab.CloudSubscription.Id

.PARAMETER Region
    Azure region. In Skillable: @lab.CloudResourceGroup(ResourceGroup1).Location

.PARAMETER EnvironmentName
    azd environment name. In Skillable: "build@lab.LabInstance.Id"

.PARAMETER LabUsername
    Lab user's UPN for RBAC. In Skillable: @lab.CloudPortalCredential(User1).Username

.PARAMETER PrincipalType
    Type of principal for RBAC: 'User' (default) or 'ServicePrincipal'.
    Use 'User' when LabUsername points to a user account.
    Use 'ServicePrincipal' when assigning roles to the SP itself.

.PARAMETER RepoRoot
    Path to the cloned repo. Defaults to the parent of this script's directory.

.EXAMPLE
    # Skillable lifecycle action (PowerShell)
    .\deploy.ps1 `
        -AppId "@lab.CloudSubscription.AppId" `
        -AppSecret "@lab.CloudSubscription.AppSecret" `
        -TenantId "@lab.CloudSubscription.TenantId" `
        -SubscriptionId "@lab.CloudSubscription.Id" `
        -Region "@lab.CloudResourceGroup(ResourceGroup1).Location" `
        -EnvironmentName "build@lab.LabInstance.Id" `
        -LabUsername "@lab.CloudPortalCredential(User1).Username"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AppId,

    [Parameter(Mandatory = $true)]
    [string]$AppSecret,

    [Parameter(Mandatory = $true)]
    [string]$TenantId,

    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,

    [Parameter(Mandatory = $true)]
    [string]$Region,

    [Parameter(Mandatory = $true)]
    [string]$EnvironmentName,

    [Parameter(Mandatory = $true)]
    [string]$LabUsername,

    [ValidateSet('User', 'ServicePrincipal')]
    [string]$PrincipalType = 'User',

    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Resolve repo root
# ---------------------------------------------------------------------------
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LAB520 — Skillable Deployment"
Write-Host "  Environment: $EnvironmentName"
Write-Host "  Region:      $Region"
Write-Host "  Principal:   $PrincipalType"
Write-Host "========================================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 1: Login with Service Principal
# ---------------------------------------------------------------------------
Write-Host "`n[1/6] Logging in with Service Principal..." -ForegroundColor Cyan

az login --service-principal -u $AppId -p $AppSecret -t $TenantId --skip-subscription-discovery | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: az login failed." -ForegroundColor Red
    exit 1
}
az account set --subscription $SubscriptionId
Write-Host "  az login: OK" -ForegroundColor Green

azd auth login --client-id $AppId --client-secret $AppSecret --tenant-id $TenantId
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: azd auth login failed." -ForegroundColor Red
    exit 1
}
Write-Host "  azd auth: OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Resolve lab user's Object ID
# ---------------------------------------------------------------------------
Write-Host "`n[2/6] Resolving lab user Object ID..." -ForegroundColor Cyan

$userId = az ad user show --id $LabUsername --query id --output tsv 2>$null
if (-not $userId) {
    Write-Host "  WARNING: Could not resolve user '$LabUsername'. RBAC will be skipped." -ForegroundColor Yellow
    $userId = ""
} else {
    Write-Host "  User: $LabUsername" -ForegroundColor Green
    Write-Host "  ObjectId: $userId" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Step 3: Copy skillable infra over main infra
# ---------------------------------------------------------------------------
Write-Host "`n[3/6] Installing skillable infrastructure templates..." -ForegroundColor Cyan

$skillableInfra = Join-Path $PSScriptRoot "infra"
$mainInfra = Join-Path $RepoRoot "infra"

# Back up originals
$backupDir = Join-Path $RepoRoot "infra_backup"
if (-not (Test-Path $backupDir)) {
    Copy-Item -Path $mainInfra -Destination $backupDir -Recurse
    Write-Host "  Original infra backed up to infra_backup/" -ForegroundColor Green
}

# Copy skillable files over main infra
Copy-Item -Path (Join-Path $skillableInfra "main.bicep") -Destination (Join-Path $mainInfra "main.bicep") -Force
Copy-Item -Path (Join-Path $skillableInfra "main.parameters.json") -Destination (Join-Path $mainInfra "main.parameters.json") -Force
Copy-Item -Path (Join-Path $skillableInfra "modules" "role-assignments.bicep") -Destination (Join-Path $mainInfra "modules" "role-assignments.bicep") -Force
Write-Host "  Skillable Bicep files installed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4: Configure azd environment
# ---------------------------------------------------------------------------
Write-Host "`n[4/6] Configuring azd environment..." -ForegroundColor Cyan

Push-Location $RepoRoot

azd env new $EnvironmentName --location $Region --subscription $SubscriptionId 2>$null
azd env set AZURE_PRINCIPAL_ID $userId -e $EnvironmentName
azd env set AZURE_PRINCIPAL_TYPE $PrincipalType -e $EnvironmentName
azd env set AZURE_LOCATION $Region -e $EnvironmentName

Write-Host "  AZURE_PRINCIPAL_ID:   $userId" -ForegroundColor Green
Write-Host "  AZURE_PRINCIPAL_TYPE: $PrincipalType" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 5: Run azd up
# ---------------------------------------------------------------------------
Write-Host "`n[5/6] Running azd up (this takes 3-5 minutes)..." -ForegroundColor Cyan

azd up -e $EnvironmentName --no-prompt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: azd up failed." -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "  azd up: OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 6: Write .env file
# ---------------------------------------------------------------------------
Write-Host "`n[6/6] Writing .env file..." -ForegroundColor Cyan

$projectEndpoint = azd env get-value AZURE_AI_PROJECT_ENDPOINT -e $EnvironmentName 2>$null
$modelName = azd env get-value MODEL_DEPLOYMENT_NAME -e $EnvironmentName 2>$null
$modelName2 = azd env get-value MODEL_DEPLOYMENT_NAME_2 -e $EnvironmentName 2>$null
$acrName = azd env get-value AZURE_CONTAINER_REGISTRY_NAME -e $EnvironmentName 2>$null

$envContent = @"
# Auto-generated by Skillable deployment script
PROJECT_ENDPOINT=$projectEndpoint
MODEL_DEPLOYMENT_NAME=$modelName
"@

if ($modelName2 -and $modelName2 -ne "") {
    $envContent += "`nMODEL_DEPLOYMENT_NAME_2=$modelName2"
}
if ($acrName -and $acrName -ne "") {
    $envContent += "`nAZURE_CONTAINER_REGISTRY_NAME=$acrName"
}

$envPath = Join-Path $RepoRoot ".env"
Set-Content -Path $envPath -Value $envContent -Encoding UTF8
Write-Host "  .env written to: $envPath" -ForegroundColor Green

Pop-Location

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Deployment complete!"
Write-Host "  PROJECT_ENDPOINT: $projectEndpoint"
Write-Host "  MODEL:            $modelName"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
