# Sprint 57.82 Plan — B-8 leg-1: Cat 10 verification judge token → cost ledger + quota (closes AD-Cat10-Judge-Cost-Ledger / B-8 blocker A)

**Branch**: `feature/sprint-57-82-verification-cost-ledger` (from `main` `7086c48c`)
**Closes**: B-8 **blocker A** only (`AD-Cat10-Judge-Cost-Ledger`) — the billing leg of the "完整 B-8" epic. Does **NOT** flip the default.

---

## 0. Background

`cat10-verification-default-enable-analysis-20260601.md` concluded "do NOT flip `chat_verification_mode` to `enabled` now" because of **3 launch-blockers**: (A) judge LLM call is not recorded in cost ledger nor counted against quota (billing/quota under-report); (B) the default `safety_review` template is Cat 9-fitted, unsuitable as a general final-output judge; (C) the enabled path has zero real-LLM test. The analysis also noted the *benefit* only materializes once real-LLM is live.

Since that analysis (2026-06-01), **real-LLM is live** (C-11, #237/#238, finished 57.79) — blocker C's prerequisite (Azure key) is cleared. User selected **完整 B-8 (clear 3 blockers + flip default)**. That is a 2-3 sprint epic; per rolling discipline we execute leg-by-leg and do **not** pre-write future leg plans.

**Epic roadmap** (this plan = leg 1 only):
- **Leg 1 = THIS sprint (57.82)**: blocker A — judge token → cost ledger + quota. Pure backend, mock-verifiable, **no flag flip**.
- **Leg 2 = 57.83** (plan written only at 57.82 closeout): blocker B (design a general final-output judge template) + blocker C (real-LLM e2e: false-positive rate / latency / cost) + flip default `enabled`. Needs real Azure. (B's false-positive measurement intrinsically depends on C's real-LLM, so B and C are bundled in leg 2, not leg 1.)

**Why blocker A is leg 1**: it is the only blocker that belongs to 鑰匙鏈② (billing correctness), is pure backend, needs no real-LLM, and is a correct fix regardless of whether the default is ever flipped (once judge runs, billing is right).

### Day-0 ground-truth (parent grep + code read + Explore, main `7086c48c`; source analysis is 8 sprints old — re-verified)

- **Blocker A confirmed STILL HOLDS** (57.79 changed pricing-key only, did not touch judge accounting): `LLMJudgeVerifier.verify()` (`llm_judge.py:84-89`) calls `self._chat.chat()` and keeps only `response.content` — `response.usage` (a `TokenUsage`: prompt/completion/cached/total) + `response.model` are **discarded**. Cost ledger is recorded only in the router SSE observer at `LoopCompleted` (`router.py:435` `record_llm_call`, sourced from the loop's `metrics_acc`); quota reconcile likewise reads `event.total_tokens` (`router.py:392`). Judge tokens flow through neither → under-report.
- **Verification runs in the WRAPPER, after `LoopCompleted`** (`correction_loop.py:121-209`): the inner `agent_loop.run()` already emitted `LoopCompleted` (captured, not yet yielded) before any judge call. The loop's `metrics_acc` is frozen by then → judge tokens must be accumulated by the **wrapper**, not the loop accumulator. (Corrects the Explore agent's "call `metrics_acc.on_event` in loop" suggestion — the loop is done.)
- **Data structures** (Explore-verified):
  - `VerificationResult` (`_contracts/verification.py:31-42`): `passed / verifier_name / verifier_type / score / reason / suggested_correction / metadata` — **no token fields**.
  - `LoopCompleted` (`_contracts/events.py:127-166`): already has `input_tokens / output_tokens / provider / model / cached_input_tokens / cache_hit_rate` (Sprint 57.2).
  - `ChatResponse.usage` (`_contracts/chat.py`): `TokenUsage(prompt_tokens, completion_tokens, cached_input_tokens, total_tokens)`.
  - `CostLedgerService.record_llm_call` (`cost_ledger.py:106-184`): writes 2 entries `{provider}_{model}_input/_output`; sub_type is a plain string column → **no DB/schema change** to add a judge sub_type variant.
  - `QuotaEnforcer.record_usage` (`quota.py:171-192`): `record_usage(*, tenant_id, actual_tokens, reserved_tokens)`.
  - SSE: `LoopCompleted` serialized in `sse.py`; verification events at `sse.py:277-300`.
  - 17.md single-source: §1.1 VerificationResult (L63) / §2.1 Verifier ABC (L139) / §4.1 LoopEvent table (LoopCompleted; VerificationPassed/Failed L248-250).
- **Design locked (user AskUserQuestion 2026-06-05)**: Option 1 — wrapper accumulates judge token → `LoopCompleted.verification_input_tokens/verification_output_tokens/verification_model` → router records a **separate** judge ledger entry (distinct sub_type) at the same `LoopCompleted` observer + adds judge tokens to the quota `actual_tokens`. Single observer point; transparent attribution; loop token semantics not polluted.
- **Default unchanged**: `chat_verification_mode` stays `disabled` (config:112). When disabled the wrapper takes the passthrough branch (`correction_loop.py:110-117`) → no verification, verification token fields stay `0` → zero behavior change on the default path.

---

## 1. Sprint Goal

When verification is enabled, the judge LLM call's tokens are recorded in the cost ledger (as a distinct, attributable sub_type) and counted against tenant quota — closing B-8 blocker A — **without** flipping the default and **without** real-LLM in this sprint (mock-verifiable).

---

## 2. User Stories

- **US-1**: As a platform operator, I want the judge LLM call's token usage captured (not discarded), so it can be accounted downstream. (`VerificationResult` + `LLMJudgeVerifier`)
- **US-2**: As a platform operator, I want judge tokens to bubble to the router via `LoopCompleted`, so accounting stays at the single existing observer point. (`events.py` + `correction_loop.py` wrapper)
- **US-3**: As finance/compliance, I want judge tokens in the cost ledger (a distinct sub_type) and in quota, so billing is correct and judge cost is separately auditable. (`cost_ledger.py` + `router.py`)
- **US-4**: As a developer, I want the SSE `LoopCompleted` + 17.md contract to reflect the new fields, so the single-source stays accurate. (`sse.py` + `17.md`)
- **US-5**: As a maintainer, I want mock tests covering all three wrapper exit paths (all-pass / correction / exhausted), so the accounting is verified without real-LLM. (tests)

---

## 3. Technical Specifications

### 3.0 Architecture

agent_harness emits a neutral event carrying judge token counts; the api/router layer does the billing write (keeps category boundary: no `platform_layer` import inside `agent_harness`). Mirrors the existing `LoopCompleted` → `record_llm_call` observer pattern (Sprint 57.2). No DB/schema change (sub_type is a string column). Default path (disabled) untouched.

### 3.1 Capture judge token (US-1) — `_contracts/verification.py` + `verification/llm_judge.py`

- `VerificationResult`: add `input_tokens: int = 0`, `output_tokens: int = 0`, `model: str | None = None` (defaults keep rules_based / external verifiers untouched).
- `LLMJudgeVerifier.verify()`: after `response = await self._chat.chat(...)`, before parsing, capture `response.usage` (prompt_tokens → input, completion_tokens → output) + `response.model`; thread into the returned `VerificationResult` (both the pass and the parse-fail return paths; the fail-closed exception path keeps 0 — no usage on a thrown call).

### 3.2 Bubble via LoopCompleted (US-2) — `_contracts/events.py` + `verification/correction_loop.py`

- `LoopCompleted`: add `verification_input_tokens: int = 0`, `verification_output_tokens: int = 0`, `verification_model: str | None = None`.
- `run_with_verification` wrapper: accumulate `result.input_tokens / output_tokens` across **all verifiers and all correction attempts** into running totals (`vin / vout`), capture last non-None `result.model`. Fill the 3 fields on **every** `LoopCompleted` it yields that ran judges:
  - all-pass forward (`correction_loop.py:194`) → fill captured_completion.
  - exhausted (`correction_loop.py:200`) → fill the newly-built `verification_failed` LoopCompleted.
  - non-end_turn (`correction_loop.py:146`) → judges did NOT run → fields stay 0 (do not fill).
  - passthrough (registry None/empty, `correction_loop.py:110-117`) → unchanged (0).
- Use `dataclasses.replace(captured_completion, verification_input_tokens=...)` to fill (events are frozen dataclasses; verify frozen-ness Day-0).

### 3.3 Record judge cost + quota (US-3) — `platform_layer/billing/cost_ledger.py` + `api/v1/chat/router.py`

- `record_llm_call`: add optional `sub_type_suffix: str = ""` → entries become `{provider}_{model}{suffix}_input/_output` (default `""` keeps existing loop sub_types byte-identical). Judge call passes `sub_type_suffix="_verification"`.
- `router.py` LoopCompleted observer (after the existing loop `record_llm_call` at :435): if `event.verification_input_tokens > 0 or event.verification_output_tokens > 0`, call `record_llm_call(provider=event.provider or "azure_openai", model=event.verification_model or event.model or _FALLBACK_PRICING_MODEL, input_tokens=event.verification_input_tokens, output_tokens=event.verification_output_tokens, session_id=session_id, sub_type_suffix="_verification")`. Best-effort try/except (mirror existing). Judge shares the loop's adapter → `event.provider` is correct for the judge.
- quota (`router.py:392`): `actual_tokens=event.total_tokens + event.verification_input_tokens + event.verification_output_tokens` so judge tokens count against the cap.

### 3.4 SSE serialize (US-4) — `api/v1/chat/sse.py`

- `LoopCompleted` serializer: add the 3 verification token fields to the emitted payload (observable; frontend may ignore). No change to verification_passed/failed serializers.

### 3.5 17.md contract sync (US-4) — `17-cross-category-interfaces.md`

- §1.1 VerificationResult: add the 3 optional token fields (judge-only; default 0/None).
- §4.1 LoopCompleted row: note the 3 verification token fields + that they are filled by 範疇 10 wrapper, consumed by the chat router billing observer.

### 3.6 Tests (US-5) — new + extend

- `test_llm_judge.py` (extend): MockChatClient returns a `ChatResponse` with `usage` + `model` → assert `VerificationResult.input_tokens/output_tokens/model` populated; fail-closed path keeps 0.
- `test_correction_loop.py` (extend): judge with token usage across (a) all-pass → captured LoopCompleted carries summed verification tokens; (b) 1 correction then pass → tokens summed across 2 judge runs; (c) exhausted → verification_failed LoopCompleted carries summed tokens; (d) non-end_turn → fields stay 0; (e) passthrough → 0.
- integration (`tests/integration/api/`): enabled registry with mock judge → assert a distinct `_verification_input/_output` cost ledger entry is written **and** quota `actual_tokens` includes judge tokens. (MockChatClient — AP-10: structural invariant asserted on the billing path, not relying on real Azure.)

### 3.7 Lint / validation

`black + isort + flake8 + mypy src/` + `python scripts/lint/run_all.py` (check_llm_sdk_leak must stay green — no openai/anthropic import added to agent_harness; the judge token capture uses neutral `TokenUsage`). Full format chain pre-commit (57.80 lesson).

---

## 4. File Change List

**Code (7)**:
1. `backend/src/agent_harness/_contracts/verification.py` — +3 fields on VerificationResult
2. `backend/src/agent_harness/verification/llm_judge.py` — capture usage + model into result
3. `backend/src/agent_harness/_contracts/events.py` — +3 fields on LoopCompleted
4. `backend/src/agent_harness/verification/correction_loop.py` — wrapper accumulates + fills (3 yield points)
5. `backend/src/platform_layer/billing/cost_ledger.py` — `sub_type_suffix` param on record_llm_call
6. `backend/src/api/v1/chat/router.py` — judge record_llm_call + quota actual includes judge
7. `backend/src/api/v1/chat/sse.py` — LoopCompleted serializer +3 fields

**Docs (1)**:
8. `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — §1.1 + §4.1

**Tests (3 extend)**:
9. `backend/tests/unit/agent_harness/verification/test_llm_judge.py`
10. `backend/tests/unit/agent_harness/verification/test_correction_loop.py`
11. `backend/tests/integration/api/` — judge billing + quota (new test file or extend existing verification integration test)

---

## 5. Acceptance Criteria

1. Enabled registry + mock judge with usage → cost ledger has a **distinct** `{provider}_{model}_verification_input/_output` entry separate from the loop entry; quota `actual_tokens` includes judge tokens.
2. Judge tokens summed across correction attempts (a 1-correction run records the tokens of both judge calls).
3. Default `disabled` path: zero behavior change (verification token fields = 0; no extra ledger entry; quota unchanged) — asserted.
4. Non-end_turn + passthrough paths: verification token fields stay 0.
5. `check_llm_sdk_leak` green; no `platform_layer` import inside `agent_harness`.
6. mypy `src/` 0 errors; full pytest green (+N new); `run_all.py` 10/10.

## 6. Deliverables

- [ ] US-1: VerificationResult +3 fields + llm_judge captures usage/model
- [ ] US-2: LoopCompleted +3 fields + wrapper accumulates across attempts + fills 3 yield points
- [ ] US-3: record_llm_call sub_type_suffix + router judge entry + quota includes judge
- [ ] US-4: sse LoopCompleted +3 fields + 17.md §1.1 + §4.1
- [ ] US-5: unit (llm_judge + correction_loop 5 paths) + integration (billing + quota) tests
- [ ] Closeout: CHANGE-049 + progress + retrospective + checklist all `[x]` + MEMORY + CLAUDE lean + next-phase-candidates

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — cross-category design with multiple wrapper exit points + 17.md contract change; careful coordination, like 57.81). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5.3 hr → class-calibrated commit ~4.2 hr (`medium-backend` 0.80).
- Day 4 retro Q2 verifies the multiplier (3-sprint window per §Workload Calibration).

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Wrapper has 3 LoopCompleted yield points — missing one drops judge tokens | §3.2 enumerates all 3 + non-end_turn(0) + passthrough(0); test (c)+(d)+(e) cover each path |
| 2 | Events are frozen dataclasses — can't mutate captured_completion | use `dataclasses.replace`; Day-0 confirm frozen=True on LoopCompleted |
| 3 | $0 pricing if judge model unpriced (FIX-022 caveat) | judge shares loop adapter/model; gpt-5.2 priced since 57.79; unknown model → $0 row (observable anomaly), not a crash — acceptable for leg 1 |
| 4 | AP-10 mock-vs-real divergence | judge billing asserted on MockChatClient with real `TokenUsage` shape; structural invariant on billing path (not relying on real Azure) — leg 2 adds real-LLM e2e |
| 5 | LLM neutrality (`check_llm_sdk_leak`) | capture uses neutral `TokenUsage`/`ChatResponse`; no SDK import added to agent_harness |
| 6 | Risk Class C (module singleton across test loops) | cost_ledger / quota singletons already have reset hooks; reuse autouse reset fixtures |

## 9. Out of Scope (this sprint; carryover)

- **Flip `chat_verification_mode` to `enabled`** → leg 2 (57.83), after blocker B + C.
- **Blocker B** (general final-output judge template + false-positive evaluation) → leg 2 (depends on real-LLM).
- **Blocker C** (real-LLM e2e: false-positive rate / p95 latency / per-chat cost) → leg 2 (needs real Azure).
- **Per-verifier cost attribution** (Option 3) — leg 1 aggregates all judge tokens into one verification sub_type; per-verifier breakdown not done.
- **Correction full-loop re-run cost** (analysis §2: worst case 3× loop) — the re-run loop tokens already flow through the normal LoopCompleted accounting; this sprint only adds the *judge* tokens. No change to loop-rerun accounting.
