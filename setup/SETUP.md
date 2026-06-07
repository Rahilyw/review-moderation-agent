# Lab Setup

> **Duration:** ~10 minutes

Complete these steps before starting the lab modules.

> **Fast-track option:** Run `.\scripts\setup.ps1` (Windows) or `./scripts/setup.sh` (Linux/macOS) to automate **all** prerequisite installation, resource provider registration, Azure provisioning, and environment configuration in one command. Then skip to Lab 1.

---

## Key Terms

New to AI development? Here are the core terms used throughout this workshop:

| Term | Definition |
|------|------------|
| **Inference** | Sending a prompt to a model and getting a response back. |
| **Token** | The unit models use to measure text — roughly ¾ of a word. Pricing is per-token. |
| **System prompt** | Hidden instructions that tell the model how to behave (e.g., "classify comments as SAFE or UNSAFE"). |
| **Endpoint** | The URL your code connects to for accessing a deployed model or project. |
| **Model deployment** | A specific model (like `gpt-4.1-mini`) made available in your project, ready to receive inference requests. |
| **Credential / authentication** | How your code proves it has permission to use Azure resources — typically via `az login` or a managed identity. |
| **Hosted agent** | Your code packaged as a container and deployed to Foundry, accessible via a REST API without managing servers. |
| **RBAC** | Role-Based Access Control — Azure's system for granting specific permissions to users and services. |

---

## Step 1: Verify Git

```bash
git --version
```

Expected output: version 2.40 or later. If not installed:

| OS | Install Command |
|----|-----------------|
| Windows | `winget install -e --id Git.Git` |
| macOS | `brew install git` |
| Ubuntu/Debian | `sudo apt-get install git` |

---

## Step 2: Verify Azure CLI

```bash
az version
```

Expected output includes a version number (e.g., `2.67.0` or later). If not installed:

| OS | Install Command |
|----|-----------------|
| Windows | `winget install -e --id Microsoft.AzureCLI` |
| macOS | `brew install azure-cli` |
| Ubuntu/Debian | `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |

Or follow the [Azure CLI install guide](https://aka.ms/installazurecli).

---

## Step 3: Log in to Azure

```bash
az login
```

Complete the browser-based authentication flow. Then verify your subscription:

```bash
az account show --query "{Name:name, SubscriptionId:id, State:state}" -o table
```

If you have multiple subscriptions, select the one you want to use:

```bash
az account set --subscription "<your-subscription-id>"
```

---

## Step 4: Verify Role Permissions

Confirm you have sufficient permissions to create Foundry resources:

```bash
az role assignment list \
  --assignee "$(az ad signed-in-user show --query id -o tsv)" \
  --query "[?contains(roleDefinitionName, 'Owner') || contains(roleDefinitionName, 'Contributor') || contains(roleDefinitionName, 'Azure AI')].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

You need **Owner**, **Contributor**, or **Azure AI Owner** at the subscription or resource group level. If you do not have the required role, contact your Azure administrator before proceeding.

---

## Step 5: Register Azure Resource Providers

The lab requires several resource providers to be registered on your subscription:

```bash
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
az provider register --namespace Microsoft.ContainerRegistry
```

Check registration status:

```bash
az provider show --namespace Microsoft.CognitiveServices --query registrationState -o tsv
```

> All should return `Registered`. Registration may take a few minutes.

---

## Step 6: Verify Azure Developer CLI

```bash
azd version
```

If not installed:

| OS | Install Command |
|----|-----------------|
| Windows | `winget install -e --id Microsoft.Azd` |
| macOS/Linux | `curl -fsSL https://aka.ms/install-azd.sh \| bash` |

Or follow the [Azure Developer CLI install guide](https://aka.ms/azure-dev/install).

Log in to azd:

```bash
azd auth login --check-status
```

If not logged in:

```bash
azd auth login
```

---

## Step 7: Verify Python

```bash
python --version
```

Requires **Python 3.10 or later**. If not installed, download from [python.org](https://www.python.org/downloads/).

---

## Step 8: Create a Virtual Environment

Create and activate a Python virtual environment so lab dependencies are isolated from your system Python:

```bash
python -m venv .venv
```

Activate the environment:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

> **Tip:** You will need to activate the virtual environment each time you open a new terminal for this workshop. Visual Studio Code can do this automatically — when prompted to select a Python interpreter, choose the one inside `.venv`.

---

## Step 9: Install Python Dependencies

With the virtual environment active, install requirements:

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| `azure-ai-projects` | Foundry project client |

| `azure-identity` | Azure authentication (DefaultAzureCredential) |
| `openai` | OpenAI-compatible API client |
| `python-dotenv` | Environment variable management |

---

## Step 10: Install Visual Studio Code Extensions (Recommended)

If you are using Visual Studio Code, install the recommended extensions:

```bash
code --install-extension ms-windows-ai-studio.windows-ai-studio
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

| Extension | Purpose |
|-----------|---------|
| Foundry Toolkit | Foundry project integration |
| Python | Python language support |
| Pylance | IntelliSense for Python |

---

## Step 11: Docker (Optional — Lab 6 Only)

Docker is only needed if you want to build the agent container locally in Lab 6. Lab 6 also supports cloud builds via ACR Tasks (no Docker required).

```bash
docker --version
```

If you want to install it: [Get Docker](https://docs.docker.com/get-docker/).

---

## Step 12: Prepare Environment File

Copy the sample environment file and fill in your values (you will get these in Lab 2):

```bash
cp .env.sample .env
```

You will populate `.env` with your project endpoint and model deployment name during Lab 2.

---

## Verification Checklist

Before proceeding to Lab 1, confirm:

- [ ] `git --version` returns 2.40+
- [ ] `az version` returns 2.67.0+
- [ ] `az account show` shows an active subscription
- [ ] You have Owner/Contributor/Azure AI Owner role
- [ ] Resource providers registered (`Microsoft.CognitiveServices`, etc.)
- [ ] `azd version` returns 1.11.0+
- [ ] `azd auth login --check-status` shows logged in
- [ ] `python --version` shows 3.10+
- [ ] `.venv` directory exists and is activated (prompt shows `(.venv)`)
- [ ] `pip install -r requirements.txt` completed successfully
- [ ] Visual Studio Code extensions installed (recommended)
- [ ] `.env` file created from `.env.sample`

---

**Next:** [Lab 1 - Discover Models →](../docs/lab1-discover-models.md)
