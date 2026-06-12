# Sprint 57.110 Retrospective — B4: subagent child governance + failure policies

**Date**: 2026-06-13 (single-day sprint, Day 0-4)
**Outcome**: SHIPPED — all 4 US + CHANGE-077; drive-through ALL legs PASS; closes harness-deepening proposal §2.5 B4 (the LAST mandatory slice — 10-slice roadmap complete except optional A3); design note 20 §5 deferred pair → RESOLVED.

## Q1 — What was delivered vs planned?

All US-1..US-4 + CHANGE-077. Two in-flight corrections, both dt-driven: (a) leg A's lever moved from tenant escalate phrases to the inherited C3 RiskyActionDetector (stronger — it also PROVES per-tenant C3 governance flows into the child; the phrase lever stayed as leg B's child-failure source); (b) **D-DAY3-1 fix-forward**: +`os.popen`/`os.spawn*`/`os.exec*` to the C3 deny-list after the dt caught a child rewriting its blocked `os.system` call as `os.popen` and EXECUTING it. Tests +19, 0 del (2485 → 2504 expected; 2502+4skip at sweep +2 Day-3). `loop.py` diff = **0 lines** — the slice's core design property held: child governance is pure ctor injection over the existing fail-closed ESCALATE invariant.

## Q2 — Estimate accuracy (calibration)

- Plan §Workload: bottom-up ~10 hr → class-calibrated commit ~5.5 hr (NEW `subagent-child-governance` 0.55, 3-segment). **Agent-delegated: no** (parent-direct; 1 Explore recon agent Day-0 only) → `agent_factor 1.0`.
- Actual ≈ 6-6.5 hr (Day 0 ~1 + Day 1 ~1.5 + Day 2 ~2 + Day 3 ~1.5 incl. the popen fix-forward + re-drive + closeout ~0.75).
- **Ratio ≈ 1.1-1.2 — IN band (upper edge)**. The over-run is again the dt discovery loop (D-DAY3-1 fix + restart + re-drive; D-DAY3-2 terminal-shape investigation + the loop-level pin) — the same shape as 57.109's upper-edge point. The build itself ran ≈0.9.
- **`subagent-child-governance` 0.55 — 1st data point** → KEEP pending 2-3 sprint validation.

## Q3 — What went well?

- **loop.py = 0**: the Day-0 grep that found the fail-closed ESCALATE invariant already in loop.py (:673-680/:1310-1311/:412) turned US-1 from a feared loop change into two closure params. The 57.88-99 pause 基建 paid again, in reverse — its fail-closed fallbacks ARE the child semantics.
- **Day-0 三-prong ROI**: D1 (engine composition is HITL-conditional) shaped the dt; D4 (output-ESCALATE is a child no-op) pre-empted a wrong dt lever; D5 (budget hardcoded; no LLM budget args) killed the timeout-lever plan before Day 1; D7 redirected the threading to `_register_all.py`. ~50 min prevented ≥2 hr.
- **The dt double-caught**: D-DAY3-1 (popen bypass — every gate was green; the detector's completeness test verifies "each pattern has a payload", NOT "each threat has a pattern") and D-DAY3-2 (FATAL terminations are invisible to the FE — `LoopTerminated` isn't on the wire; pre-existing since 57.58). Neither is reachable by paper metrics.
- The C3 inheritance proof came free: the dt's guardrail fire WAS the tenant-composed detector acting inside a child — per-tenant governance → child, no second policy surface.

## Q4 — What to improve / lessons?

- **D-DAY3-1 → deny-list completeness is a threat-model property, not a test-coverage property**: the C3 completeness test pins pattern↔payload bijection but cannot see missing patterns. An adversarial LLM (the child itself!) found the gap in ONE rewrite. Candidate practice: when shipping a deny-list, enumerate the FAMILY (os.system ⇒ popen/spawn*/exec*), not the instance; a periodic red-team dt against the sandbox is the real guard.
- **D-DAY1-1 (mypy deferred analysis)**: a closure capturing a later-assigned local DEFERS mypy's re-analysis of the enclosing function and can surface latent strict-inference looseness on UNTOUCHED lines (`subagent_dispatcher = ... / else None` → new error at :433). Fix = explicit Optional annotation. Watch (1st pt).
- **D-DAY3-2 → `AD-LoopTerminated-Wire-Surface`**: a FATAL-terminated run looks like a silent stream end + a stuck "pending" tool chip in chat-v2. Surfacing `loop_terminated` (reason + detail) to the wire/FE is a scoped slice; it also covers the 57.58 rate-limit shape.
- dt recipe note: tenant escalate phrases govern the PARENT's input gate too — any dt phrase must be kept out of the user input (split-word prompting worked first try).

## Q5 — Anti-pattern audit

AP-1..AP-11: 0 violations. AP-4 note: this slice REMOVED a structural Potemkin risk (children that LOOKED governed because the parent was); the dt then immediately exercised the new surface. AP-6: failure_policy has three live semantics + a live tenant lever; no speculative fields (the per-tenant kill switch was deliberately NOT built — the 鐵律). AP-2: every new path is main-flow (handler → executor → dispatcher → fork/teammate) and integration-tested.

## Q6 — Drive-through verdict

PASS (real UI :3007 + clean no-reload backend, sole-owner verified + real Azure gpt-5.2; zero dev-login). Evidence: Tree child row `guardrail escalate · risky_action…` (screenshot) · child `subprocess` blocked → popen bypass caught → fix → re-drive shows the child honestly giving up + whoami NOT executed (screenshot) · fail_fast: PUT 200 + invalid-422 live → child input-block (0 tok) → run terminated (no answer turn; no completion audit row) → flip-back all-None verified. Honest carve-outs: FATAL termination is invisible on the wire (D-DAY3-2 carryover); the C3 tab has no failure-policy field yet (admin sets it via the API).

## Q7 — Carryover / next

- NEW: `AD-LoopTerminated-Wire-Surface` (FATAL run-termination FE surface) · `AD-Subagent-AsTool-FailFast` (D-DAY2-1 — `as_tool_factory` is an ABC method) · `AD-HarnessPolicy-Tab-FailurePolicy-Field` (small C3-tab FE field) · deny-list red-team practice (Q4, process).
- Plan-deferred unchanged: `AD-Subagent-Child-Verification` (Cat 10 in the child) · depth>1 · child escalate-propagation-to-parent-pause (§2.5 pair).
- **Harness-deepening 10-slice roadmap: B4 was the last mandatory slice — 9.5+0.5/10 done; only optional A3 (trace-aware critique) remains.** Next direction = user's call (A3, or back to the carryover pool / next-phase-candidates).

## Design Note Extract（spike sprint only）

NOT required — feature continuation of design note 20 (§5.5 NOT-apply); note 20 §5 deferred pair marked RESOLVED + MHist instead.
