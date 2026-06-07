#!/usr/bin/env pwsh
<#
.SYNOPSIS
    One-command lab setup for "Get Started with Models in Microsoft Foundry".

.DESCRIPTION
    Validates prerequisites, provisions Azure resources via azd, configures
    the local .env file, and installs Python dependencies.

.PARAMETER Location
    Azure region for deployment. Default: northcentralus.

.PARAMETER EnvironmentName
    azd environment name (used as resource group suffix). Default: foundry-lab.

.PARAMETER DeploySecondModel
    If set, deploys a second model (gpt-4.1) for the comparison lab.

.PARAMETER SkipProvision
    Skip Azure provisioning (use when resources already exist).

.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -Location swedencentral -DeploySecondModel
    .\setup.ps1 -SkipProvision
#>
param(
    [string]$Location = "northcentralus",
    [string]$EnvironmentName = "foundry-lab",
    [switch]$DeploySecondModel,
    [switch]$SkipProvision
)

$ErrorActionPreference = "Stop"

function Write-Step($step, $msg) {
    Write-Host "`n[$step] $msg" -ForegroundColor Cyan
}

function Install-IfMissing($cmd, $displayName, $installCmd, $installUrl) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "  '$cmd' not found. Installing $displayName..." -ForegroundColor Yellow
        try {
            Invoke-Expression $installCmd
            # Refresh PATH so the newly installed tool is discoverable
            $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
            if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
                Write-Host "  WARNING: '$cmd' installed but not found in PATH. You may need to restart your terminal." -ForegroundColor Yellow
                Write-Host "  Manual install: $installUrl" -ForegroundColor Yellow
            } else {
                Write-Host "  $displayName installed successfully." -ForegroundColor Green
            }
        } catch {
            Write-Host "  ERROR: Failed to install $displayName. Install manually: $installUrl" -ForegroundColor Red
            exit 1
        }
    }
}

# -----------------------------------------------------------------------
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Get Started with Models in Microsoft Foundry"
Write-Host "  Lab Setup Script"
Write-Host "========================================================" -ForegroundColor Cyan

# -----------------------------------------------------------------------
Write-Step "1/10" "Checking and installing prerequisites..."

Install-IfMissing "git"    "Git"                 "winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements"              "https://git-scm.com/downloads"
Install-IfMissing "az"     "Azure CLI"           "winget install -e --id Microsoft.AzureCLI --accept-source-agreements --accept-package-agreements"   "https://aka.ms/installazurecli"
Install-IfMissing "azd"    "Azure Developer CLI" "winget install -e --id Microsoft.Azd --accept-source-agreements --accept-package-agreements"        "https://aka.ms/azure-dev/install"
Install-IfMissing "python" "Python"              "winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements"   "https://www.python.org/downloads/"

# Docker is optional (Lab 6 Option B) — inform but don't fail
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "  Docker not found (optional — only needed for Lab 6 local build)." -ForegroundColor Yellow
    Write-Host "  Lab 6 can use ACR Tasks (cloud build) instead. Install Docker: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
}

$gitVersion = (git --version 2>$null)
$azVersion  = (az version 2>$null | ConvertFrom-Json).'azure-cli'
$azdVersion = (azd version 2>$null).Trim()
$pyVersion  = (python --version 2>&1).Replace("Python ", "")

Write-Host "  Git:        $gitVersion"
Write-Host "  Azure CLI:  $azVersion"
Write-Host "  azd:        $azdVersion"
Write-Host "  Python:     $pyVersion"

# -----------------------------------------------------------------------
Write-Step "2/10" "Installing Visual Studio Code extensions..."

if (Get-Command "code" -ErrorAction SilentlyContinue) {
    $extensions = @(
        "ms-windows-ai-studio.windows-ai-studio",
        "ms-python.python",
        "ms-python.vscode-pylance"
    )
    foreach ($ext in $extensions) {
        $installed = code --list-extensions 2>$null | Where-Object { $_ -eq $ext }
        if ($installed) {
            Write-Host "  Already installed: $ext"
        } else {
            Write-Host "  Installing: $ext..." -ForegroundColor Yellow
            code --install-extension $ext --force 2>$null
        }
    }
} else {
    Write-Host "  Visual Studio Code CLI not found — skipping extension install." -ForegroundColor Yellow
    Write-Host "  Recommended: Install Visual Studio Code from https://code.visualstudio.com/" -ForegroundColor Yellow
}

# -----------------------------------------------------------------------
Write-Step "3/10" "Verifying Azure login..."

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "  Not logged in. Running az login..." -ForegroundColor Yellow
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Host "  Subscription: $($account.name) ($($account.id))"

# Check azd auth
$azdStatus = azd auth login --check-status 2>&1
if ($azdStatus -match "Not logged in") {
    Write-Host "  azd not logged in. Running azd auth login..." -ForegroundColor Yellow
    azd auth login
}
Write-Host "  azd auth: OK"

