# Design Note 45 — pass^k Reliability Eval Harness (research #2)

**Purpose**: Extract the verified design of V2's first `pass^k` reliability eval harness from the Sprint 57.141 thin-spike implementation.
**Category / Scope**: 範疇 12 (Observability / Evaluation) / Phase 57 / Sprint 57.141
**Created**: 2026-06-25
**Last Modified**: 2026-06-25
**Status**: Active (spike-extracted; verified ratio ≥ 95%)

> **Modification History**
> - 2026-06-25: Initial extract from Sprint 57.141 implementation (CHANGE-108)

---

## 1. Spike Summary

Closes `AD-Eval-PassK-Reliability-Harness` (research #2). Ships a pure-offline measurement harness `backend/scripts/benchmark_pass_k.py` that runs the SAME corpus input through V2's own agent loop **k times** and computes 4 reliability axes the single-run drive-through / `pass@1` view is blind to. The implementation is 3 NEW files (harness + corpus + CI test), **ZERO src edit** — it WRAPS the existing `ChatClient` + `Verifier` ABCs and direct-constructs the real `AgentLoopImpl`.

**The gap it settles**: research found `reliability ≠ capability`, diverging super-linearly with task length (τ-bench: GPT-4o pass@1 ~61% but pass^8 <25%). V2 had no repeatability measurement (`grep` confirmed zero `pass^k`/`consistency`/`fault`/`MAST` scaffolding in `backend/src`). This harness MEASURES the claim on V2's own loop rather than assuming it.

**Drive-through verdict** (real Azure gpt-5.2, 12 cases · k=3 · 90 runs): pass^k 100% = pass@1 100% (NO divergence on this reasoning corpus — valid verdict: corpus too easy to stress the regime) BUT 2 pass@1-invisible signals surfaced — answer-consistency 75% + λ-degradation 50% under a 20% fault rate.

## 2. Decision Matrix

| Decision | Chosen | Alternatives rejected | Why |
|----------|--------|-----------------------|-----|
| Axes measured | all 4 (pass^k + behavioral-consistency + λ-fault + ε-perturbation) | minimal 2 (pass^k + consistency) | user-picked; the spike self-produces λ/ε data on V2's loop, sidestepping the 🔴 weak external λ/ε citations |
| Run generation | online (harness drives `loop.run()` k times) | offline (consume persisted `message_events`) | prod has no naturally-repeated runs → nothing to consume; mirrors `benchmark_judge.py:171-187` calling the judge |
| Loop construction | direct `AgentLoopImpl(...)` (`benchmark_pass_k.py:_build_loop`) | `build_real_llm_handler()` | the factory takes NO `chat_client` param (`handler.py:280-296`) → can't inject the λ wrapper; direct-construct uses ONE path for both arms |
| λ injection point | chat client wrapper, DEFAULT loop error handling | custom transient-classifying `error_policy` + retry matrix | baseline/fault differ ONLY by the wrapper = cleanest A/B; measures the real production loop's resilience as-is (retry-specific recovery = a follow-up) |
| Rules oracle | inline normalized exact/contains | `RulesBasedVerifier` (`rules_based.py:40`) | that ABC is a `Rule`-list (regex/format) abstraction; a plain compare is zero-dependency + zero judge noise |
| Judge oracle | per-case raw template embedding the criterion + `{output}` | a named template (`output_quality`) | named templates see only `{output}`/`{trace}`, NOT the task → can't judge per-task correctness; a raw template embeds the criterion + emits the `{"passed": bool}` JSON `_parse_response` reads (`llm_judge.py:141-187`) |
| Surface | pure offline script (no wire/UI/migration) | wire event + chat-v2 dashboard | YAGNI — pass^k is a CI/offline metric, like the 5 existing `benchmark_*.py` |
| tool_use corpus | deferred (easy+multistep shipped) | include tool_use now | needs mock-tool determinism; keeps the harness DB-free + robust |

## 3. Cross-Category Contracts

**N/A** — no new cross-category contract / ABC introduced. The harness CONSUMES existing contracts (`ChatClient` `adapters/_base/chat_client.py:63`, `Verifier`/`LLMJudgeVerifier` `verification/llm_judge.py:57`, `AgentLoop` `orchestrator_loop/loop.py:315`) and follows the established `benchmark_*.py` eval pattern (Sprint 57.111 / 57.136-139). Nothing to register in `17-cross-category-interfaces.md`. (`_FaultInjectingChatClient` IMPLEMENTS the existing `ChatClient` ABC; it is test/eval scaffolding in `scripts/`, not a production adapter.)

## 4. Verified Invariants (this spike)

All verified via the CI-safe unit suite + the real-Azure drive-through:
- **pass^k computation correct**: per-case pass^k = all-k-pass; aggregate = fraction of all-pass cases — `test_build_report_pass_k_and_divergence` (`tests/unit/scripts/test_benchmark_pass_k.py`).
- **harness drives the REAL loop offline**: a spy `ChatClient` + real `AgentLoopImpl` (monkeypatched executor) → k outcomes — `test_run_case_drives_loop_offline`.
- **λ deterministic under seeded rng**: `_FaultInjectingChatClient` raises exactly per `random.Random(seed)` — `test_fault_client_seeded_rng_is_deterministic`.
- **hybrid oracle**: rules contains/exact + judge reads `{"passed":...}` JSON — `test_evaluate_*` (5 tests).
- **LLM-neutral**: `_FaultInjectingChatClient` subclasses `adapters._base.ChatClient` (no native import) — v2 `test_llm_sdk_leak` 3/3.
- **real-Azure end-to-end**: smoke (k=1, 14 calls) + full (k=3, 90 runs, 94,373 tokens) both exit 0 with a coherent report — `artifacts/passk-drivethrough-verdict.{md,json}`.

**Verification command**:
```
RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... \
  python scripts/benchmark_pass_k.py --k 3 --fault-rate 0.2 --epsilon
# CI-safe (no Azure):
python -m pytest tests/unit/scripts/test_benchmark_pass_k.py -q   # 17 passed
```
**Fixture**: `backend/tests/fixtures/observability/pass_k_cases.yaml` (12 cases, difficulty-graded).

## 5. Open Invariants (NOT verified here — deferred)

- **pass^k < pass@1 divergence regime NOT reached** — the reasoning corpus + k=3 + gpt-5.2 gives 100%/100%. The research's pass^8<25% was on tool-heavy multi-turn agentic tasks (τ-bench). Reaching the divergence regime needs a harder/longer/tool-using corpus + k≥5 → `AD-Eval-PassK-Harder-Corpus-Phase58`.
- **λ measures degradation net of DEFAULT loop handling only** — no chat-level retry exists, so a faulted chat call fails the run (pass^k 100%→50% at fault 0.2). Retry-specific recovery is unmeasured → `AD-Loop-ChatLevel-Retry-Phase58`.
- **answer-consistency 75% not attributed per-case** — which 3 cases differ, and is the difference semantic or cosmetic? → `AD-Eval-Answer-Consistency-Surface-Phase58`.
- **MAST 14-mode failure classifier** — no taxonomy in repo; a separate large item.
- **persistence-driven cross-tenant pass^k pipeline** — the harness GENERATES runs; reading them back from `message_events` is the research-flagged scarce-data opportunity, deferred.

## 6. Rollback

Trivial — 3 NEW files, ZERO src edit. `git rm scripts/benchmark_pass_k.py tests/fixtures/observability/pass_k_cases.yaml tests/unit/scripts/test_benchmark_pass_k.py` removes the harness with no runtime impact (nothing imports it; CI runs it only via the unit test). No migration / no wire / no config to revert. The `benchmark_reports/` output dir is gitignored.

## 7. References

- `claudedocs/5-status/passk-reliability-thin-spike-eval-20260624.md` — the pre-implementation eval / option matrices
- `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.7 / §5 #2 / §6 — research #2 source (pass^k 🟢; λ/ε 🔴 citation-weak)
- `backend/scripts/benchmark_judge.py` (Sprint 57.111) — the harness pattern mirrored
- `backend/src/agent_harness/orchestrator_loop/loop.py:315,1942` — `AgentLoopImpl` ctor + `run()` (the loop under test)
- `backend/src/agent_harness/verification/llm_judge.py:57,141` — the judge + its `{"passed":...}` parse format
- CHANGE-108 + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-141/{progress,retrospective}.md`

## 8-Point Quality Gate (self-review)

- [x] 1. Section header ↔ spike US (§4 invariants map to US-1..6)
- [x] 2. Every technical claim carries file:line (§2/§3/§4 anchored)
- [x] 3. Decision rationale = comparison matrix (§2, 8 rows with rejected alternatives)
- [x] 4. Verification command reproducible (§4 — both real-Azure + CI-safe)
- [x] 5. Test fixture referenced (§4 — `pass_k_cases.yaml` + the 17-test suite)
- [x] 6. Open invariants boundary explicit (§5 — what was NOT verified, with follow-on ADs)
- [x] 7. Rollback path (§6 — 3-file `git rm`, zero src impact)
- [x] 8. 17.md cross-ref (§3 — N/A justified: no new contract, reuses ChatClient/Verifier ABCs)
