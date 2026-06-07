# FY26 Build Session Outline

**Title of session:** Get Started with Models in Microsoft Foundry: From First Inference to Deployed Agent

**Session ID:** LAB520

**As of:** 04/24/2026

---

## Session Flow: 75 minutes (Lab 5 available as self-paced extension)

**Speaker:** Lee Stott

---

### Act One: Discover and Connect (23 min)

**Introduction — Setting the Scene**
3 min | Lee Stott
Content: SPEAKER-ONLY
Introduce the Zava scenario: attendees play the role of Serena, a developer at a global home-improvement retailer, tasked with building an automated product review moderation system. Explain what Microsoft Foundry is and why developers should care — production-ready hosted models, no fine-tuning required.

**Lab 1: Discover Models in Microsoft Foundry**
10 min | Lee Stott
Content: DEMO
Attendees navigate the Foundry portal (ai.azure.com), browse the model catalog, evaluate model capabilities (gpt-4.1-mini, gpt-4.1, Phi-4), check quota and region availability, and optionally test a Zava review moderation prompt in the Playground.

**Lab 2: Create and Configure a Foundry Project**
10 min | Lee Stott
Content: DEMO
Attendees run the one-command setup script (`setup.ps1` / `setup.sh`) which provisions all Azure infrastructure via azd and Bicep — AI Services account, Foundry project, model deployment (gpt-4.1-mini), monitoring, RBAC, and local `.env` configuration. Covers what azd does and why Infrastructure-as-Code matters.

---

### Act Two: Build and Moderate (32 min)

**Lab 3: Connect and Send Your First Inference**
12 min | Lee Stott
Content: DEMO
Write Python code using `AIProjectClient` (Azure AI Projects SDK) to authenticate with `DefaultAzureCredential`, obtain an OpenAI-compatible inference client via `get_openai_client()`, and send a first chat completion request. Explore message roles, token usage, temperature settings, and error scenarios.

**Lab 4: Build a Product Review Moderation Application**
20 min | Lee Stott
Content: DEMO
Build a complete moderation pipeline for Zava product reviews. Design a structured system prompt that returns JSON classifications (SAFE / NEEDS_REVIEW / UNSAFE), add a business logic layer with confidence thresholds for auto-approve, auto-block, and human review routing. Process sample reviews in batch and interactive modes.

**Lab 5: Compare Model Outputs (Self-Paced Extension — not included in 75-min session)**
15 min | Lee Stott
Content: DEMO
Run identical Zava product reviews through gpt-4.1-mini and gpt-4.1 to compare classification quality, confidence scores, latency, and cost. Demonstrate a hybrid escalation pattern — cheap model first, escalate to premium model when confidence is low. Discuss model selection as a product decision. *Attendees can complete this lab at home using the lab instructions.*

---

### Act Three: Deploy and Wrap Up (20 min)

**Lab 6: Deploy a Hosted Agent**
15 min | Lee Stott
Content: DEMO
Package the Zava review moderation logic as a hosted agent using the Microsoft Agent Framework SDK. Review the agent code (`app.py`), Dockerfile, and `agent.yaml` manifest. Deploy to Foundry Agent Service with `azd up` (builds container in ACR, deploys to managed infrastructure). Test the live agent via CLI (`azd ai agent invoke`) and the Foundry Playground.

**Lab 7: Summary, Key Takeaways, Q&A, and Next Steps**
5 min | Lee Stott
Content: SPEAKER-ONLY, GRAPHICS
Recap the full journey: model discovery → project setup → first inference → moderation pipeline → hosted agent. Point attendees to Lab 5 (model comparison) as a self-paced extension. Call out specific related sessions at Build 2026. Share additional resources and next steps. Take audience questions through chat.

---

## Goals

- **Goal 1:** Attendees can discover, provision, and connect to hosted models in Microsoft Foundry using the Azure AI Projects SDK and OpenAI client — going from zero to a working inference call in minutes.
- **Goal 2:** Attendees can build a production-quality product review moderation pipeline that classifies content as safe, needs review, or unsafe using structured prompts and business logic — and compare outputs across models to make informed deployment decisions.
- **Goal 3:** Attendees can package application logic into a hosted agent on Foundry Agent Service using the Microsoft Agent Framework, deploying a persistent cloud service with `azd up` — no infrastructure management required.

---

## Nurture (Marketing/Sales Alignment)

This lab targets developers and AI engineers who are evaluating Microsoft Foundry for production AI workloads. The session demonstrates a complete developer workflow — from model discovery through deployment — using a realistic enterprise scenario (Zava product review moderation). Key value propositions reinforced: no fine-tuning needed, OpenAI SDK compatibility, managed infrastructure for agents, and the `azd` developer experience for provisioning and deployment. Attendees leave with working code they can adapt to their own use cases, driving adoption of Microsoft Foundry, Azure AI Services, and the Azure Developer CLI.

---

## Leave Behind Resources

- **Resource 1:** [Microsoft Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/) — Official docs for Foundry projects, models, and agents
- **Resource 2:** [OpenAI SDK migration guide](https://learn.microsoft.com/azure/foundry/how-to/model-inference-to-openai-migration) — Reference for the OpenAI SDK pattern used in this lab
- **Resource 3:** [Lab GitHub repository](https://github.com/microsoft/Build26-LAB520) — Complete source code, lab instructions, and infrastructure templates attendees can clone and run at home
- **Resource 4:** [Azure Developer CLI documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/) — Getting started with azd for provisioning and deploying
- **Resource 5:** [Foundry Toolkit for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-windows-ai-studio.windows-ai-studio) — Extension for working with Foundry projects in VS Code
- **Resource 6:** [Build 2026 next steps](https://aka.ms/build26-next-steps) — Continue the learning journey after Build
