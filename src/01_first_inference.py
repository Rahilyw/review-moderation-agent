"""
Lab 3: First Inference with Microsoft Foundry
==============================================
Connect to a Foundry project and send your first inference request to a hosted model.

Scenario: You are Serena, a developer at Zava (a global home-improvement retailer),
exploring Microsoft Foundry to power AI features for the Zava platform.
"""

import os
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


def main():
    # --- Validate environment ---
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME")

    if not endpoint or endpoint.startswith("https://<"):
        print("ERROR: Set PROJECT_ENDPOINT in your .env file (see Lab 2).")
        sys.exit(1)
    if not model:
        print("ERROR: Set MODEL_DEPLOYMENT_NAME in your .env file.")
        sys.exit(1)

    # --- Connect to Foundry project ---
    print("Connecting to Foundry project...")
    project_client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )

    # --- Get inference client ---
    inference_client = project_client.get_openai_client()

    # --- Send inference request ---
    print(f"Sending inference request to model: {model}")
    response = inference_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for Zava, a global home-improvement retailer. Respond concisely.",
            },
            {
                "role": "user",
                "content": "What is Microsoft Foundry and how could a retailer like Zava use it? Answer in one sentence.",
            },
        ],
    )

    # --- Process response ---
    content = response.choices[0].message.content
    print("---")
    print(f"Response:\n{content}")
    print("---")
    print(f"Model: {response.model}")
    print(f"Finish reason: {response.choices[0].finish_reason}")
    print(
        f"Tokens used: {response.usage.total_tokens} "
        f"(prompt: {response.usage.prompt_tokens}, "
        f"completion: {response.usage.completion_tokens})"
    )


if __name__ == "__main__":
    main()
