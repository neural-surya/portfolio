# HelixBot Security / Red-Team Tests

This folder contains D3 security testing for HelixBot.

There are two separate workflows:

1. Manual red-team tests written by hand.
2. Promptfoo-generated red-team tests created from plugin configuration.

Keeping these separate avoids confusion between `tests:` that run directly and `redteam.plugins` that generate tests.

## Prerequisites

Start HelixBot before running security tests:

```bash
cd /Users/suryakanta/Desktop/Switch/capstone
cd helixbot
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The configs target:

```text
http://localhost:8080/api/chat
```

Check the app is reachable:

```bash
curl -s http://localhost:8080/health
```

Reset flags before a run:

```bash
curl -s -X POST http://localhost:8080/api/flags/reset
```

## Files

| File | Purpose |
|---|---|
| `redteam_large.yaml` | Manual hand-written adversarial test suite. Run directly with `promptfoo eval`. |
| `redteam_generate.yaml` | Promptfoo red-team generation config. Does not contain manual tests. |
| `redteam_generated.yaml` | Generated output file, created by `promptfoo redteam run` or `promptfoo redteam generate`. Not committed unless intentionally needed. |
| `results/` | JSON outputs from security runs. |
| `reports/` | Red-team reports and vulnerability notes. |

## Manual Red-Team Tests

Run the manual suite:

```bash
promptfoo eval --config security/redteam_large.yaml \
  --output security/results/latest.json \
  --no-cache
```

This runs only the hand-written `tests:` inside `redteam_large.yaml`.

The manual suite uses `functional/hooks/promptfoo_hooks.js` to reset feature flags before each test and apply each test's `metadata.flags_required` values. Because those flags are shared by the running HelixBot process, `redteam_large.yaml` sets `evaluateOptions.maxConcurrency: 1`.

Some manual tests are expected-fail vulnerability demonstrations, for example prompt injection with `guard_llm=false`.

Run one manual test by metadata ID:

```bash
promptfoo eval --config security/redteam_large.yaml \
  --filter-metadata id=RT-PI-11 \
  --output security/results/latest.json \
  --no-cache
```

Do not add `--filter-providers helixbot-api` for this suite. One manual test, `RT-RAG-05`, intentionally uses the `raw-api` provider to inspect the untransformed JSON response, and provider filtering removes `raw-api` before Promptfoo validates provider references.

## Generated Red-Team Tests

The generation config is:

```text
security/redteam_generate.yaml
```

It asks Promptfoo to generate:

| Plugin | Count |
|---|---:|
| `promptInjection` | 20 |
| `jailbreak` | 20 |
| `systemPromptLeakage` | 20 |
| `piiLeakage` | 20 |
| `hallucination` | 10 |
| `ragPoisoning` | 10 |

Total requested generated tests: 100.

## Generate And Run In One Command

Your installed Promptfoo version supports:

```bash
promptfoo redteam run \
  --config security/redteam_generate.yaml \
  --output security/redteam_generated.yaml \
  --no-cache
```

This does both steps:

1. Generates adversarial test cases from `redteam.plugins`.
2. Evaluates those generated tests against HelixBot.

Use strict mode if generation warnings should fail the run:

```bash
promptfoo redteam run \
  --config security/redteam_generate.yaml \
  --output security/redteam_generated.yaml \
  --strict \
  --no-cache
```

## Generate First, Run Later

If you want to inspect generated tests before running them:

```bash
promptfoo redteam generate \
  --config security/redteam_generate.yaml \
  --output security/redteam_generated.yaml
```

Depending on Promptfoo version, this older form may be needed:

```bash
promptfoo generate redteam \
  --config security/redteam_generate.yaml \
  --output security/redteam_generated.yaml
```

Then run the generated config:

```bash
promptfoo eval --config security/redteam_generated.yaml \
  --output security/results/redteam_generated_results.json \
  --no-cache
```

## Reports

Open the Promptfoo red-team report UI:

```bash
promptfoo redteam report
```

Export a report:

```bash
promptfoo redteam report \
  --output security/reports/redteam_generated_report.json
```

Manual vulnerability write-up:

```text
security/reports/vulnerability_report.md
```

## Important Distinction

This block:

```yaml
redteam:
  plugins:
    - id: promptInjection
      numTests: 20
```

does not make `promptfoo eval --config security/redteam_large.yaml` run 20 prompt-injection tests.

It only tells Promptfoo how many tests to generate when using:

```bash
promptfoo redteam run
```

or:

```bash
promptfoo redteam generate
```

Manual tests under `tests:` are separate and run directly with `promptfoo eval`.

## Useful Commands

Run only manual tests:

```bash
promptfoo eval --config security/redteam_large.yaml \
  --output security/results/latest.json \
  --no-cache
```

Generate and run plugin tests:

```bash
promptfoo redteam run \
  --config security/redteam_generate.yaml \
  --output security/redteam_generated.yaml \
  --no-cache
```

Run generated tests again without regenerating:

```bash
promptfoo eval --config security/redteam_generated.yaml \
  --output security/results/redteam_generated_results.json \
  --no-cache
```

View available red-team commands:

```bash
promptfoo redteam --help
promptfoo redteam run --help
```
