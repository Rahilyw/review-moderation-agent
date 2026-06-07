"""
Lab 4: Zava Product Review Moderation
======================================
A working product review moderation pipeline for Zava, a global home-improvement
retailer, using Microsoft Foundry-hosted models.

Usage:
    python 02_comment_moderation.py                          # Process sample comments
    python 02_comment_moderation.py --interactive            # Interactive mode
    python 02_comment_moderation.py --file sample_comments.json  # From file
"""

import argparse
import json
import os
import sys

# Ensure UTF-8 output on Windows (cp1252 cannot encode emoji)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# System prompt -- the core of the moderation logic
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Sample comments for demonstration
# ---------------------------------------------------------------------------
SAMPLE_COMMENTS = [
    "Love this cordless drill! Battery lasts all day and the torque is impressive.",
    "This paint is garbage and whoever designed it should be fired",
    "You're all idiots if you shop here -- worst store ever",
    "Does this deck stain work on pressure-treated lumber?",
    "Meh, the tile cutter is okay. Not great, not terrible.",
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def classify_comment(client, model: str, comment: str) -> dict:
    """Send a comment to the model and get a structured classification."""
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
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "classification": "NEEDS_REVIEW",
            "confidence": 0.0,
            "reason": f"Model returned non-JSON response: {raw[:100]}",
        }

    return result


def apply_moderation(result: dict) -> str:
    """Apply business logic to determine the moderation action."""
    classification = result.get("classification", "NEEDS_REVIEW")
    confidence = result.get("confidence", 0.0)

    if classification == "SAFE" and confidence >= 0.8:
        return "APPROVED"
    elif classification == "UNSAFE" and confidence >= 0.7:
        return "BLOCKED"
    else:
        return "FLAGGED_FOR_REVIEW"


def moderate_comment(client, model: str, comment: str) -> dict:
    """Full moderation pipeline: classify → apply logic → return result."""
    classification = classify_comment(client, model, comment)
    action = apply_moderation(classification)
    return {
        "comment": comment,
        "classification": classification.get("classification", "UNKNOWN"),
        "confidence": classification.get("confidence", 0.0),
        "reason": classification.get("reason", ""),
        "action": action,
    }


ACTION_ICONS = {
    "APPROVED": "\u2705",
    "BLOCKED": "\U0001f6ab",
    "FLAGGED_FOR_REVIEW": "\U0001f50d",
}


def print_result(result: dict, index: int = None, total: int = None):
    """Pretty-print a moderation result."""
    header = f"--- Comment {index}/{total} ---" if index else "---"
    icon = ACTION_ICONS.get(result["action"], "")
    print(header)
    print(f'Comment:  "{result["comment"]}"')
    print(
        f"Classification: {result['classification']} "
        f"(confidence: {result['confidence']:.2f})"
    )
    print(f"Reason:  {result['reason']}")
    print(f"Action:  {icon} {result['action']}")
    print()


# ---------------------------------------------------------------------------
# Execution modes
# ---------------------------------------------------------------------------
def run_samples(client, model: str):
    """Process the built-in sample comments."""
    print(f"\nProcessing {len(SAMPLE_COMMENTS)} sample comments...\n")
    results = []
    for i, comment in enumerate(SAMPLE_COMMENTS, 1):
        result = moderate_comment(client, model, comment)
        print_result(result, index=i, total=len(SAMPLE_COMMENTS))
        results.append(result)
    print_summary(results)


def run_file(client, model: str, filepath: str):
    """Process comments from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        comments = json.load(f)

    print(f"\nProcessing {len(comments)} comments from {filepath}...\n")
    results = []
    for i, item in enumerate(comments, 1):
        comment = item if isinstance(item, str) else item.get("comment", "")
        result = moderate_comment(client, model, comment)
        print_result(result, index=i, total=len(comments))
        results.append(result)
    print_summary(results)


def run_interactive(client, model: str):
    """Interactive mode -- type comments to classify in real time."""
    print("\nInteractive mode. Type a comment and press Enter.")
    print("Type 'quit' to exit.\n")
    while True:
        try:
            comment = input("Enter a comment: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if comment.lower() in ("quit", "exit", "q"):
            break
        if not comment:
            continue
        result = moderate_comment(client, model, comment)
        print_result(result)


def print_summary(results: list[dict]):
    """Print a summary of moderation actions."""
    print("=" * 40)
    print("  Summary")
    print("=" * 40)
    total = len(results)
    counts = {}
    for r in results:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    print(f"Total comments: {total}")
    for action in ("APPROVED", "FLAGGED_FOR_REVIEW", "BLOCKED"):
        print(f"  {action + ':':21s} {counts.get(action, 0)}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME")

    if not endpoint or endpoint.startswith("https://<"):
        print("ERROR: Set PROJECT_ENDPOINT in your .env file (see Lab 2).")
        sys.exit(1)
    if not model:
        print("ERROR: Set MODEL_DEPLOYMENT_NAME in your .env file.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Comment Moderation System")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--file", type=str, help="Path to JSON file with comments")
    args = parser.parse_args()

    # --- Connect ---
    project_client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    inference_client = project_client.get_openai_client()

    print("=" * 40)
    print("  Comment Moderation System")
    print(f"  Model: {model}")
    print("=" * 40)

    try:
        if args.interactive:
            run_interactive(inference_client, model)
        elif args.file:
            run_file(inference_client, model, args.file)
        else:
            run_samples(inference_client, model)
    except HttpResponseError as e:
        if e.status_code == 429:
            print("ERROR: Rate limited. Wait a moment and try again.")
        elif e.status_code == 401:
            print("ERROR: Authentication failed. Run 'az login' and try again.")
        else:
            print(f"ERROR: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
