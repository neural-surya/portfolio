"""
D4A — RAGAS Evaluation Script for HelixBot
===========================================
Deliverable: D4A | HelixBot LLM Testing Capstone | Suryakanta

What this script does:
  1. Loads 10 QA pairs from evaluation/qa_pairs.json (question + ground truth)
  2. Sends each question to HelixBot POST /api/chat and captures:
       - reply (the answer)
       - contexts (raw retrieved document passages from ChromaDB)
  3. Runs RAGAS evaluation across 4 metrics:
       - faithfulness:        Does the answer use ONLY information from the retrieved contexts?
       - answer_relevancy:    Is the answer relevant to the question asked?
       - context_precision:   Are the retrieved contexts ranked with the most relevant first?
       - context_recall:      Does the retrieved context contain all information needed to answer?
  4. Saves full results to evaluation/results/ragas_scores.json
  5. Prints a pass/fail summary against configured thresholds

Pre-requisites:
  pip install ragas datasets openai httpx

Thresholds (from manifest.json D4A):
  faithfulness:      >= 0.85
  answer_relevancy:  >= 0.80
  context_precision: >= 0.75
  context_recall:    >= 0.75

How to run:
  # Ensure HelixBot is running on http://localhost:8080
  # The script resets flags automatically, then enables grounded RAGAS settings:
  #   hallucination_guard=true, return_verification=true,
  #   rag_poisoning=false, sanitize_context=true
  python evaluation/test_ragas_eval.py

CI/CD note:
  The GitHub Actions pipeline (D5) runs this script and checks that
  the average faithfulness score meets the >= 0.75 gate.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Load capstone root .env before reading any env vars (no-op if file absent)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed — rely on shell environment

HELIXBOT_URL = os.getenv("HELIXBOT_URL", "http://localhost:8080")
QA_PAIRS_FILE = Path(__file__).parent / "qa_pairs.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_FILE = RESULTS_DIR / "ragas_scores.json"
REPORT_FILE = Path(__file__).parent / "reports" / "eval_report.md"

THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
    "context_precision": 0.75,
    "context_recall": 0.75,
}

# CI gate threshold (less strict than portfolio threshold — used in pipeline)
CI_THRESHOLD = 0.75
EPSILON = 1e-9


async def query_helixbot(client: httpx.AsyncClient, question: str, qa_id: str) -> dict:
    """Send a question to HelixBot and return the full ChatResponse."""
    response = await client.post(
        f"{HELIXBOT_URL}/api/chat",
        json={
            "message": question,
            "sessionId": f"ragas-eval-{qa_id}",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


async def collect_responses(qa_pairs: list[dict]) -> list[dict]:
    """Send all QA questions to HelixBot and collect answers + retrieved contexts."""
    collected = []
    async with httpx.AsyncClient() as client:
        for qa in qa_pairs:
            print(f"  Querying HelixBot for {qa['id']}: {qa['question'][:60]}...")
            try:
                result = await query_helixbot(client, qa["question"], qa["id"])
                collected.append({
                    "qa_id": qa["id"],
                    "category": qa["category"],
                    "question": qa["question"],
                    "answer": result.get("reply", ""),
                    "contexts": result.get("contexts", []),
                    "ground_truth": qa["ground_truth"],
                    "intent": result.get("intent", ""),
                    "sources": result.get("sources", []),
                    "guard_triggered": result.get("guard_triggered", False),
                })
            except Exception as exc:
                print(f"  ERROR querying {qa['id']}: {exc}")
                collected.append({
                    "qa_id": qa["id"],
                    "category": qa["category"],
                    "question": qa["question"],
                    "answer": "",
                    "contexts": [],
                    "ground_truth": qa["ground_truth"],
                    "error": str(exc),
                })
    return collected


def run_ragas_evaluation(collected: list[dict]) -> dict:
    """
    Run RAGAS evaluation on the collected responses.

    RAGAS requires a HuggingFace Dataset with columns:
      - question
      - answer
      - contexts  (list of strings — raw retrieved passages)
      - ground_truth

    Returns a dict with per-sample scores and aggregate averages.
    """
    # ragas API changed significantly at v0.2. We support both:
    #   < 0.2  (old): from ragas.metrics import faithfulness  (lowercase instances)
    #   >= 0.2 (new): from ragas.metrics import Faithfulness  (class-based)
    # Pin for reproducibility: pip install "ragas>=0.1.21,<0.2" datasets openai httpx
    try:
        from datasets import Dataset
        from ragas import evaluate
        try:
            # ragas < 0.2 API (lowercase metric instances)
            from ragas.metrics import (
                answer_relevancy,
                context_precision,
                context_recall,
                faithfulness,
            )
        except ImportError:
            # ragas >= 0.2 API (class-based metrics)
            from ragas.metrics import (
                AnswerRelevancy as answer_relevancy,
                ContextPrecision as context_precision,
                ContextRecall as context_recall,
                Faithfulness as faithfulness,
            )
    except ImportError as exc:
        print(f"\nMissing dependency: {exc}")
        print("Install with: pip install 'ragas>=0.1.21,<0.2' datasets openai httpx")
        sys.exit(1)

    # RAGAS evaluates retrieval-grounded answers. Tool-calling order support
    # answers are validated in test_function_calling.py; their evidence comes
    # from tool outputs, not retrieved RAG contexts, so including them here
    # would make faithfulness/context scores misleading.
    valid = [
        c for c in collected
        if c.get("answer") and c.get("contexts") and not c.get("error")
        and c.get("category") != "order_support"
    ]

    if not valid:
        print("\nERROR: No valid samples with contexts — cannot run RAGAS.")
        print("Ensure HelixBot is running and returning non-empty contexts in ChatResponse.")
        sys.exit(1)

    print(f"\n  Running RAGAS on {len(valid)}/{len(collected)} valid samples...")

    dataset = Dataset.from_list([
        {
            "question": s["question"],
            "answer": s["answer"],
            "contexts": s["contexts"],
            "ground_truth": s["ground_truth"],
        }
        for s in valid
    ])

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    # RAGAS evaluate() returns a dict-like result; convert to DataFrame for per-sample scores
    scores_df = result.to_pandas()

    # Build per-sample output
    per_sample = []
    for i, row in scores_df.iterrows():
        sample_data = valid[i]
        per_sample.append({
            "qa_id": sample_data["qa_id"],
            "category": sample_data["category"],
            "question": sample_data["question"],
            "answer": sample_data["answer"],
            "ground_truth": sample_data["ground_truth"],
            "sources": sample_data.get("sources", []),
            "contexts": sample_data.get("contexts", []),
            "scores": {
                "faithfulness": float(row.get("faithfulness", 0)),
                "answer_relevancy": float(row.get("answer_relevancy", 0)),
                "context_precision": float(row.get("context_precision", 0)),
                "context_recall": float(row.get("context_recall", 0)),
            },
        })

    # Aggregate averages
    aggregates = {
        metric: float(scores_df[metric].mean())
        for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        if metric in scores_df.columns
    }

    return {
        "per_sample": per_sample,
        "aggregates": aggregates,
    }


def check_thresholds(aggregates: dict) -> dict:
    """Compare aggregate scores against thresholds. Returns pass/fail per metric."""
    results = {}
    for metric, threshold in THRESHOLDS.items():
        score = aggregates.get(metric, 0.0)
        results[metric] = {
            "score": score,
            "threshold": threshold,
            "passed": score + EPSILON >= threshold,
        }
    return results


def print_report(aggregates: dict, threshold_results: dict, elapsed: float) -> None:
    """Print a formatted console report."""
    print("\n" + "=" * 60)
    print("RAGAS EVALUATION RESULTS — HelixBot D4A")
    print("=" * 60)
    print(f"{'Metric':<25} {'Score':>8}  {'Threshold':>10}  {'Status':>8}")
    print("-" * 60)
    for metric, data in threshold_results.items():
        status = "PASS" if data["passed"] else "FAIL"
        marker = "✓" if data["passed"] else "✗"
        print(f"  {metric:<23} {data['score']:>8.3f}  {data['threshold']:>10.2f}  {marker} {status}")
    print("-" * 60)

    all_passed = all(d["passed"] for d in threshold_results.values())
    overall = "ALL PASS" if all_passed else "SOME FAILURES"
    print(f"\n  Overall: {overall}  (elapsed: {elapsed:.1f}s)")

    ci_faith = aggregates.get("faithfulness", 0.0)
    ci_status = "PASS" if ci_faith + EPSILON >= CI_THRESHOLD else "FAIL"
    print(f"\n  CI Gate — faithfulness >= {CI_THRESHOLD}: {ci_faith:.3f} → {ci_status}")
    print("=" * 60)


def save_results(
    collected: list[dict],
    ragas_output: dict,
    threshold_results: dict,
    elapsed: float,
) -> None:
    """Save full results to JSON for portfolio website integration."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "_meta": {
            "deliverable": "D4A",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "helixbot_url": HELIXBOT_URL,
            "elapsed_seconds": elapsed,
            "qa_pairs_evaluated": len(collected),
            "valid_samples": len([
                c for c in collected
                if c.get("answer") and c.get("contexts") and not c.get("error")
                and c.get("category") != "order_support"
            ]),
            "excluded_from_ragas": [
                c["qa_id"] for c in collected
                if c.get("category") == "order_support"
            ],
        },
        "thresholds": THRESHOLDS,
        "ci_threshold": CI_THRESHOLD,
        "aggregates": ragas_output["aggregates"],
        "threshold_results": threshold_results,
        "overall_pass": all(d["passed"] for d in threshold_results.values()),
        "per_sample": ragas_output["per_sample"],
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Results saved to: {RESULTS_FILE}")


