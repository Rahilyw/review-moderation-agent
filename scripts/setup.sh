#!/bin/bash
# ---------------------------------------------------------------------------
# One-command lab setup for "Get Started with Models in Microsoft Foundry"
#
# Usage:
#   ./setup.sh                              # Default: northcentralus, foundry-lab
#   ./setup.sh -l swedencentral             # Custom region
#   ./setup.sh -l northcentralus -s         # Deploy second model
#   ./setup.sh --skip-provision             # Skip Azure provisioning
# ---------------------------------------------------------------------------
set -e

LOCATION="northcentralus"
ENV_NAME="foundry-lab"
DEPLOY_SECOND=false
SKIP_PROVISION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--location)       LOCATION="$2"; shift 2;;
        -e|--env-name)       ENV_NAME="$2"; shift 2;;
        -s|--second-model)   DEPLOY_SECOND=true; shift;;
        --skip-provision)    SKIP_PROVISION=true; shift;;
        -h|--help)
            echo "Usage: $0 [-l location] [-e env-name] [-s] [--skip-provision]"
            echo "  -l, --location       Azure region (default: northcentralus)"
            echo "  -e, --env-name       azd environment name (default: foundry-lab)"
            echo "  -s, --second-model   Deploy second model for comparison lab"
            echo "  --skip-provision     Skip Azure provisioning"
            exit 0;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

step() { echo -e "\n\033[36m[$1] $2\033[0m"; }
ok()   { echo -e "\033[32m  $1\033[0m"; }
warn() { echo -e "\033[33m  WARNING: $1\033[0m"; }
fail() { echo -e "\033[31m  ERROR: $1\033[0m"; exit 1; }

echo ""
echo "========================================================"
echo "  Get Started with Models in Microsoft Foundry"
echo "  Lab Setup Script"
echo "========================================================"

# -----------------------------------------------------------------------
step "1/10" "Checking and installing prerequisites..."

# Install Git if missing
if ! command -v git >/dev/null 2>&1; then
    echo "  'git' not found. Installing Git..."
    sudo apt-get update -qq && sudo apt-get install -y -qq git 2>/dev/null || \
    brew install git 2>/dev/null || \
    fail "Could not auto-install Git. Install manually: https://git-scm.com/downloads"
    echo "  Git installed."
fi

# Install Azure CLI if missing
if ! command -v az >/dev/null 2>&1; then
    echo "  'az' not found. Installing Azure CLI..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash 2>/dev/null || \
    brew install azure-cli 2>/dev/null || \
    fail "Could not auto-install Azure CLI. Install manually: https://aka.ms/installazurecli"
    echo "  Azure CLI installed."
fi

# Install Azure Developer CLI if missing
if ! command -v azd >/dev/null 2>&1; then
    echo "  'azd' not found. Installing Azure Developer CLI..."
    curl -fsSL https://aka.ms/install-azd.sh | bash 2>/dev/null || \
    fail "Could not auto-install azd. Install manually: https://aka.ms/azure-dev/install"
    echo "  Azure Developer CLI installed."
fi

# Check Python
command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || fail "'python' not found. Install: https://www.python.org/downloads/"

# Docker is optional (Lab 6 Option B) — inform but don't fail
if ! command -v docker >/dev/null 2>&1; then
    warn "Docker not found (optional — only needed for Lab 6 local build)."
    echo "  Lab 6 can use ACR Tasks (cloud build) instead. Install Docker: https://docs.docker.com/get-docker/"
fi

PYTHON_CMD=$(command -v python3 || command -v python)
GIT_VER=$(git --version 2>/dev/null)
AZ_VER=$(az version 2>/dev/null | grep '"azure-cli"' | head -1 | sed 's/[^0-9.]//g')
AZD_VER=$(azd version 2>/dev/null | tr -d '[:space:]')
PY_VER=$($PYTHON_CMD --version 2>&1 | sed 's/Python //')

echo "  Git:       $GIT_VER"
echo "  Azure CLI: $AZ_VER"
echo "  azd:       $AZD_VER"
echo "  Python:    $PY_VER"

# -----------------------------------------------------------------------
step "2/10" "Installing Visual Studio Code extensions..."

if command -v code >/dev/null 2>&1; then
    EXTENSIONS=(
        "ms-windows-ai-studio.windows-ai-studio"
        "ms-python.python"
        "ms-python.vscode-pylance"
    )
    INSTALLED=$(code --list-extensions 2>/dev/null)
    for ext in "${EXTENSIONS[@]}"; do
        if echo "$INSTALLED" | grep -qi "^${ext}$"; then
            echo "  Already installed: $ext"
        else
            echo "  Installing: $ext..."
            code --install-extension "$ext" --force 2>/dev/null || warn "Failed to install $ext"
        fi
    done
else
    warn "Visual Studio Code CLI not found — skipping extension install."
    echo "  Recommended: Install Visual Studio Code from https://code.visualstudio.com/"
fi

# -----------------------------------------------------------------------
step "3/10" "Verifying Azure login..."

