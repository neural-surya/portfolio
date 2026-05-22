# Capstone Project Scope — Track 2A: LLM Testing Essentials

**Student:** Suryakanta  
**Cohort Date:** May 2026  
**Track:** 2A — LLM Testing Essentials (Sessions 1–10)  
**Time Budget:** 1 week (~18–22 hours)  
**Capstone Target:** HelixBot — Helix Store Assistant public Docker image (`docker.io/suryakanta87/helixbot:latest`)

---

## 1. Scope Philosophy

The capstone is not a demonstration of everything you built across 9 sessions. It is a single, coherent test engagement — from strategy to CI/CD — executed against one real target application. Quality over coverage. Think of it as something you would hand to a hiring manager.

**Realistic student time in 1 week:**
- Weeknights (Mon–Fri): ~2 hours/night = 10 hours
- Weekend: ~8–10 hours
- Total: ~18–22 hours

---

## 2. What Changed from the Original Curriculum Scope

The curriculum's original 7-deliverable scope was well-calibrated for 1 week. The only meaningful addition is one evaluation component (RAGAS or function calling contracts) — because that is now a market expectation that was not in the original curriculum scope.

Everything else beyond the original scope belongs in your session exercises, not the capstone.

**Dropped from the earlier "enhanced" scope:**
- PyRIT and Garak — too much environment setup for a 1-week window
- Multi-agent, memory, and context window testing — valuable skills, wrong place
- Performance and resilience testing — session 9 work, not capstone scope
- Drift detection and observability dashboard — post-launch concern, not pre-launch testing
- Composite scorecard — implied by the evaluation deliverable
- Cost governance report — session 3 work, not a capstone blocker

---

## 3. Capstone Deliverables (6 Core Deliverables)

| # | Deliverable | Time |
|---|-------------|------|
| 1 | Test strategy document (1–2 pages) | 2h |
| 2 | PromptFoo test suite (20+ cases, 2 providers) | 4h |
| 3 | Red team report — PromptFoo only, OWASP mapped | 4h |
| 4 | Evaluation: RAGAS eval OR function calling contracts (pick one) | 3h |
| 5 | GitHub Actions pipeline (3–4 quality gates) | 2h |
| 6 | Bug report portfolio — minimum 4 high-signal bugs + stakeholder summary | 3.5h |
| | **Total** | **~18.5h** |

---

## 4. Deliverable Details

---

### Deliverable 1 — Test Strategy Document

**What to produce:** A 1–2 page document covering the target application, risk areas, testing approach, and what success looks like.

**Must include:**
- What the application does and how it works (architecture summary)
- The 3 highest-risk areas and why
- Which testing techniques address which risks
- Acceptance criteria: what passing looks like

---

### Deliverable 2 — PromptFoo Test Suite

**What to produce:** A single YAML file with 20+ test cases targeting the capstone application across 2 providers.

**Must include:**
- Minimum 2 providers (e.g., OpenAI gpt-4o-mini + Anthropic Claude Haiku)
- Mix of assertions: at least 4 deterministic types (contains, not-contains, regex, json-schema) and at least 5 model-graded (llm-rubric)
- Test cases covering at least 5 of the 7 challenges: hallucination, prompt injection, context limits, bias, non-determinism
- Non-determinism: use the `high_temperature` feature flag (ON = temp 0.8, OFF = temp 0.2) to run the same query 5× and measure response variance
- Bias: use the `bias_mitigation` flag (ON = fairness instruction active, OFF = raw LLM) and parameterise the same query with different demographic descriptors via CSV
- CSV-based test data file for parameterised inputs

---

### Deliverable 3 — Red Team Report

**What to produce:** A PromptFoo red team run (Large configuration) against the capstone application. A written report mapping every finding to OWASP LLM Top 10.

**Must include:**
- Large config: minimum 100 adversarial tests
- At minimum these plugins: promptInjection, jailbreak, systemPromptLeakage, piiLeakage, hallucination, ragPoisoning
- For ragPoisoning: enable the `rag_poisoning` feature flag (`POST /api/flags {"flags":{"rag_poisoning":true}}`) before the red team run — this injects misleading documents into ChromaDB retrieval so the plugin has a real attack surface to probe (OWASP LLM09 — Supply Chain)
- Findings table: vulnerability name, OWASP ID, severity (Critical/High/Medium/Low), reproduction step, remediation suggestion
- Clear label: "security-aware observations" not a full penetration test

**Tool:** PromptFoo red team only. Do not attempt PyRIT or Garak in the capstone — environment setup cost is too high for the time budget.

---

### Deliverable 4 — Evaluation (Pick One)

Pick whichever fits your target application better. Do not do both.