async def main() -> None:
    print("HelixBot RAGAS Evaluation — D4A")
    print(f"Target: {HELIXBOT_URL}")
    print(f"QA pairs: {QA_PAIRS_FILE}")
    print()

    # Health check
    async with httpx.AsyncClient() as client:
        try:
            health = await client.get(f"{HELIXBOT_URL}/health", timeout=5.0)
            health.raise_for_status()
            print(f"  HelixBot health: {health.json()['status']}")
        except Exception as exc:
            print(f"  ERROR: HelixBot is not reachable at {HELIXBOT_URL}")
            print(f"  Details: {exc}")
            sys.exit(1)

        # Reset flags first so previous functional/red-team runs do not leak
        # state into RAGAS, then enable grounded evaluation behavior.
        try:
            await client.post(
                f"{HELIXBOT_URL}/api/flags/reset",
                json={},
                timeout=5.0,
            )
            await client.post(
                f"{HELIXBOT_URL}/api/flags",
                json={
                    "flags": {
                        "hallucination_guard": True,
                        "return_verification": True,
                        "rag_poisoning": False,
                        "sanitize_context": True,
                    }
                },
                timeout=5.0,
            )
            print("  Flags reset and set for grounded RAGAS evaluation")
        except Exception as exc:
            print(f"  WARNING: Could not set RAGAS flag state: {exc}")
            print("  Continuing with current flag state.")

    # Load QA pairs
    with open(QA_PAIRS_FILE) as f:
        qa_pairs = json.load(f)
    print(f"  Loaded {len(qa_pairs)} QA pairs")

    # Collect responses
    print("\nStep 1 — Collecting HelixBot responses...")
    start = asyncio.get_event_loop().time()
    collected = await collect_responses(qa_pairs)

    # Run RAGAS
    print("\nStep 2 — Running RAGAS evaluation...")
    ragas_output = run_ragas_evaluation(collected)
    elapsed = asyncio.get_event_loop().time() - start

    # Check thresholds
    threshold_results = check_thresholds(ragas_output["aggregates"])

    # Print report
    print_report(ragas_output["aggregates"], threshold_results, elapsed)

    # Save results
    print("\nStep 3 — Saving results...")
    save_results(collected, ragas_output, threshold_results, elapsed)

    # Exit with failure code if CI faithfulness gate fails
    ci_faith = ragas_output["aggregates"].get("faithfulness", 0.0)
    if ci_faith + EPSILON < CI_THRESHOLD:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
