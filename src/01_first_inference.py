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
    user_input = "I'm Bruno and I'm renovating my kitchen. What tools do I need to install new cabinets?"
    temperature = 0.0

    print(f"Sending inference request to model: {model}")
    response = inference_client.chat.completions.create(
        model= model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You are Cora, Zava's friendly AI shopping assistant. Help customers find the right home-improvement products."},
            {"role": "user", "content": user_input},
        ],
    )

    print("User:", user_input)
    print("Temperature:", temperature)
    print("Response:\n", response.choices[0].message.content)

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