**Option A — RAGAS Evaluation (if target app has a RAG component):**
- Run RAGAS on minimum 10 QA pairs
- Report scores for: Faithfulness, Answer Relevancy, Context Precision, Context Recall
- State whether each score passes or fails against the threshold
- Thresholds: Faithfulness ≥ 0.85 | Answer Relevancy ≥ 0.80 | Context Precision ≥ 0.75 | Context Recall ≥ 0.75
- One-paragraph deployment recommendation based on scores

**Option B — Function Calling Contract Tests (if target app uses tool calling):**
- Pydantic schema for each tool the LLM calls
- Test cases covering: valid call, missing required field, wrong type, injection attempt
- Validate against the OpenAPI spec if one exists
- Pass/fail summary with failure root cause for each failure

---

### Deliverable 5 — GitHub Actions Pipeline

**What to produce:** A single GitHub Actions workflow that runs on every push and enforces 3–4 quality gates.

**Gates to enforce (pick 3–4 that match your target app):**

| Gate | Threshold | Blocks Build? |
|------|-----------|---------------|
| Safety pass rate | ≥ 95% | Yes |
| RAGAS Faithfulness (if Option A) | ≥ 0.75 | Yes |
| Contract test pass rate (if Option B) | 100% | Yes |
| PromptFoo pass rate | ≥ 80% | Yes |

**Keep it simple:** One workflow file. Smoke tests on push, full suite manually. Do not try to merge all 8 session workflows into one — start clean.

---

### Deliverable 6 — Bug Report Portfolio + Stakeholder Summary

**What to produce:** Minimum 4 high-signal bug reports from exploratory testing, plus a half-page plain-English summary written for a non-technical reader (product manager, team lead, or executive).

**Each bug report must include:**
- Bug title (clear, specific)
- AI vulnerability category (hallucination / prompt injection / context loss / bias / guard bypass / tool failure / output formatting / knowledge base poisoning)
- Severity: P0–P4 with clear impact and likelihood rationale
- Steps to reproduce (exact prompts used)
- Actual vs expected output
- Reproduction rate (e.g., "4 of 5 attempts")
- OWASP LLM mapping where applicable

**Target distribution across severity:**
- At least 1 P1 or P2 finding
- Clear severity rationale for every submitted bug
- Exclude findings that are not reproducible in the current build unless they are explicitly labeled historical or mitigated

**Stakeholder summary must include (half a page, plain English):**
- One sentence on what the application was tested for
- Top 3 findings in plain language — no jargon, no OWASP codes
- A clear ship / don't ship / ship with conditions recommendation
- One sentence on what would need to be fixed before the next test cycle

This is the artifact you hand to a product manager. It answers the most common interview question in AI QA: *"How do you communicate test findings to a non-technical stakeholder?"*

**Reproducibility tip:** HelixBot ships with feature flags (`GET /api/flags`, `POST /api/flags`). Toggle the relevant flag ON or OFF to make every bug deterministically reproducible. Include the flag state in your "steps to reproduce" section. Reset between runs with `POST /api/flags/reset`.

---

---

## 5. Repository Structure

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
├── bugs/                              # Bug portfolio and stakeholder summary
│   ├── bug_001.md
│   ├── bug_002.md
│   ├── bug_003.md
│   ├── bug_005.md
│   ├── index.json
│   └── stakeholder_summary.md
├── evaluation/                        # RAGAS evaluation only
│   ├── test_ragas_eval.py
│   ├── qa_pairs.json
│   ├── README.md
│   └── results/
├── strategy/                          # Test strategy document
├── manifest.json                      # Portfolio metadata
├── capstone.html                      # Static portfolio page
└── .github/workflows/
    └── capstone-pipeline.yml          # CI quality gates
```

---

## 6. Suggested Day-by-Day Plan

| Day | Focus | Hours |
|-----|-------|-------|
| Day 1 (Mon) | Set up repo, explore target app, write test strategy | 2h |
| Day 2 (Tue) | Build PromptFoo YAML suite (first 15 cases) | 2h |
| Day 3 (Wed) | Complete PromptFoo suite, run red team | 2h |
| Day 4 (Thu) | Run evaluation (RAGAS or contracts), start bug reports | 2h |
| Day 5 (Fri) | Complete bug reports, set up CI/CD pipeline | 2h |
| Day 6 (Sat) | Polish all reports, fix gaps, run everything end to end | 5h |
| Day 7 (Sun) | Final README, clean artifacts, push to GitHub | 3h |
| **Total** | | **~18h** |

---

## 7. What This Capstone Proves

| Skill | Where it Shows |
|-------|----------------|
| Test strategy authoring | Deliverable 1 |
| PromptFoo fluency | Deliverable 2 |
| Adversarial / red team thinking | Deliverable 3 |
| Evaluation with real metrics | Deliverable 4 |
| CI/CD integration | Deliverable 5 |
| Bug classification and reporting | Deliverable 6 |
| Communication of findings | Deliverable 6 |

This covers the full test lifecycle — strategy → functional → adversarial → evaluation → automation → reporting — which is exactly what AI QA roles require.
