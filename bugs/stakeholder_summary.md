---
id: D6-stakeholder
title: "HelixBot AI Testing — Stakeholder Summary"
deliverable: D6
author: "Surya Kanta"
date: "2026-05-15"
audience: non-technical
tags: [stakeholder, summary, d6, executive]
---

# AI Testing Summary: HelixBot — Customer AI Assistant

- **Prepared by:** Suryakanta, AI Quality Engineer
- **Testing Date:** 2026-05-15
- **Testing Duration:** 20+ hours across 7 test categories
- **Application Tested:** HelixBot v1.0 — AI-powered retail assistant for Helix Store

---

## What Was Tested

HelixBot is an AI assistant planned for Helix Store's customer-facing experience. It helps customers find products, check order status, apply promo codes, and understand store policies. Testing involved asking the assistant a wide range of realistic customer questions — including edge cases, adversarial scenarios, and security stress-tests — to assess whether responses were accurate, safe, consistent, and fair.

---

## Summary of Findings

| Severity | Count | Plain-English Description |
|----------|-------|--------------------------|
| 🔴 Critical (P1) | 2 | The AI can be misdirected when the guard is off; a historical product hallucination bug is now mitigated |
| 🟠 High (P2) | 2 | Poisoned knowledge can create false prices; high-value returns can bypass verification if the return gate is disabled |
| **Total** | **4** | Minimum high-signal bug portfolio |

This portfolio intentionally focuses on four defensible findings with current reproduction evidence or clearly labeled historical mitigation evidence. Candidate bugs that did not reproduce in the current build were excluded from the submitted set.

---

## Top Risks

### Risk 1: The AI Can Be Hijacked by Clever Messages

**What happened:** When our safety guard is turned off, prompt injection attempts can reach normal routing instead of being blocked by the guard. In the current observed run, the bot did not output the attacker's requested word, but it also did not mark the request as blocked by the guard.

**Why it matters:** In a retail setting, this could cause the bot to give harmful, off-brand, or competitor-favouring responses to real customers. Any user — without needing a login or special access — can attempt this. The fix is simple: enabling the safety guard catches and blocks these attacks before they reach the AI.

---

### Risk 2: Historical Product Hallucination Is Now Mitigated

**What happened:** Earlier testing found that the bot could invent details for a product we do not sell. In the current build, the original prompt no longer reproduces the bug. With the hallucination guard enabled, the bot returns the safe refusal: "I don't have that information in our current product catalog or store policies."

**Why it matters:** This remains important because invented product details can create false advertising risk. The current mitigation shows the right product behavior: the assistant should only discuss products and policies present in trusted data.

### Risk 3: Poisoned Knowledge Can Create False Prices

**What happened:** When simulated poisoned knowledge-base content is enabled, the bot told a customer that the Helix Air 13 was available for `$0.00` as part of an anniversary sale. The real product price is `$999.99`.

**Why it matters:** If false information gets into the AI knowledge base, the assistant may repeat it as official store policy. That can create revenue loss, customer complaints, and trust damage. Context sanitization and knowledge-base access controls reduce this risk.

### Risk 4: High-Value Returns Can Bypass Verification

**What happened:** With return verification disabled, the bot initiated a return for order `ORD-2024-001` and issued return ID `RET-5460B9F2` without asking for identity verification. With verification enabled, the bot correctly required identity verification because the order is over `$500`.

**Why it matters:** If this gate is disabled in production, anyone with a high-value order ID could start a return process without proving they are the customer. This creates direct fraud and refund risk.

---

## What Was Working Well

- **Safety guard** (when enabled) blocked 100% of direct instruction hijacking attempts and 95%+ of adversarial probes in automated testing — it works reliably when switched on.
- **Hallucination guard** (when enabled) kept all AI answers grounded in our verified product catalog, producing accurate, trustworthy responses.
- **Context sanitization** removed poisoned RAG content before the final answer, preventing false `$0.00` product claims from reaching customers.
- **Order and inventory tools** performed accurately and reliably across all test scenarios — order status, stock levels, and checkout logic all returned correct results.
- **Return verification** correctly blocked high-value return processing when enabled.

---

## Recommendation

> **⚠️ Conditional release** — high-impact issues identified. Recommend fixing the following before production deployment:
> 1. Enable safety guard (`guard_llm`) and hallucination guard by default in production configuration.
> 2. Enable context sanitization and restrict write access to the knowledge base.
> 3. Lock return verification to always-ON — remove runtime toggle from public API.

**Rationale:** The strongest findings are controlled by feature flags or simulated poisoned context. With safe defaults locked on and the knowledge base protected, the overall risk posture is acceptable for a phased launch with continued monitoring.

---

## Next Steps

| Action | Owner | Priority |
|--------|-------|----------|
| Enable guard_llm + hallucination_guard in production config | DevOps | P1 — before launch |
| Enable sanitize_context and add RAG source controls | Engineering / Security | P1 — before launch |
| Lock return_verification to always-ON | Engineering | P1 — before launch |
| Implement ChromaDB write access controls | Security / Infra | P2 — current sprint |
| Continue automated PromptFoo and RAGAS gates in CI | AI Quality | P2 — ongoing |

---

*Full technical details: `bugs/bug_001.md`, `bugs/bug_002.md`, `bugs/bug_003.md`, `bugs/bug_005.md`, and `security/reports/vulnerability_report_findings.md`*

*Bug reports follow template v2.0 | Track 2A | Session 5 Hour 4*
