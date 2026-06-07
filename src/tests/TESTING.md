# Testing Instructions

Verify your lab work at each phase by running these checks.

---

## Phase 3: First Inference

```bash
python src/01_first_inference.py
```

**Pass criteria:**

- [ ] Script runs without errors
- [ ] Model response is printed to terminal
- [ ] Token usage is displayed
- [ ] Response is relevant to "What is Microsoft Foundry"

**Common issues:**

| Error | Fix |
|-------|-----|
| `PROJECT_ENDPOINT not set` | Edit `.env`  - set your project endpoint from Lab 2 |
| `401 Unauthorized` | Run `az login` and retry |
| `404 Not Found` | Verify `MODEL_DEPLOYMENT_NAME` matches an active deployment |
| `429 Rate Limited` | Wait 30 seconds and retry |

---

## Phase 4: Comment Moderation

### Test 1: Sample Comments

```bash
python src/02_comment_moderation.py
```

**Pass criteria:**

- [ ] All 5 sample comments are classified
- [ ] Each result shows classification, confidence, reason, and action
- [ ] Summary counts are printed
- [ ] Threatening comment ("I will find you...") is classified as UNSAFE
- [ ] Positive comment ("Great article!") is classified as SAFE

### Test 2: File Input

```bash
python src/02_comment_moderation.py --file src/sample_comments.json
```

**Pass criteria:**

- [ ] All 15 comments from the JSON file are processed
- [ ] No JSON parsing errors in the output
- [ ] Summary is printed at the end

### Test 3: Interactive Mode

```bash
python src/02_comment_moderation.py --interactive
```

**Pass criteria:**

- [ ] Prompt appears: `Enter a comment:`
- [ ] Typing a comment returns a classification
- [ ] Typing `quit` exits cleanly

### Test 4: Classification Accuracy

Review the output from Test 2 and compare against the `expected` labels in `sample_comments.json`. The model should correctly classify most comments:

| Expected Accuracy | Status |
|-------------------|--------|
| > 80% agreement | Good |
| 60-80% agreement | Acceptable  - try adjusting the system prompt |
| < 60% | Review your system prompt or try a different model |

---

## Phase 5: Model Comparison (Optional)

### Test 5: Side-by-Side Comparison

```bash
python src/03_model_comparison.py
```

**Pass criteria:**

- [ ] Each comment shows results from both models (or one if only one deployed)
- [ ] Latency is measured for each model
- [ ] Agreement rate is displayed in the summary

### Test 6: Hybrid Mode

```bash
python src/03_model_comparison.py --hybrid
```

**Pass criteria:**

- [ ] Low-confidence classifications are escalated to the secondary model
- [ ] Escalation count is displayed at the end
- [ ] Escalated comments show the secondary model name

---

## Quick Validation Script

Run all tests in sequence:

```bash
echo "=== Phase 3: First Inference ===" && \
python src/01_first_inference.py && \
echo "" && \
echo "=== Phase 4: Comment Moderation (samples) ===" && \
python src/02_comment_moderation.py && \
echo "" && \
echo "=== Phase 4: Comment Moderation (file) ===" && \
python src/02_comment_moderation.py --file src/sample_comments.json && \
echo "" && \
echo "=== All tests passed ==="
```

---

## Phase 6: Deploy Agent

### Test 7: Deploy Hosted Agent

```bash
python src/agent/deploy_agent.py
```

**Pass criteria:**

- [ ] Agent container image builds successfully
- [ ] Agent is created in Foundry project
- [ ] Container status reaches `Running`
- [ ] Test message returns a valid moderation classification

### Test 8: Invoke Agent

```bash
python src/agent/invoke_agent.py
```

**Pass criteria:**

- [ ] Test comments are sent to the deployed agent
- [ ] Each response contains classification, confidence, reason, and action fields
- [ ] Threatening comment is classified as UNSAFE
- [ ] Positive comment is classified as SAFE

### Test 9: Stop Agent

```bash
python src/agent/invoke_agent.py --stop
```

**Pass criteria:**

- [ ] Agent container is stopped
- [ ] No errors returned during teardown

---

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `ModuleNotFoundError` | Dependencies not installed | `pip install -r requirements.txt` |
| `EnvironmentError` | Missing `.env` values | Copy `.env.sample` to `.env` and fill in values |
| JSON parse errors in moderation | Model returning free text | Check that `SYSTEM_PROMPT` includes "Respond ONLY with valid JSON" |
| All comments classified the same | Temperature too high or prompt too vague | Ensure `temperature=0.0` and review system prompt |
| `HttpResponseError 429` | Rate limiting | Wait 30-60 seconds, reduce request frequency |
| Connection timeout | Network or endpoint issue | Verify endpoint URL, check `az account show` |