if ! az account show >/dev/null 2>&1; then
    warn "Not logged in. Running az login..."
    az login
fi
SUBSCRIPTION=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "  Subscription: $SUBSCRIPTION ($SUBSCRIPTION_ID)"

if azd auth login --check-status 2>&1 | grep -qi "not logged in"; then
    warn "azd not logged in. Running azd auth login..."
    azd auth login
fi
ok "azd auth: OK"

# -----------------------------------------------------------------------
step "4/10" "Registering Azure resource providers..."

PROVIDERS=(
    "Microsoft.CognitiveServices"
    "Microsoft.OperationalInsights"
    "Microsoft.Insights"
    "Microsoft.ContainerRegistry"
    "Microsoft.Resources"
)
for provider in "${PROVIDERS[@]}"; do
    STATE=$(az provider show --namespace "$provider" --query registrationState -o tsv 2>/dev/null)
    if [ "$STATE" = "Registered" ]; then
        echo "  $provider — already registered"
    else
        echo "  $provider — registering..."
        az provider register --namespace "$provider" --wait 2>/dev/null
        ok "$provider — registered"
    fi
done

# -----------------------------------------------------------------------
step "5/10" "Getting principal ID for RBAC..."

PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")
if [ -n "$PRINCIPAL_ID" ]; then
    echo "  Principal ID: $PRINCIPAL_ID"
else
    warn "Could not retrieve principal ID. RBAC roles will not be assigned."
fi

# -----------------------------------------------------------------------
if [ "$SKIP_PROVISION" = false ]; then
    step "6/10" "Initializing azd environment..."

    cd "$ROOT_DIR"
    azd init --no-prompt -e "$ENV_NAME" 2>/dev/null || true
    azd env set AZURE_LOCATION "$LOCATION"
    [ -n "$PRINCIPAL_ID" ] && azd env set AZURE_PRINCIPAL_ID "$PRINCIPAL_ID"
    [ "$DEPLOY_SECOND" = true ] && azd env set DEPLOY_SECOND_MODEL "true"

    echo "  Environment:  $ENV_NAME"
    echo "  Location:     $LOCATION"
    echo "  Second model: $DEPLOY_SECOND"

    # -------------------------------------------------------------------
    step "7/10" "Provisioning Azure resources (this takes 5-10 minutes)..."

    azd provision --no-prompt

    ok "Provisioning complete."
else
    step "6/10" "Skipping azd init (--skip-provision)"
    step "7/10" "Skipping azd provision (--skip-provision)"
fi

# -----------------------------------------------------------------------
step "8/10" "Creating Python virtual environment..."

VENV_PATH="$ROOT_DIR/.venv"
if [ ! -d "$VENV_PATH" ]; then
    $PYTHON_CMD -m venv "$VENV_PATH"
    ok "Virtual environment created at: .venv"
else
    echo "  Virtual environment already exists at: .venv"
fi

# Activate the virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    ok "Virtual environment activated."
else
    warn "Could not activate virtual environment."
fi

# -----------------------------------------------------------------------
step "9/10" "Installing Python dependencies..."

REQ_PATH="$ROOT_DIR/requirements.txt"
if [ -f "$REQ_PATH" ]; then
    pip install -r "$REQ_PATH" --quiet
    ok "Dependencies installed."
else
    warn "requirements.txt not found."
fi

# -----------------------------------------------------------------------
step "10/10" "Writing .env configuration..."

ENV_PATH="$ROOT_DIR/.env"
if [ ! -f "$ENV_PATH" ] || [ "$SKIP_PROVISION" = true ]; then
    ENDPOINT=$(azd env get-value AZURE_AI_PROJECT_ENDPOINT 2>/dev/null || echo "")
    MODEL=$(azd env get-value MODEL_DEPLOYMENT_NAME 2>/dev/null || echo "gpt-4.1-mini")
    MODEL2=$(azd env get-value MODEL_DEPLOYMENT_NAME_2 2>/dev/null || echo "")

    if [ -z "$ENDPOINT" ]; then
        warn "PROJECT_ENDPOINT not resolved. Edit .env manually."
        ENDPOINT="https://<your-resource>.services.ai.azure.com/api/projects/<your-project>"
    fi

    cat > "$ENV_PATH" <<EOF
# Auto-generated by setup.sh
PROJECT_ENDPOINT=$ENDPOINT
MODEL_DEPLOYMENT_NAME=$MODEL
EOF

    if [ -n "$MODEL2" ]; then
        echo "MODEL_DEPLOYMENT_NAME_2=$MODEL2" >> "$ENV_PATH"
    fi
fi

ok ".env written."

# -----------------------------------------------------------------------
echo ""
echo "========================================================"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. $PYTHON_CMD src/01_first_inference.py   (Lab 3)"
echo "    2. $PYTHON_CMD src/02_comment_moderation.py (Lab 4)"
echo "    3. $PYTHON_CMD src/03_model_comparison.py   (Lab 5)"
echo ""
echo "  Cleanup when done:"
echo "    azd down --force --purge"
echo "========================================================"
echo ""
