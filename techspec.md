# Skillable VM Image Tech Spec — LAB520

> **Session:** LAB520 — Get Started with Models in Microsoft Foundry: From First Inference to Deployed Agent  
> **Duration:** 75–90 minutes  
> **VM OS:** Windows 11 (recommended) or Windows Server 2022  

---

## Pre-installed Software Checklist

All software below must be installed and available on `PATH` before the attendee starts.

### Required

- [ ] **Git** — v2.40 or later  
  `winget install -e --id Git.Git`

- [ ] **Python** — v3.10 or later (3.13 recommended)  
  `winget install -e --id Python.Python.3.13`  
  Ensure `python` and `pip` are on PATH. Verify: `python --version`

- [ ] **Azure CLI** — v2.67.0 or later  
  `winget install -e --id Microsoft.AzureCLI`  
  Verify: `az version`

- [ ] **Azure Developer CLI (azd)** — v1.11.0 or later  
  `winget install -e --id Microsoft.Azd`  
  Verify: `azd version`

- [ ] **Visual Studio Code** — latest stable  
  `winget install -e --id Microsoft.VisualStudioCode`

- [ ] **A modern web browser** — Edge or Chrome (for Azure portal and Foundry playground)

### VS Code Extensions

Pre-install these so attendees don't wait for marketplace downloads:

- [ ] **Python** (`ms-python.python`)
- [ ] **Pylance** (`ms-python.vscode-pylance`)
- [ ] **Microsoft Foundry Toolkit Extension** (`ms-windows-ai-studio.windows-ai-studio`)

Install via CLI:

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-windows-ai-studio.windows-ai-studio
```

### Optional (Lab 6 local build path)

- [ ] **Docker Desktop** — v24 or later  
  Only needed if attendees run `docker build` locally. Lab 6 supports cloud builds via ACR Tasks as the default path, so Docker is not strictly required.

---

## Repository Setup

- [ ] Clone the repository to a known path (e.g., `C:\Labs\Build26-LAB520`)

```powershell
git clone https://github.com/microsoft/Build26-LAB520.git C:\Labs\Build26-LAB520
```

- [ ] Open the folder in VS Code so it's ready on first launch

---

## Python Virtual Environment & Dependencies

Pre-create the virtual environment and install all packages so attendees don't wait for `pip install`:

```powershell
cd C:\Labs\Build26-LAB520
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r src\agent\requirements.txt
```

### Python Packages — Main (`requirements.txt`)

| Package | Min Version | Purpose |
|---------|-------------|---------|
| `azure-ai-projects` | 1.0.0b7 | Foundry project client (provides OpenAI-compatible inference client) |
| `azure-identity` | 1.19.0 | Azure authentication (DefaultAzureCredential) |
| `openai` | 1.60.0 | OpenAI-compatible API client |
| `python-dotenv` | 1.0.1 | Environment variable management |
| `pytest` | 8.0.0 | Test framework (Lab 4 unit tests) |

### Python Packages — Agent (`src/agent/requirements.txt`)

| Package | Min Version | Purpose |
|---------|-------------|---------|
| `agent-framework-core` | 1.0.0rc3 | Microsoft Agent Framework core |
| `agent-framework-azure-ai` | 1.0.0rc3 | Agent Framework Azure AI integration |
| `azure-ai-agentserver-agentframework` | 1.0.0b17 | Hosted agent server adapter |
| `azure-ai-agentserver-core` | 1.0.0b17 | Agent server core runtime |
| `azure-identity` | 1.19.0 | Azure authentication |
| `python-dotenv` | 1.0.1 | Environment variable management |

---

## Azure Subscription Pre-configuration

Each attendee needs an Azure subscription with the following already configured:

### Authentication

- [ ] `az login` completed (attendee session pre-authenticated)
- [ ] `azd auth login` completed

### RBAC Roles

- [ ] Attendee has **Owner** or **Contributor** role on the subscription (or a dedicated resource group)
- [ ] **Azure AI Owner** or equivalent for Foundry resource creation

### Resource Provider Registration

The following providers must be registered on the subscription:

- [ ] `Microsoft.CognitiveServices`
- [ ] `Microsoft.OperationalInsights`
- [ ] `Microsoft.Insights`
- [ ] `Microsoft.ContainerRegistry`

Register via:

```bash
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
az provider register --namespace Microsoft.ContainerRegistry
```

### Quota

- [ ] The subscription has available quota for `gpt-4.1-mini` (GlobalStandard SKU) in the target region
- [ ] *(Optional for Lab 5)* Quota for a second model (`gpt-4.1`) if cross-model comparison is desired

---

## Network Requirements

- [ ] Outbound HTTPS (443) to `*.azure.com`, `*.microsoft.com`, `*.ai.azure.com`
- [ ] Outbound HTTPS (443) to `pypi.org` and `files.pythonhosted.org` (pip packages, if not pre-cached)
- [ ] Outbound HTTPS (443) to `github.com` (repo clone, if not pre-cloned)
- [ ] No VPN or proxy blocking Azure authentication redirects (`login.microsoftonline.com`)

---

## PowerShell Execution Policy

- [ ] Set to `RemoteSigned` (or `Unrestricted`) so `setup.ps1` and `.venv\Scripts\Activate.ps1` can run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

---

## Azure Resource Deployment

Pre-provision Azure resources for each attendee before the session using one of two approaches:

| Approach | File | Best For |
|----------|------|----------|
| **ARM template** | [`infra/azuredeploy.json`](infra/azuredeploy.json) | Admin pre-provisioning, no extra tooling needed |
| **Bicep + azd** | [`infra/main.bicep`](infra/main.bicep) | Attendee self-service via `setup.ps1` |

See [ARM Deployment Guide](setup/armsetup.md) for step-by-step instructions, batch deployment scripts, and cleanup commands.

---

## Validation

After image build, run the setup script end-to-end to confirm everything works:

```powershell
cd C:\Labs\Build26-LAB520
.\scripts\setup.ps1
```

Then run the offline validation checks:

```powershell
.\.venv\Scripts\Activate.ps1
python src\tests\validate_lab.py
```

Expected result: all offline checks pass (101/101).

---

## Summary Table

| Category | Item | Required |
|----------|------|----------|
| OS | Windows 11 / Server 2022 | Yes |
| Git | v2.40+ | Yes |
| Python | v3.10+ (3.13 recommended) | Yes |
| Azure CLI | v2.67.0+ | Yes |
| Azure Developer CLI | v1.11.0+ | Yes |
| VS Code | Latest stable | Yes |
| VS Code — Python extension | `ms-python.python` | Yes |
| VS Code — Pylance extension | `ms-python.vscode-pylance` | Yes |
| VS Code — Foundry Toolkit | `ms-windows-ai-studio.windows-ai-studio` | Yes |
| Docker Desktop | v24+ | Optional (Lab 6 only) |
| Browser | Edge or Chrome | Yes |
| Python venv + packages | Pre-installed in `.venv` | Yes |
| Repo cloned | `C:\Labs\Build26-LAB520` | Yes |
| Azure auth | `az login` + `azd auth login` | Yes |
| RBAC | Owner/Contributor | Yes |
| Resource providers | 4 providers registered | Yes |
| Network | HTTPS 443 outbound | Yes |
| PowerShell policy | RemoteSigned | Yes |
