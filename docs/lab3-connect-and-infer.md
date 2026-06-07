# Lab 3: Connect and Send Your First Inference

> **Duration:** ~15 minutes | **Phase:** Code-First Interaction

## Objective

As Serena (Zava's developer), write Python code that authenticates against your Foundry project, connects to a hosted model endpoint, and sends your first inference request -- laying the groundwork for Zava's review moderation system.

---

## Concepts

| Concept | Description |
|---------|-------------|
| **AIProjectClient** | SDK client that connects to your Foundry project |
| **DefaultAzureCredential** | Automatic credential chain -- uses your `az login` session locally |
| **Chat Completion** | Send a system prompt + user message, receive a model response |
| **Inference Endpoint** | The API endpoint your model deployment exposes |

---

## Step 1: Review the Code

Open `src/01_first_inference.py` in your editor. The following sections walk through it step by step.

### Authentication and Client Setup

```python
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
```

This creates a project client authenticated with your Azure credentials. The `PROJECT_ENDPOINT` comes from your `.env` file (configured in Lab 2).

### Getting an Inference Client

```python
inference_client = project_client.get_openai_client()
```

The project client provides an OpenAI-compatible client for chat completions. This client is pre-configured with your project's endpoint and credentials.

### Sending a Request

```python
response = inference_client.chat.completions.create(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    messages=[
        {"role": "system", "content": "You are a helpful assistant for Zava, a global home-improvement retailer. Respond concisely."},
        {"role": "user", "content": "What is Microsoft Foundry and how could a retailer like Zava use it? Answer in one sentence."},
    ],
)
```

The `chat.completions.create()` method sends a chat completion request with:

- **model** -- The deployment name (e.g., `gpt-4.1-mini`)
- **messages** -- An array of conversation messages with roles (`system`, `user`, `assistant`)

### Processing the Response

```python
print(response.choices[0].message.content)
```

The response object contains an array of `choices`. Each choice has a `message` with `content` -- the model's text response.

---

## Step 2: Run the Code

Make sure your `.env` file is configured (from Lab 2), then run:

```bash
python src/01_first_inference.py
```

### Expected Output

```
Connecting to Foundry project...
Sending inference request to model: gpt-4.1-mini
---
Response:
Microsoft Foundry is a unified platform for discovering, deploying, and
managing AI models, which Zava could use to power product recommendations,
review moderation, and customer support agents at scale.
---
Model: gpt-4.1-mini
Tokens used: 52 (prompt: 30, completion: 22)
```

> **Note:** The first inference request may take 3-5 seconds due to cold start (the model endpoint warming up). Subsequent requests in the same session are typically much faster (under 2 seconds). This is normal behavior -- if you see a delay on the first call, just wait for the response.

### Troubleshooting Common Errors

If the script fails, check the table below before asking for help:

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'PROJECT_ENDPOINT'` | `.env` file is missing or incomplete | Run `azd env get-values > .env` to regenerate it |
| `AuthenticationError` or `DefaultAzureCredential failed` | Azure CLI session expired | Run `az login` and try again |
| `Connection timed out` after 30+ seconds | Endpoint is unreachable | Check your network/VPN; verify the endpoint URL in `.env` |
| `ResourceNotFoundError` | Model deployment name does not match | Run `az cognitiveservices account deployment list` to check the exact name |

---

## Step 3: Experiment

Try modifying the code to explore different behaviors:

### Change the System Prompt

Edit the system message to change the model's behavior:

```python
{"role": "system", "content": "You are Cora, Zava's friendly AI shopping assistant. Help customers find the right home-improvement products."},
```

### Change the User Input

```python
{"role": "user", "content": "I'm Bruno and I'm renovating my kitchen. What tools do I need to install new cabinets?"},
```

### Add Temperature Control

```python
response = inference_client.chat.completions.create(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    messages=[...],
    temperature=0.0,  # Deterministic output
)
```

| Temperature | Behavior |
|-------------|----------|
| `0.0` | Deterministic -- same input produces same output |
| `0.7` | Balanced creativity (default) |
| `1.0` | Maximum creativity / variability |

> **For Zava's review moderation tasks (Lab 4), use `temperature=0.0`** to get consistent, reproducible classifications.

### Break It on Purpose

The best way to understand what each piece does is to remove it and see what happens. Try these experiments (undo each change before the next):

| Experiment | What to Change | What Happens |
|------------|---------------|---------------|
| Remove the system prompt | Delete the `{"role": "system", ...}` message | The model gives a generic answer instead of a focused one |
| Send an empty user message | Change content to `""` | The model may return an empty response or ask for clarification |
| Use a nonsense model name | Change `MODEL_DEPLOYMENT_NAME` to `"fake-model"` | You get a `ResourceNotFoundError` -- the SDK cannot find the deployment |
| Remove `load_dotenv()` | Comment out the line | `KeyError: 'PROJECT_ENDPOINT'` -- Python cannot read your `.env` file |

These errors are the same ones you will hit in real projects. Seeing them now makes them easier to diagnose later.

---

## Step 4: Understand the Response Object

The full response object contains useful metadata:

```python
print(f"Model: {response.model}")
print(f"Finish reason: {response.choices[0].finish_reason}")
print(f"Prompt tokens: {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")
```

| Field | Description |
|-------|-------------|
| `model` | The model that generated the response |
| `finish_reason` | Why generation stopped (`stop`, `length`, `content_filter`) |
| `usage.prompt_tokens` | Tokens consumed by your input |
| `usage.completion_tokens` | Tokens generated in the response |
| `usage.total_tokens` | Total tokens (drives cost) |

---

## What You Learned

- ✅ How to authenticate with `DefaultAzureCredential`
- ✅ How to create an `AIProjectClient` connected to your Foundry project
- ✅ How to obtain an inference client for chat completions
- ✅ How to send a structured message (system + user) to a model
- ✅ How to process the response programmatically
- ✅ How to read token usage metadata

---

## Checkpoint

Before moving on, confirm:

- [ ] Running `python src/01_first_inference.py` returns a text response (not an error)
- [ ] The output shows `Model: gpt-4.1-mini` (or your chosen model)
- [ ] Token usage is displayed (prompt + completion tokens)

If any of these fail, check your `.env` file has the correct `PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` values.

---

## Key Takeaway

> Connecting to a Foundry-hosted model takes three lines of setup: load credentials, create a project client, get an OpenAI-compatible client. From there, every interaction follows the same request/response pattern.

---

**Next:** [Lab 4 - Zava Review Moderation App →](lab4-comment-moderation.md)
