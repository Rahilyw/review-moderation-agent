# Lab 2: Create and Configure a Foundry Project

> **Duration:** ~15 minutes | **Phase:** Project Setup

## Objective

Create a Microsoft Foundry project using the Azure Developer CLI (azd), provision the required infrastructure, and configure your local development environment for model inference.

---

## What is a Foundry Project?

A Foundry **project** is the organizational unit within Microsoft Foundry that groups together:

- Model deployments
- Agents
- Evaluations
- Files and data assets

Projects are created within a **Foundry account** (Azure AI Services resource) and provide the endpoint your application code connects to.

**Why do you need one?** A Foundry project acts as a single connection point for all your AI resources -- models, agents, evaluations, and data -- so your code only needs one endpoint and one set of credentials to access everything.

> [Learn more: Create a project in Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/how-to/create-projects)

---

> **Which option should I pick?** Use **Option A** -- it runs one script and does everything for you. Option B below covers the same steps manually, one at a time. It is there for reference or troubleshooting, not something you need to follow. **If you are unsure, choose Option A.**

## Option A: One-Command Setup (Recommended)

The fastest way to provision everything is the included setup script. From the **workshop root directory**, run:

**Windows (PowerShell):**

```powershell
.\scripts\setup.ps1
```

**Linux / macOS:**

```bash
./scripts/setup.sh
```

This script will:

1. Verify all prerequisites (Azure CLI, azd, Python)
2. Log you into Azure and azd
3. Create and activate a Python virtual environment (`.venv`)
4. Initialize the azd environment
5. Provision all infrastructure (Foundry account, project, model deployment, monitoring)
6. Install Python dependencies into the virtual environment
7. Write your `.env` file automatically

> **⏱ Provisioning takes approximately 5-10 minutes.**

**Optional flags:**

| Flag | Effect |
|------|--------|
| `-Location swedencentral` / `-l swedencentral` | Deploy to a different region |
| `-DeploySecondModel` / `-s` | Also deploy `gpt-4.1` for Lab 5 comparison |
| `-SkipProvision` / `--skip-provision` | Skip Azure provisioning (if resources already exist) |

After the script completes, skip to **Step 8: Verify in Foundry Portal** and then **Step 9: Validate Your Setup** below.

---

<details>
<summary><strong>Option B: Step-by-Step Manual Setup</strong> (click to expand)</summary>

If you prefer to understand each step, follow the manual process below.

### Step 1: Initialize the azd Environment

From the workshop root directory (which contains `azure.yaml` and the `infra/` folder):

```bash
azd init --no-prompt -e foundry-lab
```

### Step 2: Create and Activate a Virtual Environment

Create a Python virtual environment to keep lab dependencies isolated:

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt. Install the lab dependencies:

```bash
pip install -r requirements.txt
```

> **Tip:** Visual Studio Code can activate the venv automatically -- when prompted, select the Python interpreter inside `.venv`.

### Step 3: Configure the Azure Region

Set the region where you have model quota (verified in Lab 1):

```bash
azd env set AZURE_LOCATION northcentralus
```

> **Common regions with model availability:** `eastus`, `eastus2`, `westus3`, `northcentralus`, `swedencentral`

### Step 4: Set Your Principal ID (for RBAC)

This grants your user account the `Cognitive Services OpenAI User` and `Cognitive Services Contributor` roles on the provisioned AI Services resource:

```bash
# Get your Azure AD object ID
az ad signed-in-user show --query id -o tsv
```

```bash
azd env set AZURE_PRINCIPAL_ID <your-principal-id>
```

### Step 5: (Optional) Enable Second Model for Lab 5

To deploy `gpt-4.1` alongside `gpt-4.1-mini` for the model comparison lab:

```bash
azd env set DEPLOY_SECOND_MODEL true
```

### Step 6: Provision Infrastructure

```bash
azd provision --no-prompt
```

This deploys the Bicep templates in `infra/` and creates:

| Resource | Purpose |
|----------|---------|
| Resource group (`rg-foundry-lab`) | Container for all resources |
| Azure AI Services account | Foundry account (model host) |
| Foundry project | Organizes models, agents, evaluations |
| `gpt-4.1-mini` deployment | Primary model for Labs 3-4 |
| `gpt-4.1` deployment *(optional)* | Second model for Lab 5 |
| Log Analytics workspace | Telemetry storage |
| Application Insights | Project monitoring |
| RBAC role assignments | Your user gets OpenAI User + Contributor |

> **⏱ This takes approximately 5-10 minutes.** Wait for it to complete.

You will see output like:

```
SUCCESS: Your application was provisioned in Azure in XX minutes XX seconds.
```

### Step 7: Retrieve and Configure Environment

After provisioning, the **post-provision hook** automatically creates your `.env` file. Verify it:

> **What is a `.env` file?** It is a plain text file that stores configuration values (like your project endpoint and model name) as `KEY=VALUE` pairs. The `python-dotenv` package loads these into your Python scripts automatically via `load_dotenv()`, so you never hardcode secrets or endpoints in your source code.

```bash
azd env get-values
```

Key outputs:

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_AI_PROJECT_ENDPOINT` | Your project endpoint URL | `https://ai-xxxx.services.ai.azure.com/api/projects/foundry-lab-project` |
| `AZURE_RESOURCE_GROUP` | Resource group name | `rg-foundry-lab` |
| `MODEL_DEPLOYMENT_NAME` | Primary model | `gpt-4.1-mini` |

Check that `.env` was written:

```bash
cat .env
```

If `.env` is missing, copy from the sample and edit manually:

```bash
cp .env.sample .env
# Edit PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME with values from azd env get-values
```

</details>

---

## Step 8: Verify in Foundry Portal

1. Open **[https://ai.azure.com](https://ai.azure.com)**
2. You should see your new project listed
3. Click into the project and verify:
   - The project endpoint matches your `.env`
   - Your model deployment appears under **Deployments**

---

## Step 9: Validate Your Setup

Run the included validation script to confirm that all files, dependencies, CLI tools, and configuration are correct:

```bash
python -X utf8 src/tests/validate_lab.py
```

> **Note:** Use the `-X utf8` flag on Windows to avoid encoding errors. On Linux/macOS you can omit it.

You should see output ending with:

```
  VALIDATION SUMMARY
  Total checks: 100
  ✅ Passed:  100
  ❌ Failed:  0

  Result: PASS  - lab is ready!
```

If any checks fail, the output tells you exactly what to fix. Common issues:

| Failure | Fix |
|---------|-----|
| Missing file | Re-check your `azd provision` output for errors |
| CLI not found | Install the missing tool (see [SETUP.md](../setup/SETUP.md)) |
| Package not installed | Run `pip install -r requirements.txt` inside your `.venv` |
| `.env` not configured | Copy `.env.sample` to `.env` and fill in your endpoint |

> **Tip:** Re-run validation after any fix to confirm it resolves the issue.

---

## What You Learned

- ✅ How to provision a Foundry project using azd with Bicep templates
- ✅ How infrastructure-as-code works (resource group, AI Services, project, model deployments)
- ✅ How azd post-provision hooks automate environment configuration
- ✅ How RBAC role assignments grant your user model access
- ✅ How to retrieve project configuration for SDK use
- ✅ How to validate your setup with the automated validation script

---

## Checkpoint

Before moving on, confirm all of the following:

- [ ] `.env` file exists and contains `PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME`
- [ ] `python -X utf8 src/tests/validate_lab.py` shows all checks passing
- [ ] `azd env get-values` shows your project endpoint and resource group
- [ ] Your Foundry project is visible at [ai.azure.com](https://ai.azure.com)

If validation fails, check the failure messages -- common issues include missing `.env` values or incomplete provisioning.

---

## Key Takeaway

> A Foundry project is your workspace for organizing AI resources. The project endpoint is the single connection point your application code needs to access any model deployed within it.

---

**Next:** [Lab 3 - Connect & Infer →](lab3-connect-and-infer.md)
