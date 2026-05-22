# HelixBot LLM Testing Portfolio

HelixBot is a retail AI assistant used as the system under test for LLM quality, safety, red-team, and RAG evaluation. This portfolio repo is designed so reviewers can run the app through a public Docker image, then execute the test suites from the repository.

The HelixBot application source is not required in this repo. The root `docker-compose.yml` pulls the published image:

```text
suryakanta87/helixbot:latest
```

## Repository Layout

```text
portfolio/
├── docker-compose.yml                 # Runs HelixBot from public Docker image
├── .env.example                       # Runtime config template
├── requirements.txt                   # Python test/evaluation dependencies
├── functional/                        # PromptFoo functional suites
│   ├── promptfoo.yaml
│   ├── promptfoo_parametrized.yaml
│   ├── promptfoo_raw.yaml
│   ├── promptfoo_bias.yaml
│   ├── promptfoo_bias_parity.yaml
│   ├── promptfoo_stability.yaml
│   ├── promptfoo_nondeterminism.yaml
│   ├── hooks/
│   ├── data/
│   └── results/
├── security/                          # Manual and generated red-team assets
│   ├── redteam_large.yaml
│   ├── redteam_generate.yaml
│   ├── redteam_generated.yaml
│   ├── reports/
│   └── results/
├── evaluation/                        # RAGAS evaluation only
│   ├── test_ragas_eval.py
│   ├── qa_pairs.json
│   ├── README.md
│   └── results/
├── strategy/                          # Test strategy document
└── .github/workflows/
    └── capstone-pipeline.yml          # CI quality gates
```

Note: the `evaluation/` folder in this portfolio only contains `test_ragas_eval.py`. There are no `test_function_calling.py`, `test_performance.py`, or `test_resilience.py` evaluation scripts in this repo.

## Prerequisites

Install or verify:

| Requirement | Check |
| --- | --- |
| Docker Desktop | `docker info` |
| Python 3.11+ | `python3 --version` |
| PromptFoo CLI | `promptfoo --version` |
| OpenAI API key | needed in `.env` |

Install local test dependencies:

```bash
pip install -r requirements.txt
npm install -g promptfoo
```

## Start HelixBot

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and set:

```env
OPENAI_API_KEY=your_real_key
```

Then start the server:

```bash
docker compose up -d
```

The compose file pulls and runs:

```text
suryakanta87/helixbot:latest
```

Verify health:

```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```

Expected:

```json
{
  "status": "ok",
  "rag_status": "ready"
}
```

Stop the server:

```bash
docker compose down
```

## Functional Tests

Run the main PromptFoo functional suite:

```bash
promptfoo eval \
  --config functional/promptfoo.yaml \
  --filter-providers helixbot-api \
  --output functional/results/latest.json \
  --no-cache
```

Run the parametrized CSV-backed suite:

```bash
promptfoo eval \
  --config functional/promptfoo_parametrized.yaml \
  --filter-providers helixbot-api \
  --output functional/results/promptfoo_parametrized_results.json \
  --no-cache
```

Run the raw API schema suite:

```bash
promptfoo eval \
  --config functional/promptfoo_raw.yaml \
  --filter-providers raw-api \
  --output functional/results/raw_latest.json \
  --no-cache
```

Run all functional suites used by CI:

```bash
promptfoo eval --config functional/promptfoo.yaml --filter-providers helixbot-api --output functional/results/latest.json --no-cache
promptfoo eval --config functional/promptfoo_parametrized.yaml --filter-providers helixbot-api --output functional/results/promptfoo_parametrized_results.json --no-cache
promptfoo eval --config functional/promptfoo_raw.yaml --filter-providers raw-api --output functional/results/raw_latest.json --no-cache
promptfoo eval --config functional/promptfoo_bias.yaml --filter-providers helixbot-api --output functional/results/bias_results.json --no-cache
promptfoo eval --config functional/promptfoo_bias_parity.yaml --repeat 5 --filter-providers helixbot-api --output functional/results/bias_parity_results.json --no-cache
promptfoo eval --config functional/promptfoo_stability.yaml --repeat 2 --filter-providers helixbot-api --output functional/results/stability_latest.json --no-cache
promptfoo eval --config functional/promptfoo_nondeterminism.yaml --repeat 5 --filter-providers helixbot-api --output functional/results/nondeterminism_results.json --no-cache
```

PromptFoo results are written under:

```text
functional/results/
```

## RAGAS Evaluation

This portfolio includes only the RAGAS evaluation script:

```text
evaluation/test_ragas_eval.py
```

Run it from the repository root:

```bash
python evaluation/test_ragas_eval.py
```

The script:

1. Loads QA pairs from `evaluation/qa_pairs.json`.
2. Queries HelixBot at `http://localhost:8080/api/chat`.
3. Collects answers and retrieved contexts.
4. Runs RAGAS metrics: `faithfulness`, `answer_relevancy`, `context_precision`, and `context_recall`.
5. Saves results to `evaluation/results/ragas_scores.json`.

The CI gate uses:

```text
faithfulness >= 0.75
```

For detailed RAGAS notes, see:

```text
evaluation/README.md
```

## Security / Red Team

Run the manual red-team suite:

```bash
promptfoo eval \
  --config security/redteam_large.yaml \
  --filter-providers helixbot-api \
  --output security/results/latest.json \
  --no-cache
```

Generated red-team assets are also included:

```text
security/redteam_generate.yaml
security/redteam_generated.yaml
```

For details, see:

```text
security/README.md
security/reports/vulnerability_report_findings.md
```

## CI Pipeline

GitHub Actions uses:

```text
.github/workflows/capstone-pipeline.yml
```

Behavior:

| Trigger | Suite |
| --- | --- |
| Push | Smoke suite |
| Manual `workflow_dispatch` | Full suite by default, smoke optional |

Blocking gates:

| Gate | Threshold |
| --- | --- |
| Health check | `/health` returns OK and RAG ready |
| Safety pass rate | `>= 90%` |
| PromptFoo pass rate | `>= 80%` |
| RAGAS faithfulness | `>= 0.75` |

If any gate breaches its threshold, the workflow exits with code `1` and fails the build.

Required GitHub secret:

```text
OPENAI_API_KEY
```

Optional GitHub repo variable:

```text
HELIXBOT_IMAGE=docker.io/suryakanta87/helixbot:latest
```

## Troubleshooting

If Docker cannot pull the image:

```bash
docker pull suryakanta87/helixbot:latest
```

If the server is not healthy:

```bash
docker logs helixbot
```

If PromptFoo cannot reach the app, confirm:

```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```

If RAGAS fails due to dependencies:

```bash
pip install -r requirements.txt
```

If a previous run left old state behind:

```bash
docker compose down
docker compose up -d
```
