# Lab 5: Compare Model Outputs (Optional Extension)

> **Duration:** ~15 minutes | **Phase:** Extension Challenge

## Objective

Compare how different hosted models classify the same Zava product reviews, measure response quality and latency, and help Serena make an informed decision about which model to deploy for Zava's review moderation pipeline.

---

## Why Compare Models?

Different models have different strengths:

| Model | Strengths | Trade-offs |
|-------|-----------|-----------|
| `gpt-4.1-mini` | Fast, cost-efficient, good for simple tasks | May miss nuance in complex cases |
| `gpt-4.1` | Higher reasoning quality, better at edge cases | Slower, more expensive |
| `Phi-4` | Open-weight, strong reasoning, runs on-device | May need different prompt tuning |

Comparing models on your **actual Zava review data** helps Serena make informed deployment decisions.

---

## Prerequisites

To complete this lab, you need **two model deployments** in your Foundry project. Update your `.env`:

```ini
MODEL_DEPLOYMENT_NAME=gpt-4.1-mini
MODEL_DEPLOYMENT_NAME_2=gpt-4.1
```

If you only have one model deployed, deploy a second one using:

```bash
az cognitiveservices account deployment create \
  --name <your-foundry-resource-name> \
  --resource-group rg-foundry-lab \
  --deployment-name gpt-4.1 \
  --model-name gpt-4.1 \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "GlobalStandard"
```

### Single-Model Alternative

If you only have **one model** deployed, you can still get meaningful comparison insights by varying **how** you call it rather than **which** model you call. Try these experiments with `src/02_comment_moderation.py`:

**1. Compare prompt strategies** -- Edit the system prompt in `classify_comment()` to be stricter or more lenient:

```python
# Strict: lower tolerance
"Classify as UNSAFE if there is any negativity or personal criticism."

# Lenient: higher tolerance
"Only classify as UNSAFE if the comment contains explicit threats or slurs."
```

Run the script with each prompt and compare how classifications change for the same comments.

**2. Compare temperature settings** -- Change `temperature=0.0` to `temperature=0.7` and run the moderation script several times. At `0.0`, results should be identical every run; at `0.7`, you may see classification drift on borderline comments.

**3. Compare output formats** -- Modify the system prompt to return a plain text label instead of JSON. Compare how reliably you can parse the response vs. the structured JSON approach.

These experiments teach the same core lesson as multi-model comparison: **small changes in configuration produce measurably different results**, and you should test systematically before committing to a production setup.

---

## Step 1: Review the Comparison Code

Open `src/03_model_comparison.py`. The key function runs the same comment through multiple models:

```python
def compare_models(client, models: list[str], comment: str) -> list[dict]:
    results = []
    for model in models:
        start = time.time()
        result = classify_comment(client, model, comment)
        elapsed = time.time() - start
        results.append({
            "model": model,
            "classification": result["classification"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "latency_ms": round(elapsed * 1000),
        })
    return results
```

---

## Step 2: Run the Comparison

```bash
python src/03_model_comparison.py
```

### Expected Output

```
========================================
  Model Comparison: Zava Review Moderation
========================================

Comment: "This paint is garbage and whoever designed it should be fired"

  Model         Classification  Confidence  Latency   Reason
  ------------- -------------- ----------  --------  ------
  gpt-4.1-mini   NEEDS_REVIEW   0.75        324ms     Strong negative sentiment...
  gpt-4.1        NEEDS_REVIEW   0.80        891ms     Borderline personal attack toward staff...

Comment: "You're all idiots if you shop here -- worst store ever"

  Model         Classification  Confidence  Latency   Reason
  ------------- -------------- ----------  --------  ------
  gpt-4.1-mini   UNSAFE         0.95        298ms     Contains insults directed at customers
  gpt-4.1        UNSAFE         0.98        845ms     Personal attacks targeting customers

========================================
  Comparison Summary
========================================
  Agreement rate: 100% (both models agreed on all classifications)
  Avg latency - gpt-4.1-mini: 310ms
  Avg latency - gpt-4.1:      868ms
  Cost ratio:  gpt-4.1-mini is ~10x cheaper per token
```

---

## Step 3: Analyze the Results

Look for patterns in the comparison:

### Agreement

Do both models classify comments the same way? If they disagree, which model would you trust for your use case?

### Confidence

Does the more capable model consistently give higher confidence scores? Higher confidence may justify the additional cost for borderline cases.

### Latency

How much slower is the larger model? For real-time moderation (e.g., chat), latency matters. For batch processing, it may not.

### Cost

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|----------------------|
| `gpt-4.1-mini` | ~$0.15 | ~$0.60 |
| `gpt-4.1` | ~$2.50 | ~$10.00 |

**Estimating your lab cost:** Each moderation request uses roughly 250 input tokens (system prompt + comment) and 50 output tokens (JSON response). With 5 sample comments across 2 models, that is 10 requests total:

| | Input tokens | Output tokens | Cost per 1M tokens (input/output) | Estimated cost |
|---|---|---|---|---|
| `gpt-4.1-mini` | 5 × 250 = 1,250 | 5 × 50 = 250 | $0.15 / $0.60 | **$0.0003** |
| `gpt-4.1` | 5 × 250 = 1,250 | 5 × 50 = 250 | $2.50 / $10.00 | **$0.006** |
| **Total for this lab** | | | | **< $0.01** |

Even running the full `sample_comments.json` (15 Zava reviews × 2 models = 30 requests) stays well under $0.01. The cost difference becomes meaningful at Zava's scale -- at 100,000 reviews/day, `gpt-4.1-mini` costs ~$5/day vs. `gpt-4.1` at ~$80/day.

> **Tip:** For this type of classification task, `gpt-4.1-mini` often matches `gpt-4.1` performance at a fraction of the cost.

---

## Step 4: Try a Hybrid Approach

A common production pattern is to use the cheaper model first and escalate disagreements to the more capable model.

The comparison script includes a `--hybrid` mode:

```bash
python src/03_model_comparison.py --hybrid
```

This runs `gpt-4.1-mini` first. If confidence is below 0.8, it re-runs with `gpt-4.1` for a second opinion.

---

## Extension Challenges

If you finish early, try these:

1. **Add a third model** -- Deploy `Phi-4` and add it to the comparison
2. **Create your own test set** -- Write 10 Zava product reviews that span edge cases (returns complaints, competitor mentions, sarcastic praise)
3. **Measure consistency** -- Run the same review 5 times and check if classification varies (it should not at `temperature=0.0`)
4. **Adjust the prompt** -- Make the system prompt stricter about complaints toward Zava staff and see how it changes classifications

---

## What You Learned

- ✅ How to run the same inference across multiple models
- ✅ How to compare classification quality, confidence, and latency
- ✅ How to make model selection decisions based on task requirements
- ✅ How to implement a hybrid escalation pattern

---

## Key Takeaway

> Model selection is a product decision, not just a technical one. By programmatically comparing models on your actual task data, you can optimize for the right balance of quality, speed, and cost.

---

**Next:** [Lab 6 - Deploy Agent →](lab6-deploy-agent.md)
