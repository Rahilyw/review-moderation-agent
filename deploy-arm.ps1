#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Skillable ARM-only deployment — no azd dependency. Uses az deployment sub create directly.

.DESCRIPTION
    Alternative deployment script that uses the ARM template directly.
    Does not require azd to be installed. Useful for CI/CD pipelines
    or environments where only Azure CLI is available.

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
    Environment name for resource naming. In Skillable: "build@lab.LabInstance.Id"

.PARAMETER LabUsername
    Lab user's UPN for RBAC. In Skillable: @lab.CloudPortalCredential(User1).Username

.PARAMETER PrincipalType
    Type of principal for RBAC: 'User' (default) or 'ServicePrincipal'.

.PARAMETER DeploySecondModel
    Deploy a second model (gpt-4.1) for Lab 5. Default: false.

.PARAMETER EnableHostedAgents
    Deploy ACR + capability host for Lab 6. Default: true.

.EXAMPLE
    .\deploy-arm.ps1 `
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

    [bool]$DeploySecondModel = $false,

    [bool]$EnableHostedAgents = $true
)

$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$templateFile = Join-Path $scriptDir "infra" "azuredeploy.json"
$paramsFile = Join-Path $scriptDir "infra" "azuredeploy.parameters.json"
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LAB520 — Skillable ARM Deployment"
Write-Host "  Environment: $EnvironmentName"
Write-Host "  Region:      $Region"
Write-Host "  Template:    ARM (no azd required)"
Write-Host "========================================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 1: Login
# ---------------------------------------------------------------------------
Write-Host "`n[1/5] Logging in with Service Principal..." -ForegroundColor Cyan

az login --service-principal -u $AppId -p $AppSecret -t $TenantId --skip-subscription-discovery | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: az login failed." -ForegroundColor Red
    exit 1
}
az account set --subscription $SubscriptionId
Write-Host "  OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Resolve lab user
# ---------------------------------------------------------------------------
Write-Host "`n[2/5] Resolving lab user Object ID..." -ForegroundColor Cyan

$userId = az ad user show --id $LabUsername --query id --output tsv 2>$null
if (-not $userId) {
    Write-Host "  WARNING: Could not resolve user '$LabUsername'. RBAC will be skipped." -ForegroundColor Yellow
    $userId = ""
} else {
    Write-Host "  User: $LabUsername -> $userId" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Step 3: Validate template
# ---------------------------------------------------------------------------
Write-Host "`n[3/5] Validating ARM template..." -ForegroundColor Cyan

az deployment sub validate `
    --location $Region `
    --template-file $templateFile `
    --parameters $paramsFile `
    --parameters environmentName=$EnvironmentName `
                 location=$Region `
                 principalId=$userId `
                 principalType=$PrincipalType `
                 deploySecondModel=$DeploySecondModel `
                 enableHostedAgents=$EnableHostedAgents `
    | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Template validation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Validation: OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4: Deploy
# ---------------------------------------------------------------------------
Write-Host "`n[4/5] Deploying (3-5 minutes)..." -ForegroundColor Cyan

$deploymentName = "lab520-$EnvironmentName"

az deployment sub create `
    --name $deploymentName `
    --location $Region `
    --template-file $templateFile `
    --parameters $paramsFile `
    --parameters environmentName=$EnvironmentName `
                 location=$Region `
                 principalId=$userId `
                 principalType=$PrincipalType `
                 deploySecondModel=$DeploySecondModel `
                 enableHostedAgents=$EnableHostedAgents

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Deployment: OK" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 5: Write .env
# ---------------------------------------------------------------------------
Write-Host "`n[5/5] Writing .env file..." -ForegroundColor Cyan

$outputs = az deployment sub show --name $deploymentName --query properties.outputs -o json | ConvertFrom-Json

$envContent = @"
# Auto-generated by Skillable ARM deployment
PROJECT_ENDPOINT=$($outputs.AZURE_AI_PROJECT_ENDPOINT.value)
MODEL_DEPLOYMENT_NAME=$($outputs.MODEL_DEPLOYMENT_NAME.value)
"@

if ($outputs.AZURE_CONTAINER_REGISTRY_NAME.value) {
    $envContent += "`nAZURE_CONTAINER_REGISTRY_NAME=$($outputs.AZURE_CONTAINER_REGISTRY_NAME.value)"
}

$envPath = Join-Path $repoRoot ".env"
Set-Content -Path $envPath -Value $envContent -Encoding UTF8
Write-Host "  .env written to: $envPath" -ForegroundColor Green

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Deployment complete!"
Write-Host "  PROJECT_ENDPOINT: $($outputs.AZURE_AI_PROJECT_ENDPOINT.value)"
Write-Host "  MODEL:            $($outputs.MODEL_DEPLOYMENT_NAME.value)"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
