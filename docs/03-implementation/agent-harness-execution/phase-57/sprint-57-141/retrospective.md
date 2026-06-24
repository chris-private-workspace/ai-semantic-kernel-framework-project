# Sprint 57.141 Retrospective — pass^k reliability eval harness (research #2)

**Sprint**: 57.141 · **Dates**: 2026-06-24 → 25 · **Branch**: `feature/sprint-57-141-passk-reliability-harness` (from `main` `196d8892`)
**Closes**: `AD-Eval-PassK-Reliability-Harness` (research #2)

---

## Q1 — What was delivered?

V2's first `pass^k` reliability eval harness — a pure-offline `scripts/benchmark_pass_k.py` (mirrors `benchmark_judge.py`) measuring 4 axes (pass^k vs pass@1 · behavioral consistency · λ fault-injection · ε perturbation) with a hybrid oracle (rules + LLM judge), over a 12-case difficulty-graded corpus, plus 17 CI-safe unit tests. **3 NEW files, ZERO src edit.** Drive-through verdict obtained on real Azure (90 runs). CHANGE-108 + design note 45.

## Q2 — Estimate accuracy

- Plan §7: bottom-up ~11 hr → class-calibrated commit **~6.5 hr** (mult 0.60).
- Actual ≈ **~6.5 hr-equivalent** of scoped work (eval ~1 + plan/checklist/Day-0 ~1.5 + harness/corpus/tests incl. iteration ~2.5 + drive-through ~0.5 + closeout ~1). Ratio **≈ 1.0 — IN band**.
- The 4-axis breadth (the flagged upper-edge risk) did NOT over-run: the harness was a single cohesive file (4 axes share `run_case`/`build_report`), and the grounding (5 benchmark precedents + a working `AgentLoopImpl` driver test) was unusually complete, so there was near-zero blind-write risk.

## Q3 — What went well?

- **Evidence-first paid off**: the spike MEASURED the research's pass^k≠pass@1 claim on V2's own loop instead of importing the (🔴 weak-citation) external numbers. Result is honest in BOTH directions — no divergence on this corpus + 2 real pass@1-invisible signals (answer-consistency 75%, λ 50%).
- **Day-0 三-prong fully de-risked the build**: the key scope risk (D-loop-run-noDB) resolved GREEN (loop is DB-less drivable) → the harness needed no DB/migration/session; rules-oracle simplification SHRANK scope. The `test_loop_retry_integration.py` file gave a complete `AgentLoopImpl`-driver + `ChatClient`-subclass template → the harness imported + ran first try (only a self-inflicted test bug to fix).
- **Smoke-before-spend**: a k=1 (~14 call) smoke proved real-Azure wiring before the 90-run full spend — caught nothing, but the right discipline for a cost-incurring drive-through.
- **Zero src blast radius**: full pytest 2859+5skip with the only "fail" a pre-existing isolation flake (passes in isolation).

## Q4 — Calibration outcome

- NEW scope class **`passk-reliability-spike` 0.60**, 1st data point, ratio ≈ 1.0 → **IN band, KEEP**. Anchored to `verification-trace-and-benchmark-spike` 0.60 (57.111) + the #136-139 measurement-harness spikes (all 0.60) — same Cat-12/10 greenfield-benchmark-script + golden-fixture shape. The 57.137 lesson held: a >~3 hr real implementation core (4-axis computation + fault wrapper + corpus + 17 CI tests) holds the spike multiplier — this was NOT a tiny-code full-ceremony sprint needing the 0.85 re-point.
- **Agent-delegated: no** (parent-direct; harness design + λ injection-point decision + verdict interpretation are judgment-dense). `agent_factor` 1.0.
- If a 2nd `passk-reliability-spike` lands > 1.20, re-point toward 0.75 (the 4-axis breadth is the variance risk).

## Q5 — Anti-pattern self-check

- **AP-2** (side-track) ✅ — a permanent, CI-exercised eval tool (via the unit test); not dead code; follows the 5 existing `benchmark_*.py`.
- **AP-3** (cross-dir scatter) ✅ — single harness file in `scripts/`, fixture in `tests/fixtures/observability/`, test in `tests/unit/scripts/`.
- **AP-4** (Potemkin) ✅ — all verdict numbers from real Azure; rules oracle deterministic (zero judge noise on 10/12); corpus has a real difficulty gradient; "100% pass^k" is honest (gpt-5.2 IS reliable here), not a rigged oracle.
- **AP-6** (speculative abstraction) ✅ — no new ABC; WRAPS existing `ChatClient`/`Verifier`; λ/ε deferred-extension points are documented, not pre-built; tool_use deferred not stubbed.
- **AP-8** (no central PromptBuilder) N/A — eval harness, not a chat path; the loop it drives uses the real PromptBuilder.
- **AP-11** (version suffixes) ✅ — no `_v2`/`_old`; names reflect behavior.
- v2 lint tests: **21 pass** (incl. llm_sdk_leak — `_FaultInjectingChatClient` neutrality).

## Q6 — What to improve / lessons

- **Corpus difficulty is the divergence lever, not the harness.** A reasoning-only corpus at k=3 won't reproduce τ-bench's pass^8<25% — that regime is tool-heavy multi-turn agentic. The harness is sound; the FIRST corpus should have included ≥1 genuinely hard multi-step/tool case to give divergence a chance (deferred to `AD-Eval-PassK-Harder-Corpus`). Lesson: for a "measure X" spike, design the corpus to give X a chance to be non-trivial, while staying honest (don't rig it).
- **Stale-doc drift**: CLAUDE.md + `sprint-workflow.md` reference `python scripts/lint/run_all.py` which doesn't exist — the v2 lints are pytest tests under `tests/unit/scripts/lint/`. Logged as a carryover (not this sprint's fix).
- **Self-inflicted test bug**: `random.Random(42).random()` re-seeded each list-comprehension iteration (always same value) — a reminder that even test reference data needs a single generator. Caught + fixed in one cycle.

## Q7 — Carryover / next

- **research #2 CLOSED** → next canonical = **#5 `AD-Observability-OTel-GenAI-Schema`** (or #7 tool-desc lint; both net-new, loop.py-independent).
- 3 NEW follow-on candidates (→ `next-phase-candidates.md`): `AD-Eval-PassK-Harder-Corpus-Phase58` · `AD-Loop-ChatLevel-Retry-Phase58` (λ axis showed no chat retry) · `AD-Eval-Answer-Consistency-Surface-Phase58`.
- Stale-doc carryover: `AD-Lint-RunAll-Stale-Path` (the `run_all.py` reference).
- Pre-existing (not surfaced here, unchanged): `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C).
