# Zava Product Review Moderation Agent

A product review moderation pipeline built on **Microsoft Foundry**, deployed as a cloud-hosted agent. Built as part of the Microsoft Build 2026 lab: *Get Started with Models in Microsoft Foundry: From First Inference to Deployed Agent*.

![Agent Status](https://img.shields.io/badge/agent-active-brightgreen) ![Model](https://img.shields.io/badge/model-gpt--4.1--mini-blue) ![Platform](https://img.shields.io/badge/platform-Microsoft%20Foundry-purple)

---

## Demo

### Foundry Playground — Live Agent Classification
![Foundry Playground showing UNSAFE and SAFE classifications](Screenshots/Screenshot%202026-06-07%20130944.png)
![Foundry Playground showing NEEDS_REVIEW classifications](Screenshots/Screenshot%202026-06-07%20132227.png)


### CLI — Remote Agent Invocation via `azd ai agent invoke`
![VS Code terminal showing remote agent invoke returning NEEDS_REVIEW](Screenshots/Screenshot%202026-06-07%20132711.png)

### CLI — Local Agent Test via `python src/02_comment_moderation.py --interactive`
![Terminal showing local agent returning NEEDS_REVIEW with confidence 0.8](Screenshots/Screenshot%202026-06-07%20132912.png)

---

## What This Does

Zava (a fictional global home-improvement retailer) receives thousands of product reviews daily. This project automates moderation by classifying each review into one of three categories:

| Classification | Action | Description |
|---|---|---|
| `SAFE` (confidence ≥ 0.8) | ✅ APPROVED | Review goes live on the site |
| `UNSAFE` (confidence ≥ 0.7) | 🚫 BLOCKED | Review is rejected |
| Everything else | 🔍 FLAGGED_FOR_REVIEW | Sent to human moderation queue |

---

## Architecture

```
Customer Review
      │
      ▼
 Hosted Agent (Foundry)
      │
      ▼
 gpt-4.1-mini ──► JSON Classification
      │              { classification, confidence, reason }
      ▼
 Business Logic Layer
      │
      ├── APPROVED
      ├── FLAGGED_FOR_REVIEW
      └── BLOCKED
```

The agent runs as a **Docker container on Microsoft Foundry Agent Service**, exposed via the OpenAI Responses API. It can be called from the Foundry Playground, other agents, or any HTTP client.

---

## Project Structure

```
├── src/
│   ├── 01_first_inference.py        # Lab 3: Basic chat completion
│   ├── 02_comment_moderation.py     # Lab 4: Full moderation pipeline
│   ├── 03_model_comparison.py       # Lab 5: Multi-model comparison
│   ├── sample_comments.json         # Test dataset (15 reviews)
│   ├── agent/
│   │   ├── app.py                   # Hosted agent (Agent Framework SDK)
│   │   ├── agent.yaml               # Agent manifest
│   │   ├── Dockerfile               # Container definition
│   │   └── requirements.txt         # Agent dependencies
│   └── tests/
│       ├── validate_lab.py          # Environment validation script
│       └── test_moderation.py       # Unit tests for business logic
├── infra/
│   ├── main.bicep                   # Infrastructure orchestration
│   └── modules/
│       ├── ai-services.bicep        # AI Services, project, model, ACR
│       ├── monitoring.bicep         # Application Insights
│       └── role-assignments.bicep   # RBAC configuration
├── azure.yaml                       # azd project configuration
├── .env.sample                      # Environment variable template
└── requirements.txt                 # Python dependencies
```

---

## Key Features

- **Structured JSON output** — system prompt forces `{ classification, confidence, reason }` every time
- **Deterministic classification** — `temperature=0.0` ensures consistent results
- **Confidence-based routing** — business logic layer on top of model output
- **Graceful error handling** — catches Azure content filter blocks and malformed JSON
- **Batch + interactive modes** — process files or type reviews in real time
- **Cloud-hosted** — deployed as a managed container, scales automatically

---

## Setup

### Prerequisites

- Python 3.12+
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- An Azure subscription with Microsoft Foundry access

### 1. Clone and install dependencies

```bash
git clone https://github.com/Rahilyw/review-moderation-agent.git
cd review-moderation-agent
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.sample .env
# Fill in PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME
```

### 3. Validate setup

```bash
python -X utf8 src/tests/validate_lab.py
```

---

## Running Locally

### Basic inference

```bash
python src/01_first_inference.py
```

### Moderation pipeline (batch mode)

```bash
python src/02_comment_moderation.py
```

### Moderation pipeline (file mode)

```bash
python src/02_comment_moderation.py --file src/sample_comments.json
```

### Moderation pipeline (interactive mode)

```bash
python src/02_comment_moderation.py --interactive
```

### Run unit tests

```bash
pytest src/tests/test_moderation.py -v
```

---

## Deploying the Hosted Agent

### 1. Set the Foundry project endpoint

```bash
azd env set FOUNDRY_PROJECT_ENDPOINT "https://<your-resource>.services.ai.azure.com/api/projects/<your-project>"
```

### 2. Deploy

```bash
azd up
```

This builds the Docker image in Azure Container Registry and deploys the agent to Foundry Agent Service.

### 3. Check status

```bash
azd ai agent show --output table
```

### 4. Invoke

```bash
azd ai agent invoke "Love this cordless drill! Battery lasts all day."
```

Expected response:

```json
{
  "classification": "SAFE",
  "confidence": 0.95,
  "reason": "Positive product feedback describing good battery life and torque."
}
```

### 5. Clean up

```bash
azd down --force --purge
```

---

## Example Classifications

| Review | Classification | Action |
|---|---|---|
| "Love this cordless drill! Battery lasts all day." | SAFE (1.00) | ✅ APPROVED |
| "This paint is garbage and whoever designed it should be fired" | NEEDS_REVIEW (0.90) | 🔍 FLAGGED |
| "You're all idiots if you shop here" | UNSAFE (0.90) | 🚫 BLOCKED |
| "Does this deck stain work on pressure-treated lumber?" | SAFE (1.00) | ✅ APPROVED |
| "The drill is excellent but the store staff are completely useless" | NEEDS_REVIEW (0.85) | 🔍 FLAGGED |

---

## How It Works

### The System Prompt

The core of the system is a structured prompt that constrains the model to return only valid JSON:

```python
SYSTEM_PROMPT = """You are a product review moderation system for Zava...
Respond ONLY with valid JSON in this exact format:
{
    "classification": "<SAFE|NEEDS_REVIEW|UNSAFE>",
    "confidence": <0.0-1.0>,
    "reason": "<brief explanation>"
}"""
```

### The Business Logic Layer

The model provides probabilistic output — the code makes deterministic decisions:

```python
def apply_moderation(result: dict) -> str:
    classification = result["classification"]
    confidence = result["confidence"]
    if classification == "SAFE" and confidence >= 0.8:
        return "APPROVED"
    elif classification == "UNSAFE" and confidence >= 0.7:
        return "BLOCKED"
    else:
        return "FLAGGED_FOR_REVIEW"
```

### The Hosted Agent

The same logic runs in the cloud via the Microsoft Agent Framework:

```python
agent = Agent(
    client=FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL_DEPLOYMENT_NAME,
        credential=DefaultAzureCredential(),
    ),
    name="zava-review-moderation-agent",
    instructions=SYSTEM_PROMPT,
)
ResponsesHostServer(agent).run(port=8088)
```

---

## Built With

- [Microsoft Foundry](https://ai.azure.com) — AI model hosting and agent service
- [Azure AI Projects SDK](https://pypi.org/project/azure-ai-projects/) — Foundry project client
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/) — Infrastructure and deployment
- [Microsoft Agent Framework](https://pypi.org/project/agent-framework/) — Hosted agent runtime
- [Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/) — Infrastructure as Code
- `gpt-4.1-mini` — Model used for classification