# -----------------------------------------------------------------------
Write-Step "4/10" "Registering Azure resource providers..."

$providers = @(
    "Microsoft.CognitiveServices",
    "Microsoft.OperationalInsights",
    "Microsoft.Insights",
    "Microsoft.ContainerRegistry",
    "Microsoft.Resources"
)
foreach ($provider in $providers) {
    $state = az provider show --namespace $provider --query registrationState -o tsv 2>$null
    if ($state -eq "Registered") {
        Write-Host "  $provider — already registered"
    } else {
        Write-Host "  $provider — registering..." -ForegroundColor Yellow
        az provider register --namespace $provider --wait 2>$null
        Write-Host "  $provider — registered" -ForegroundColor Green
    }
}

# -----------------------------------------------------------------------
Write-Step "5/10" "Getting principal ID for RBAC..."

$principalId = az ad signed-in-user show --query id -o tsv 2>$null
if ($principalId) {
    Write-Host "  Principal ID: $principalId"
} else {
    Write-Host "  WARNING: Could not retrieve principal ID. RBAC roles will not be assigned." -ForegroundColor Yellow
    $principalId = ""
}

# -----------------------------------------------------------------------
if (-not $SkipProvision) {
    Write-Step "6/10" "Initializing azd environment..."

    azd init --no-prompt -e $EnvironmentName 2>$null
    azd env set AZURE_LOCATION $Location
    if ($principalId) {
        azd env set AZURE_PRINCIPAL_ID $principalId
    }
    if ($DeploySecondModel) {
        azd env set DEPLOY_SECOND_MODEL "true"
    }

    Write-Host "  Environment:  $EnvironmentName"
    Write-Host "  Location:     $Location"
    Write-Host "  Second model: $($DeploySecondModel.IsPresent)"

    # -------------------------------------------------------------------
    Write-Step "7/10" "Provisioning Azure resources (this takes 5-10 minutes)..."

    azd provision --no-prompt

    Write-Host "  Provisioning complete." -ForegroundColor Green
} else {
    Write-Step "6/10" "Skipping azd init (--SkipProvision)"
    Write-Step "7/10" "Skipping azd provision (--SkipProvision)"
}

# -----------------------------------------------------------------------
Write-Step "8/10" "Creating Python virtual environment..."

$venvPath = Join-Path $PSScriptRoot ".." ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "  Virtual environment created at: .venv" -ForegroundColor Green
} else {
    Write-Host "  Virtual environment already exists at: .venv"
}

# Activate the virtual environment
$activateScript = Join-Path $venvPath "Scripts" "Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "  Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "  WARNING: Could not activate virtual environment." -ForegroundColor Yellow
}

# -----------------------------------------------------------------------
Write-Step "9/10" "Installing Python dependencies..."

$reqPath = Join-Path $PSScriptRoot ".." "requirements.txt"
if (Test-Path $reqPath) {
    pip install -r $reqPath --quiet
    Write-Host "  Dependencies installed."
} else {
    Write-Host "  WARNING: requirements.txt not found at $reqPath" -ForegroundColor Yellow
}

# -----------------------------------------------------------------------
Write-Step "10/10" "Writing .env configuration..."

# The postprovision hook already writes .env, but if SkipProvision was used
# we need to check.
$envPath = Join-Path $PSScriptRoot ".." ".env"
if (-not (Test-Path $envPath) -or $SkipProvision) {
    $endpoint = $null
    $model    = $null
    $model2   = $null
    if (-not $SkipProvision) {
        $endpoint = azd env get-value AZURE_AI_PROJECT_ENDPOINT 2>$null
        $model    = azd env get-value MODEL_DEPLOYMENT_NAME 2>$null
        $model2   = azd env get-value MODEL_DEPLOYMENT_NAME_2 2>$null
    }

    if (-not $endpoint) {
        Write-Host "  WARNING: PROJECT_ENDPOINT not resolved. Edit .env manually." -ForegroundColor Yellow
        $endpoint = "https://<your-resource>.services.ai.azure.com/api/projects/<your-project>"
    }
    if (-not $model) { $model = "gpt-4.1-mini" }

    $content = @"
# Auto-generated by setup.ps1
PROJECT_ENDPOINT=$endpoint
MODEL_DEPLOYMENT_NAME=$model
"@
    if ($model2 -and $model2 -ne "") {
        $content += "`nMODEL_DEPLOYMENT_NAME_2=$model2"
    }
    Set-Content -Path $envPath -Value $content -Encoding UTF8
}

Write-Host "  .env written." -ForegroundColor Green

# -----------------------------------------------------------------------
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Setup complete!"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. python src/01_first_inference.py   (Lab 3)"
Write-Host "    2. python src/02_comment_moderation.py (Lab 4)"
Write-Host "    3. python src/03_model_comparison.py   (Lab 5)"
Write-Host ""
Write-Host "  Cleanup when done:"
Write-Host "    azd down --force --purge"
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
