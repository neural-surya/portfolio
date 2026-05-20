# HelixBot Functional Promptfoo Tests

This folder contains the Promptfoo functional evaluation suites for HelixBot.

## Prerequisites

Start HelixBot before running tests:

```bash
cd /Users/suryakanta/Desktop/Switch/capstone
cd helixbot
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The tests assume the API is available at:

```text
http://localhost:8080/api/chat
```

Check the app is reachable:

```bash
curl -s http://localhost:8080/health
```

## Files

| File | Purpose |
|---|---|
| `promptfoo_parametrized.yaml` | Main CSV-backed functional suite. Prefer this for normal runs. |
| `data/promptfoo_parametrized.csv` | Test data, prompts, assertions, and metadata for the parametrized suite. |
| `promptfoo.yaml` | Inline YAML version of the main suite. Useful for readability and editing complex cases. |
| `promptfoo_raw.yaml` | Raw API schema test for the full `ChatResponse` JSON envelope. |
| `promptfoo_bias.yaml` | Bias bug reproduction suite with `bias_mitigation=false`. |
| `promptfoo_bias_parity.yaml` | Bias mitigation/parity matrix with `bias_mitigation=true`. |
| `promptfoo_stability.yaml` | Low-temperature repeat stability suite. |
| `promptfoo_nondeterminism.yaml` | High-temperature non-determinism suite. |
| `hooks/promptfoo_hooks.js` | Shared Promptfoo lifecycle hook that resets feature flags before each test and applies `metadata.flags_required`. |
| `results/` | JSON outputs from previous runs. |

## Recommended Full Run

Run suites separately because some require different flags, providers, and repeat counts.

### Main Parametrized Suite

```bash
promptfoo eval --config functional/promptfoo_parametrized.yaml \
  --filter-providers helixbot-api \
  --output functional/results/promptfoo_parametrized_results.json \
  --no-cache
```

Note: `D2-TC20` is expected to fail because it demonstrates RAG poisoning. `D2-TC20M` is the mitigation test and should pass when the app has the `sanitize_context` flag code.

### Raw API Schema

```bash
promptfoo eval --config functional/promptfoo_raw.yaml \
  --filter-providers raw-api \
  --output functional/results/raw_latest.json \
  --no-cache
```

### Bias Bug Reproduction

```bash
promptfoo eval --config functional/promptfoo_bias.yaml \
  --filter-providers helixbot-api \
  --output functional/results/bias_results.json \
  --no-cache
```

### Bias Parity / Mitigation

Use repeat runs for stronger parity evidence:

```bash
promptfoo eval --config functional/promptfoo_bias_parity.yaml \
  --repeat 5 \
  --filter-providers helixbot-api \
  --output functional/results/bias_parity_results.json \
  --no-cache
```

For quick debugging, use `--repeat 1` or omit `--repeat`.

### Low-Temperature Stability

```bash
promptfoo eval --config functional/promptfoo_stability.yaml \
  --repeat 2 \
  --filter-providers helixbot-api \
  --output functional/results/stability_latest.json \
  --no-cache
```

### High-Temperature Non-Determinism

```bash
promptfoo eval --config functional/promptfoo_nondeterminism.yaml \
  --repeat 5 \
  --filter-providers helixbot-api \
  --output functional/results/nondeterminism_results.json \
  --no-cache
```

## Run One Test

Run a single test by metadata id:

```bash
promptfoo eval --config functional/promptfoo_parametrized.yaml \
  --filter-metadata id=D2-TC06 \
  --filter-providers helixbot-api \
  --output functional/results/promptfoo_parametrized_results.json \
  --no-cache
```

Run the context-limits test:

```bash
promptfoo eval --config functional/promptfoo_parametrized.yaml \
  --filter-metadata id=D2-TC26 \
  --filter-providers helixbot-api \
  --output functional/results/promptfoo_parametrized_results.json \
  --no-cache
```

## Coverage

| Challenge | Coverage |
|---|---|
| Hallucination | `D2-TC03`, `D2-TC18`, `D2-TC19`, `D2-TC20`, `D2-TC20M` |
| Prompt injection / jailbreak | `D2-TC14`, `D2-TC15` |
| Context limits / context handling | `D2-TC20`, `D2-TC20M`, `D2-TC26`, raw `contexts` schema in `D2-TC04` |
| Bias | `D2-TC21`-`D2-TC23`, plus `promptfoo_bias_parity.yaml` |
| Non-determinism | `D2-TC24`, `D2-TC25`, `D2-TC25B` |

Additional areas covered:

| Area | Tests |
|---|---|
| Product inquiry / RAG grounding | `D2-TC01`-`D2-TC03` |
| Order support / tool use | `D2-TC05`-`D2-TC07` |
| FAQ / policy grounding | `D2-TC08`-`D2-TC10` |
| Promo code business logic | `D2-TC11`-`D2-TC13` |
| PII protection | `D2-TC16` |
| API schema integrity | `D2-TC04` |

## Feature Flags

Tests do not require manual flag setup. The shared hook reads each test's `metadata.flags_required`, resets flags before each test, and applies the required values.

Example:

```yaml
metadata:
  flags_required:
    rag_poisoning: true
    sanitize_context: true
```

Hook location:

```text
functional/hooks/promptfoo_hooks.js
```

All configs reference it as:

```yaml
extensions:
  - file://hooks/promptfoo_hooks.js:resetFlagsBeforeEach
```

## Expected Failure

`D2-TC20` is intentionally an expected failure:

```text
rag_poisoning=true
```

It demonstrates that a poisoned RAG chunk can make HelixBot claim the Helix Pro 15 is free. The mitigation test is:

```text
D2-TC20M
```

That test uses:

```text
rag_poisoning=true
sanitize_context=true
```

and should pass.

## Common Troubleshooting

If Promptfoo cannot access its log/database files, rerun normally from your terminal rather than a restricted sandbox.

If the API is not reachable:

```bash
curl -s http://localhost:8080/api/flags
```

If a new flag is not recognized, restart HelixBot. Python code changes are not picked up by a running server unless it was started with reload.

If Docker fails to pull `python:3.11-slim` with a Docker Hub DNS error, that is a Docker/network issue, not a Promptfoo config issue.

## Notes

- `--filter-metadata id=D2-TC01` is the most reliable way to run one test.
- `--filter-pattern` matches prompt/description text, not necessarily the metadata id.
- In `zsh`, quote patterns with brackets if you use regex-like filters.
- The parametrized suite is easier to run and maintain for table-like tests. The inline YAML suite is easier to read for complex rubrics.
