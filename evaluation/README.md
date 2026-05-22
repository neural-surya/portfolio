# HelixBot RAGAS Evaluation

This folder contains the RAG quality evaluation for HelixBot. This README only covers `evaluation/test_ragas_eval.py`.

## Purpose

`test_ragas_eval.py` evaluates whether HelixBot's retrieval-augmented generation is grounded, relevant, and supported by retrieved context from the product catalog and FAQ data.

The script:

1. Loads QA pairs from `evaluation/qa_pairs.json`.
2. Calls HelixBot at `POST /api/chat` for each question.
3. Collects the model answer, retrieved contexts, sources, intent, and guard state.
4. Runs RAGAS metrics over retrieval-grounded samples.
5. Writes the full result to `evaluation/results/ragas_scores.json`.
6. Prints a pass/fail summary and deployment recommendation.

## What It Measures

The script runs four RAGAS metrics:

| Metric | Meaning |
| --- | --- |
| `faithfulness` | Whether the answer is grounded in the retrieved contexts instead of unsupported model knowledge. |
| `answer_relevancy` | Whether the answer directly addresses the user question. |
| `context_precision` | Whether the retrieved contexts are ranked with the most relevant context first. |
| `context_recall` | Whether the retrieved contexts contain the information needed to answer the question. |

RAGAS uses evaluator LLM calls to score these metrics, so the run requires an LLM API key and may consume tokens.

## Setup

Start HelixBot before running the evaluation:

```bash
docker compose up --build
```

By default, the script targets:

```bash
http://localhost:8080
```

To use a different HelixBot URL:

```bash
export HELIXBOT_URL=http://localhost:8080
```

Install Python dependencies:

```bash
pip install "ragas>=0.1.21,<0.2" datasets openai httpx python-dotenv
```

Set the OpenAI key used by HelixBot and by RAGAS evaluation:

```bash
export OPENAI_API_KEY=your_key_here
```

The script also attempts to load the repository root `.env` file if `python-dotenv` is installed.

## Running

From the repository root:

```bash
python3.13 evaluation/test_ragas_eval.py
```

If your environment uses a different Python executable:

```bash
python evaluation/test_ragas_eval.py
```

Before collecting answers, the script attempts to reset HelixBot flags and then sets a grounded evaluation state:

```json
{
  "hallucination_guard": true,
  "return_verification": true,
  "rag_poisoning": false,
  "sanitize_context": true
}
```

This prevents previous functional or red-team runs from leaking flag state into the RAGAS evaluation.

## Inputs

Primary input:

```text
evaluation/qa_pairs.json
```

Each QA pair includes:

| Field | Purpose |
| --- | --- |
| `id` | Stable QA identifier, for example `QA-001`. |
| `category` | Test category such as `product_inquiry`, `faq_policy`, or `order_support`. |
| `question` | User question sent to HelixBot. |
| `ground_truth` | Expected factual answer used by RAGAS. |
| `context_keywords` | Human-readable keywords for the expected retrieved context. |
| `owasp` | Related OWASP LLM risk area. |
| `notes` | Test intent and interpretation notes. |

## RAGAS Scope

Only samples with non-empty answers and non-empty retrieved contexts are sent to RAGAS.

`order_support` samples are collected but excluded from RAGAS scoring. Those answers depend on tool outputs, not retrieved RAG context, so including them would distort faithfulness and context metrics.

The output metadata records excluded samples under:

```json
"_meta": {
  "excluded_from_ragas": ["QA-006", "QA-007"]
}
```

## Thresholds

Portfolio thresholds:

| Metric | Required Score |
| --- | ---: |
| `faithfulness` | `>= 0.85` |
| `answer_relevancy` | `>= 0.80` |
| `context_precision` | `>= 0.75` |
| `context_recall` | `>= 0.75` |

CI hard gate:

```text
faithfulness >= 0.75
```

The CI gate is less strict than the portfolio threshold. A run can pass CI while still receiving a conditional deployment recommendation if one of the portfolio thresholds fails.

The script uses a small floating-point tolerance (`EPSILON = 1e-9`) so values that are effectively equal to the threshold, such as `0.749999999925`, are treated correctly.

## Outputs

Primary output:

```text
evaluation/results/ragas_scores.json
```

The result JSON has this shape:

```json
{
  "_meta": {
    "deliverable": "D4A",
    "generated_at": "2026-05-21T00:00:00Z",
    "helixbot_url": "http://localhost:8080",
    "elapsed_seconds": 0,
    "qa_pairs_evaluated": 10,
    "valid_samples": 8,
    "excluded_from_ragas": ["QA-006", "QA-007"]
  },
  "thresholds": {
    "faithfulness": 0.85,
    "answer_relevancy": 0.8,
    "context_precision": 0.75,
    "context_recall": 0.75
  },
  "ci_threshold": 0.75,
  "aggregates": {},
  "threshold_results": {},
  "overall_pass": true,
  "deployment_recommendation": "",
  "per_sample": []
}
```

Important fields:

| Field | Meaning |
| --- | --- |
| `aggregates` | Average score for each RAGAS metric. |
| `threshold_results` | Per-metric score, threshold, and pass/fail result. |
| `overall_pass` | Whether all portfolio thresholds passed. |
| `deployment_recommendation` | One-paragraph recommendation generated from the scores. |
| `per_sample` | Per-question answer, ground truth, retrieved contexts, sources, and metric scores. |

## Deployment Recommendation

The script generates one of three recommendation styles:

| Recommendation | Meaning |
| --- | --- |
| `PASS` | All portfolio RAGAS thresholds passed. |
| `BLOCK` | The CI faithfulness gate failed. Do not promote the build. |
| `CONDITIONAL` | CI faithfulness passed, but one or more portfolio metrics failed. Suitable for demo/non-production only until remediated. |

## Troubleshooting

If HelixBot is not reachable:

```text
ERROR: HelixBot is not reachable at http://localhost:8080
```

Start the application and verify:

```bash
curl -I http://localhost:8080/health
```

If dependencies are missing:

```bash
pip install "ragas>=0.1.21,<0.2" datasets openai httpx python-dotenv
```

If RAGAS reports no valid samples, HelixBot likely returned empty `contexts`. Check that product and FAQ retrieval are working and that `/api/chat` returns a `contexts` array.

If a metric prints as `0.750` but appears close to failing, inspect the raw JSON value in `evaluation/results/ragas_scores.json`. The script includes a small tolerance for floating-point precision.

If results look inconsistent after functional or red-team testing, rerun the script. It resets flags before evaluation, but the HelixBot service must be running and able to accept `/api/flags/reset` and `/api/flags`.
