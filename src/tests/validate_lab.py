"""
Lab Validation Test Suite
==========================
Validates that the workshop repo is correctly structured and all components
work end-to-end. Run this before deploying to Skillable or after setup.

Usage:
    python tests/validate_lab.py                    # Run offline checks only
    python tests/validate_lab.py --live             # Also run live Azure inference tests
    python tests/validate_lab.py --live --agent     # Also test agent deployment
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve repo root (works whether run from repo root or tests/ directory)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

passed = 0
failed = 0
skipped = 0
results = []


def record(name: str, status: str, detail: str = ""):
    global passed, failed, skipped
    icon = {"PASS": "\u2705", "FAIL": "\u274c", "SKIP": "\u23ed\ufe0f"}.get(status, "?")
    results.append((name, status, detail))
    if status == "PASS":
        passed += 1
    elif status == "FAIL":
        failed += 1
    else:
        skipped += 1
    line = f"  {icon} {name}"
    if detail:
        line += f" — {detail}"
    print(line)


# =========================================================================
# SECTION 1: File Structure Checks
# =========================================================================
def test_file_structure():
    print("\n" + "=" * 60)
    print("  Section 1: File Structure")
    print("=" * 60)

    required_files = [
        "README.md",
        "azure.yaml",
        "requirements.txt",
        ".env.sample",
        # Infra
        "infra/main.bicep",
        "infra/main.parameters.json",
        "infra/abbreviations.json",
        "infra/modules/ai-services.bicep",
        "infra/modules/monitoring.bicep",
        "infra/modules/role-assignments.bicep",
        # Setup & cleanup
        "setup/SETUP.md",
        "cleanup/CLEANUP.md",
        # Scripts
        "scripts/setup.ps1",
        "scripts/setup.sh",
        "scripts/postprovision.ps1",
        "scripts/postprovision.sh",
        # Labs
        "docs/lab1-discover-models.md",
        "docs/lab2-project-setup.md",
        "docs/lab3-connect-and-infer.md",
        "docs/lab4-comment-moderation.md",
        "docs/lab5-model-comparison.md",
        "docs/lab6-deploy-agent.md",
        "docs/lab7-summary.md",
        # Source
        "src/01_first_inference.py",
        "src/02_comment_moderation.py",
        "src/03_model_comparison.py",
        "src/sample_comments.json",
        # Agent (Hosted Agent — container-based)
        "src/agent/app.py",
        "src/agent/Dockerfile",
        "src/agent/requirements.txt",
        "src/agent/agent.yaml",
        # Tests
        "src/tests/TESTING.md",
        "src/tests/validate_lab.py",
    ]

    for f in required_files:
        path = REPO_ROOT / f
        if path.exists():
            record(f"File exists: {f}", "PASS")
        else:
            record(f"File exists: {f}", "FAIL", "Missing")


# =========================================================================
# SECTION 2: JSON Validation
# =========================================================================
def test_json_files():
    print("\n" + "=" * 60)
    print("  Section 2: JSON Validity")
    print("=" * 60)

    json_files = [
        "src/sample_comments.json",
        "infra/main.parameters.json",
        "infra/abbreviations.json",
    ]

    for f in json_files:
        path = REPO_ROOT / f
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            record(f"JSON valid: {f}", "PASS")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            record(f"JSON valid: {f}", "FAIL", str(e))

    # Verify sample_comments.json structure
    path = REPO_ROOT / "src/sample_comments.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            comments = json.load(fh)
        if isinstance(comments, list) and len(comments) == 15:
            record("sample_comments.json has 15 entries", "PASS")
        else:
            record("sample_comments.json has 15 entries", "FAIL", f"Got {len(comments)}")
        valid_labels = {"SAFE", "NEEDS_REVIEW", "UNSAFE"}
        all_valid = all(c.get("expected") in valid_labels for c in comments)
        if all_valid:
            record("sample_comments.json labels valid", "PASS")
        else:
            record("sample_comments.json labels valid", "FAIL", "Invalid expected labels")
    except Exception as e:
        record("sample_comments.json structure", "FAIL", str(e))


# =========================================================================
# SECTION 3: Python Syntax Validation
# =========================================================================
def test_python_syntax():
    print("\n" + "=" * 60)
    print("  Section 3: Python Syntax")
    print("=" * 60)

    py_files = [
        "src/01_first_inference.py",
        "src/02_comment_moderation.py",
        "src/03_model_comparison.py",
        "src/agent/app.py",
    ]

    for f in py_files:
        path = REPO_ROOT / f
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            record(f"Syntax OK: {f}", "PASS")
        else:
            record(f"Syntax OK: {f}", "FAIL", result.stderr.strip())


# =========================================================================
# SECTION 4: Markdown Navigation Chain
# =========================================================================
def test_markdown_links():
    print("\n" + "=" * 60)
    print("  Section 4: Markdown Navigation Chain")
    print("=" * 60)

    # Expected navigation: Setup → Lab1 → Lab2 → Lab3 → Lab4 → Lab5 → Lab6 → Lab7 → Cleanup
    nav_chain = [
        ("setup/SETUP.md", "docs/lab1-discover-models.md"),
        ("docs/lab1-discover-models.md", "docs/lab2-project-setup.md"),
        ("docs/lab2-project-setup.md", "docs/lab3-connect-and-infer.md"),
        ("docs/lab3-connect-and-infer.md", "docs/lab4-comment-moderation.md"),
        ("docs/lab4-comment-moderation.md", "docs/lab5-model-comparison.md"),
        ("docs/lab5-model-comparison.md", "docs/lab6-deploy-agent.md"),
        ("docs/lab6-deploy-agent.md", "docs/lab7-summary.md"),
        ("docs/lab7-summary.md", "cleanup/CLEANUP.md"),
    ]

    for source, target in nav_chain:
        source_path = REPO_ROOT / source
        # The link in the source file references the target relative to source's directory
        target_filename = Path(target).name
        try:
            content = source_path.read_text(encoding="utf-8")
            if target_filename in content:
                record(f"Nav link: {Path(source).name} → {target_filename}", "PASS")
            else:
                record(f"Nav link: {Path(source).name} → {target_filename}", "FAIL", "Link not found")
        except FileNotFoundError:
            record(f"Nav link: {Path(source).name} → {target_filename}", "FAIL", "Source file missing")


# =========================================================================
# SECTION 5: Model Reference Consistency
# =========================================================================
def test_model_references():
    print("\n" + "=" * 60)
    print("  Section 5: Model Reference Consistency")
    print("=" * 60)

    # Ensure deprecated model names are gone
    deprecated = ["gpt-4o-mini", "gpt-4o"]
    all_files = list(REPO_ROOT.rglob("*"))
    # Exclude this validation script itself — it contains deprecated names as test data
    self_path = Path(__file__).resolve()
    text_files = [
        f for f in all_files
        if f.is_file()
        and f.suffix in (".md", ".py", ".bicep", ".json", ".yaml", ".yml", ".ps1", ".sh", ".sample")
        and ".git" not in str(f)
        and ".venv" not in str(f)
        and f.resolve() != self_path
    ]

    for old_model in deprecated:
        found_in = []
        for f in text_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if old_model in content:
                    found_in.append(str(f.relative_to(REPO_ROOT)))
            except Exception:
                pass
        if not found_in:
            record(f"No references to deprecated '{old_model}'", "PASS")
        else:
            record(
                f"No references to deprecated '{old_model}'",
                "FAIL",
                f"Found in: {', '.join(found_in[:5])}",
            )

    # Ensure new model names are present where expected
    expected_model_refs = {
        "gpt-4.1-mini": [
            "infra/main.bicep",
            ".env.sample",
            "src/agent/app.py",
        ],
        "gpt-4.1": [
            "infra/main.bicep",
            ".env.sample",
        ],
    }
    for model, files in expected_model_refs.items():
        for f in files:
            path = REPO_ROOT / f
            try:
                content = path.read_text(encoding="utf-8")
                if model in content:
                    record(f"'{model}' referenced in {f}", "PASS")
                else:
                    record(f"'{model}' referenced in {f}", "FAIL", "Not found")
            except FileNotFoundError:
                record(f"'{model}' referenced in {f}", "FAIL", "File missing")


# =========================================================================
# SECTION 6: Infrastructure Validation
# =========================================================================
def test_infra():
    print("\n" + "=" * 60)
    print("  Section 6: Infrastructure Files")
    print("=" * 60)

    # Check azure.yaml has correct hooks
    azure_yaml = REPO_ROOT / "azure.yaml"
    try:
        content = azure_yaml.read_text(encoding="utf-8")
        for keyword in ["postprovision", "postprovision.ps1", "postprovision.sh"]:
            if keyword in content:
                record(f"azure.yaml contains '{keyword}'", "PASS")
            else:
                record(f"azure.yaml contains '{keyword}'", "FAIL")
    except FileNotFoundError:
        record("azure.yaml exists", "FAIL")

    # Check main.bicep has required params
    bicep_path = REPO_ROOT / "infra/main.bicep"
    try:
        content = bicep_path.read_text(encoding="utf-8")
        for param in [
            "environmentName",
            "location",
            "modelName",
            "deploySecondModel",
            "enableHostedAgents",
            "principalId",
        ]:
            if param in content:
                record(f"main.bicep param: {param}", "PASS")
            else:
                record(f"main.bicep param: {param}", "FAIL")

        # Check outputs
        for output in [
            "AZURE_RESOURCE_GROUP",
            "AZURE_AI_PROJECT_ENDPOINT",
            "MODEL_DEPLOYMENT_NAME",
            "AZURE_CONTAINER_REGISTRY_NAME",
        ]:
            if output in content:
                record(f"main.bicep output: {output}", "PASS")
            else:
                record(f"main.bicep output: {output}", "FAIL")
    except FileNotFoundError:
        record("main.bicep exists", "FAIL")

    # Check main.parameters.json binds all expected vars
    params_path = REPO_ROOT / "infra/main.parameters.json"
    try:
        content = params_path.read_text(encoding="utf-8")
        for var in [
            "AZURE_ENV_NAME",
            "AZURE_LOCATION",
            "AZURE_PRINCIPAL_ID",
            "DEPLOY_SECOND_MODEL",
            "ENABLE_HOSTED_AGENTS",
        ]:
            if var in content:
                record(f"parameters.json binds {var}", "PASS")
            else:
                record(f"parameters.json binds {var}", "FAIL")
    except FileNotFoundError:
        record("main.parameters.json exists", "FAIL")


# =========================================================================
# SECTION 7: Hosted Agent Files
# =========================================================================
def test_agent_service():
    print("\n" + "=" * 60)
    print("  Section 7: Hosted Agent")
    print("=" * 60)

    # Check app.py uses hosting adapter pattern
    app_path = REPO_ROOT / "src/agent/app.py"
    try:
        content = app_path.read_text(encoding="utf-8")
        if "Agent" in content and "from agent_framework import" in content:
            record("app.py uses Agent", "PASS")
        else:
            record("app.py uses Agent", "FAIL")
        if "from_agent_framework" in content:
            record("app.py uses hosting adapter", "PASS")
        else:
            record("app.py uses hosting adapter", "FAIL")
        if "AzureAIAgentClient" in content:
            record("app.py uses AzureAIAgentClient", "PASS")
        else:
            record("app.py uses AzureAIAgentClient", "FAIL")
    except FileNotFoundError:
        record("app.py exists", "FAIL")

    # Check Dockerfile exposes port 8088
    docker_path = REPO_ROOT / "src/agent/Dockerfile"
    try:
        content = docker_path.read_text(encoding="utf-8")
        if "8088" in content:
            record("Dockerfile exposes port 8088", "PASS")
        else:
            record("Dockerfile exposes port 8088", "FAIL")
        if "app.py" in content:
            record("Dockerfile runs app.py", "PASS")
        else:
            record("Dockerfile runs app.py", "FAIL")
    except FileNotFoundError:
        record("Dockerfile exists", "FAIL")

    # Check agent.yaml manifest
    manifest_path = REPO_ROOT / "src/agent/agent.yaml"
    try:
        content = manifest_path.read_text(encoding="utf-8")
        if "hosted" in content:
            record("agent.yaml kind: hosted", "PASS")
        else:
            record("agent.yaml kind: hosted", "FAIL")
        if "responses" in content:
            record("agent.yaml protocol: responses", "PASS")
        else:
            record("agent.yaml protocol: responses", "FAIL")
    except FileNotFoundError:
        record("agent.yaml exists", "FAIL")

    # Check requirements.txt has hosting adapter packages
    req_path = REPO_ROOT / "src/agent/requirements.txt"
    try:
        content = req_path.read_text(encoding="utf-8")
        if "azure-ai-agentserver" in content:
            record("requirements.txt includes hosting adapter", "PASS")
        else:
            record("requirements.txt includes hosting adapter", "FAIL")
        if "agent-framework" in content:
            record("requirements.txt includes agent-framework", "PASS")
        else:
            record("requirements.txt includes agent-framework", "FAIL")
    except FileNotFoundError:
        record("Agent requirements.txt exists", "FAIL")

    # Check azure.yaml has agent service config
    azure_yaml = REPO_ROOT / "azure.yaml"
    try:
        content = azure_yaml.read_text(encoding="utf-8")
        if "azure.ai.agent" in content:
            record("azure.yaml host: azure.ai.agent", "PASS")
        else:
            record("azure.yaml host: azure.ai.agent", "FAIL")
        if "remoteBuild" in content:
            record("azure.yaml docker remoteBuild", "PASS")
        else:
            record("azure.yaml docker remoteBuild", "FAIL")
    except FileNotFoundError:
        record("azure.yaml exists", "FAIL")


# =========================================================================
# SECTION 8: Environment Configuration
# =========================================================================
def test_env_config():
    print("\n" + "=" * 60)
    print("  Section 8: Environment Configuration")
    print("=" * 60)

    # Check .env.sample has required vars
    sample_path = REPO_ROOT / ".env.sample"
    try:
        content = sample_path.read_text(encoding="utf-8")
        for var in ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME_2"]:
            if var in content:
                record(f".env.sample contains {var}", "PASS")
            else:
                record(f".env.sample contains {var}", "FAIL")
    except FileNotFoundError:
        record(".env.sample exists", "FAIL")

    # Check if .env exists and is configured (for live tests)
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        from dotenv import dotenv_values
        values = dotenv_values(env_path)
        endpoint = values.get("PROJECT_ENDPOINT", "")
        model = values.get("MODEL_DEPLOYMENT_NAME", "")
        if endpoint and not endpoint.startswith("https://<"):
            record(".env PROJECT_ENDPOINT configured", "PASS")
        else:
            record(".env PROJECT_ENDPOINT configured", "FAIL", "Placeholder or missing")
        if model:
            record(".env MODEL_DEPLOYMENT_NAME configured", "PASS")
        else:
            record(".env MODEL_DEPLOYMENT_NAME configured", "FAIL", "Missing")
    else:
        record(".env file exists", "SKIP", "Not yet created — run setup first")


# =========================================================================
# SECTION 9: Dependency Check
# =========================================================================
def test_dependencies():
    print("\n" + "=" * 60)
    print("  Section 9: Python Dependencies")
    print("=" * 60)

    required_packages = [
        ("azure.ai.projects", "azure-ai-projects"),
        ("azure.identity", "azure-identity"),
        ("openai", "openai"),
        ("dotenv", "python-dotenv"),
    ]

    for module_name, pip_name in required_packages:
        try:
            importlib.import_module(module_name)
            record(f"Package installed: {pip_name}", "PASS")
        except ImportError:
            record(f"Package installed: {pip_name}", "FAIL", f"pip install {pip_name}")


# =========================================================================
# SECTION 10: CLI Tool Check
# =========================================================================
def test_cli_tools():
    print("\n" + "=" * 60)
    print("  Section 10: CLI Tools")
    print("=" * 60)

    tools = {
        "az": ["az", "version", "--output", "json"],
        "azd": ["azd", "version"],
        "python": [sys.executable, "--version"],
        "git": ["git", "--version"],
    }

    use_shell = sys.platform == "win32"  # needed to find .cmd wrappers (az.cmd)

    for name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=use_shell)
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0][:60]
                record(f"CLI available: {name}", "PASS", version)
            else:
                record(f"CLI available: {name}", "FAIL", result.stderr.strip()[:80])
        except FileNotFoundError:
            record(f"CLI available: {name}", "FAIL", "Not installed")
        except subprocess.TimeoutExpired:
            record(f"CLI available: {name}", "FAIL", "Timed out")

    # Docker is optional (for Lab 6 Option B)
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=10, shell=use_shell
        )
        if result.returncode == 0:
            record("CLI available: docker (optional)", "PASS", result.stdout.strip()[:60])
        else:
            record("CLI available: docker (optional)", "SKIP", "Not running")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        record("CLI available: docker (optional)", "SKIP", "Not installed — use ACR Tasks for Lab 6")


# =========================================================================
# SECTION 11: Live Azure Inference Tests (--live flag)
# =========================================================================
def test_live_inference():
    print("\n" + "=" * 60)
    print("  Section 11: Live Azure Inference")
    print("=" * 60)

    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        record("Live test: .env required", "SKIP", "Run setup first")
        return

    from dotenv import load_dotenv
    load_dotenv(env_path)

    endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME", "")

    if not endpoint or endpoint.startswith("https://<"):
        record("Live test: endpoint configured", "SKIP", "PROJECT_ENDPOINT not set")
        return

    # Test 1: Basic inference (Lab 3)
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        client = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        inference = client.get_openai_client()
        response = inference.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Respond with exactly: HELLO"},
                {"role": "user", "content": "Say hello"},
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content
        if content:
            record("Live: Basic inference", "PASS", f"Response: {content[:50]}")
        else:
            record("Live: Basic inference", "FAIL", "Empty response")
    except Exception as e:
        record("Live: Basic inference", "FAIL", str(e)[:100])

    # Test 2: Comment moderation classification (Lab 4)
    try:
        moderation_prompt = textwrap.dedent("""\
            You are a content moderation system. Classify the comment.
            Respond ONLY with valid JSON: {"classification": "<SAFE|NEEDS_REVIEW|UNSAFE>", "confidence": <0.0-1.0>, "reason": "<text>"}
        """)

        test_cases = [
            ("Great product!", "SAFE"),
            ("I will find you and hurt you", "UNSAFE"),
        ]

        all_correct = True
        for comment, expected in test_cases:
            try:
                response = inference.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": moderation_prompt},
                        {"role": "user", "content": comment},
                    ],
                    temperature=0.0,
                )
                raw = response.choices[0].message.content.strip()
                try:
                    result = json.loads(raw)
                    classification = result.get("classification", "")
                    if classification == expected:
                        record(
                            f"Live: Classify '{comment[:30]}...'",
                            "PASS",
                            f"{classification} (confidence: {result.get('confidence', '?')})",
                        )
                    else:
                        record(
                            f"Live: Classify '{comment[:30]}...'",
                            "FAIL",
                            f"Expected {expected}, got {classification}",
                        )
                        all_correct = False
                except json.JSONDecodeError:
                    record(f"Live: Classify '{comment[:30]}...'", "FAIL", f"Non-JSON: {raw[:50]}")
                    all_correct = False
            except Exception as cf_err:
                # Azure content safety filter may block UNSAFE test inputs — treat as correct
                if expected == "UNSAFE" and "content_filter" in str(cf_err).lower() or "filtered" in str(cf_err).lower():
                    record(
                        f"Live: Classify '{comment[:30]}...'",
                        "PASS",
                        "Content filter triggered (equivalent to UNSAFE)",
                    )
                else:
                    record(f"Live: Classify '{comment[:30]}...'", "FAIL", str(cf_err)[:100])
                    all_correct = False
    except Exception as e:
        record("Live: Moderation classification", "FAIL", str(e)[:100])

    # Test 3: Second model (Lab 5) — optional
    model2 = os.environ.get("MODEL_DEPLOYMENT_NAME_2", "")
    if model2:
        try:
            response = inference.chat.completions.create(
                model=model2,
                messages=[
                    {"role": "system", "content": "Respond with exactly: OK"},
                    {"role": "user", "content": "Confirm"},
                ],
                temperature=0.0,
            )
            if response.choices[0].message.content:
                record("Live: Second model inference", "PASS", f"Model: {model2}")
            else:
                record("Live: Second model inference", "FAIL", "Empty response")
        except Exception as e:
            record("Live: Second model inference", "FAIL", str(e)[:100])
    else:
        record("Live: Second model inference", "SKIP", "MODEL_DEPLOYMENT_NAME_2 not set")


# =========================================================================
# SECTION 12: Agent Deployment Test (--agent flag)
# =========================================================================
def test_agent_deployment():
    print("\n" + "=" * 60)
    print("  Section 12: Agent Deployment (Lab 6)")
    print("=" * 60)

    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        record("Agent test: .env required", "SKIP", "Run setup first")
        return

    from dotenv import load_dotenv
    load_dotenv(env_path)

    acr_name = os.environ.get("AZURE_CONTAINER_REGISTRY_NAME", "")
    if not acr_name:
        record("Agent test: ACR configured", "SKIP", "AZURE_CONTAINER_REGISTRY_NAME not set")
        record("Agent test", "SKIP", "Run: azd env set ENABLE_HOSTED_AGENTS true && azd provision")
        return

    record("Agent test: ACR configured", "PASS", f"ACR: {acr_name}")

    # Check if Docker or ACR Tasks are available
    docker_available = False
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=10
        )
        docker_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if docker_available:
        record("Agent test: Docker available", "PASS", "Can build locally")
    else:
        record("Agent test: Docker available", "SKIP", "Use 'az acr build' instead")

    record(
        "Agent test: Manual steps required",
        "SKIP",
        "Run deploy_agent.py and invoke_agent.py manually per Lab 6",
    )


# =========================================================================
# Summary
# =========================================================================
def print_summary():
    print("\n" + "=" * 60)
    print("  VALIDATION SUMMARY")
    print("=" * 60)
    total = passed + failed + skipped
    print(f"  Total checks: {total}")
    print(f"  \u2705 Passed:  {passed}")
    print(f"  \u274c Failed:  {failed}")
    print(f"  \u23ed\ufe0f  Skipped: {skipped}")
    print()

    if failed > 0:
        print("  FAILED CHECKS:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"    \u274c {name}: {detail}")
        print()
        print("  Result: FAIL — fix the issues above before running the lab.")
        return 1
    else:
        print("  Result: PASS — lab is ready!")
        return 0


# =========================================================================
# Main
# =========================================================================
def main():
    parser = argparse.ArgumentParser(description="Validate workshop lab setup")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live Azure inference tests (requires .env with valid credentials)",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Also test agent deployment infrastructure (requires ACR)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Workshop Lab Validation")
    print("  Get Started with Models in Microsoft Foundry")
    print("=" * 60)

    # Always run offline checks
    test_file_structure()
    test_json_files()
    test_python_syntax()
    test_markdown_links()
    test_model_references()
    test_infra()
    test_agent_service()
    test_env_config()
    test_dependencies()
    test_cli_tools()

    # Optionally run live tests
    if args.live:
        test_live_inference()

    if args.agent:
        test_agent_deployment()

    exit_code = print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
