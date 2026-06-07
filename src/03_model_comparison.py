"""
Lab 5: Model Comparison for Zava Review Moderation
================================================
Compare how different models classify the same Zava product reviews.
Measures agreement, confidence, and latency.

Usage:
    python 03_model_comparison.py              # Side-by-side comparison
    python 03_model_comparison.py --hybrid     # Hybrid escalation mode
"""

import argparse
import json
import os
import sys
import time

# Ensure UTF-8 output on Windows (cp1252 cannot encode emoji)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# Reuse the same system prompt from Lab 4
SYSTEM_PROMPT = """You are a product review moderation system for Zava, a global home-improvement retailer. Analyze the provided customer review and classify it.

Respond ONLY with valid JSON in this exact format:
{
    "classification": "<SAFE|NEEDS_REVIEW|UNSAFE>",
    "confidence": <0.0-1.0>,
    "reason": "<brief explanation>"
}

Classification rules:
- SAFE: Constructive product feedback, installation questions, positive experiences, neutral observations about products or services
- NEEDS_REVIEW: Borderline content, strong complaints about products or staff, potential sarcasm, frustration without abuse
- UNSAFE: Hate speech, threats toward staff or customers, harassment, explicit content, personal attacks

Do not include any text outside the JSON object."""

TEST_COMMENTS = [
    "Love this cordless drill! Battery lasts all day and the torque is impressive.",
    "This paint is garbage and whoever designed it should be fired",
    "You're all idiots if you shop here -- worst store ever",
    "Does this deck stain work on pressure-treated lumber?",
    "The staff are useless and ugly -- never going back to this Zava location",
    "Meh, the tile cutter is okay. Not great, not terrible.",
    "I respectfully disagree with the 5-star ratings -- the sander vibrates too much.",
    "LOL Zava sells overpriced junk, are they even trying???",
]


def classify_comment(client, model: str, comment: str) -> dict:
    """Classify a single comment using the given model."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": comment},
            ],
            temperature=0.0,
        )
    except Exception as e:
        if "content_filter" in str(e) or "content management policy" in str(e):
            return {
                "classification": "UNSAFE",
                "confidence": 1.0,
                "reason": "Blocked by Azure content safety filter.",
            }
        raise
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "classification": "NEEDS_REVIEW",
            "confidence": 0.0,
            "reason": f"Non-JSON response: {raw[:80]}",
        }


def compare_models(client, models: list[str], comment: str) -> list[dict]:
    """Run the same comment through multiple models and collect results."""
    results = []
    for model in models:
        start = time.time()
        result = classify_comment(client, model, comment)
        elapsed = time.time() - start
        results.append(
            {
                "model": model,
                "classification": result["classification"],
                "confidence": result["confidence"],
                "reason": result["reason"],
                "latency_ms": round(elapsed * 1000),
            }
        )
    return results


def hybrid_classify(
    client, primary: str, secondary: str, comment: str, threshold: float = 0.8
) -> dict:
    """Use the primary model first; escalate to secondary if confidence is low."""
    start = time.time()
    result = classify_comment(client, primary, comment)
    primary_latency = round((time.time() - start) * 1000)

    escalated = False
    if result["confidence"] < threshold:
        start = time.time()
        result = classify_comment(client, secondary, comment)
        secondary_latency = round((time.time() - start) * 1000)
        escalated = True
        total_latency = primary_latency + secondary_latency
        model_used = secondary
    else:
        total_latency = primary_latency
        model_used = primary

    return {
        "comment": comment,
        "model_used": model_used,
        "escalated": escalated,
        "classification": result["classification"],
        "confidence": result["confidence"],
        "reason": result["reason"],
        "latency_ms": total_latency,
    }


def run_comparison(client, models: list[str]):
    """Side-by-side comparison of models on all test comments."""
    print("=" * 60)
    print("  Model Comparison: Comment Moderation")
    print("=" * 60)

    all_results = []
    for comment in TEST_COMMENTS:
        print(f'\nComment: "{comment}"')
        print()
        results = compare_models(client, models, comment)
        all_results.append(results)

        # Table header
        print(
            f"  {'Model':<20s} {'Classification':<16s} "
            f"{'Confidence':<12s} {'Latency':<10s} Reason"
        )
        print(f"  {'-'*18:<20s} {'-'*14:<16s} {'-'*10:<12s} {'-'*8:<10s} {'-'*20}")
        for r in results:
            print(
                f"  {r['model']:<20s} {r['classification']:<16s} "
                f"{r['confidence']:<12.2f} {str(r['latency_ms'])+'ms':<10s} "
                f"{r['reason'][:40]}"
            )

    # Summary
    print("\n" + "=" * 60)
    print("  Comparison Summary")
    print("=" * 60)

    agreements = sum(
        1
        for r in all_results
        if len(set(x["classification"] for x in r)) == 1
    )
    total = len(all_results)
    print(f"  Agreement rate: {agreements}/{total} ({agreements/total*100:.0f}%)")

    for model in models:
        latencies = [
            x["latency_ms"]
            for results in all_results
            for x in results
            if x["model"] == model
        ]
        avg = sum(latencies) / len(latencies) if latencies else 0
        print(f"  Avg latency - {model}: {avg:.0f}ms")
    print()


def run_hybrid(client, primary: str, secondary: str):
    """Hybrid escalation mode."""
    print("=" * 60)
    print("  Hybrid Moderation (Escalation Mode)")
    print(f"  Primary: {primary} | Secondary: {secondary}")
    print(f"  Escalation threshold: confidence < 0.8")
    print("=" * 60)

    escalation_count = 0
    for comment in TEST_COMMENTS:
        result = hybrid_classify(client, primary, secondary, comment)
        icon = "\u2b06\ufe0f " if result["escalated"] else "  "
        print(f'\n{icon}"{comment}"')
        print(
            f"   Model: {result['model_used']} | "
            f"{result['classification']} ({result['confidence']:.2f}) | "
            f"{result['latency_ms']}ms"
        )
        if result["escalated"]:
            escalation_count += 1

    print(f"\n  Escalated: {escalation_count}/{len(TEST_COMMENTS)} comments")
    print()


def main():
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    model_1 = os.environ.get("MODEL_DEPLOYMENT_NAME")
    model_2 = os.environ.get("MODEL_DEPLOYMENT_NAME_2")

    if not endpoint or endpoint.startswith("https://<"):
        print("ERROR: Set PROJECT_ENDPOINT in your .env file.")
        sys.exit(1)
    if not model_1:
        print("ERROR: Set MODEL_DEPLOYMENT_NAME in your .env file.")
        sys.exit(1)
    if not model_2:
        print(
            "NOTE: MODEL_DEPLOYMENT_NAME_2 not set. "
            "Using only MODEL_DEPLOYMENT_NAME for demo."
        )
        print("      Set MODEL_DEPLOYMENT_NAME_2 in .env for a real comparison.\n")
        model_2 = model_1

    parser = argparse.ArgumentParser(description="Model Comparison")
    parser.add_argument("--hybrid", action="store_true", help="Hybrid escalation mode")
    args = parser.parse_args()

    project_client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    inference_client = project_client.get_openai_client()

    models = [model_1, model_2] if model_1 != model_2 else [model_1]

    if args.hybrid and len(models) == 2:
        run_hybrid(inference_client, models[0], models[1])
    else:
        if args.hybrid and len(models) < 2:
            print("WARN: Hybrid requires two models. Running comparison instead.\n")
        run_comparison(inference_client, models)


if __name__ == "__main__":
    main()
