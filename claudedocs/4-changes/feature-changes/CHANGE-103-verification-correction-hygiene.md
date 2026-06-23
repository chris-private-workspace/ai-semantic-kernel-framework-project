# CHANGE-103: Verification correction-context hygiene (self-conditioning spike)

**Date**: 2026-06-23
**Sprint**: 57.136
**Scope**: Cat 1 (Orchestrator Loop) + Cat 4 (Context Mgmt — settings) + Cat 10 (Verification — measurement); backend-only, NO migration / NO new wire event / NO frontend

## Problem

The in-loop Cat 10 verification correction (`loop.py`, the `outcome=="correct"` branch) appended the **failed assistant answer verbatim** back into context before retrying. Research §7 (arXiv 2509.09677) warns this is the *self-conditioning* shape — a model that re-reads its own just-failed output in context tends to repeat the error, and model scale does not fix it. The structural risk was code-grounded (file:line read 2026-06-23) but the **effect magnitude** at this repo's 2-turn correction horizon was unmeasured. Closes `AD-Verification-Retry-Context-SelfConditioning` (research opportunity #6, the highest-tension reconciliation item).

## Root Cause

The correction branch was hardwired to `messages.append(Message(role="assistant", content=parsed.text))` (re-show the failed answer) then the correction `user` message, then `continue`. Intentional at the time (the docstring noted "the conversation — including the just-failed assistant answer — is already in `messages`"), but it left no lever to test the known mitigation (retry from a cleaner context) and no number to justify changing the default.

## Solution

Parameterized the correction-context handling — measure first, then let evidence gate the default (no blind refactor):

1. **`loop.py`** (Cat 1): new ctor param `correction_context_strategy: str = "keep"` (`loop.py:385`; stored `self._correction_context_strategy` at `:452`). The correction branch (`:2645`) now guards the failed-answer append:
   - `keep` (default, **any non-`summarize` value**) → `messages.append(assistant, parsed.text)` — **pre-57.136 byte-identical** (rollback guarantee).
   - `summarize` → **drops** the failed assistant turn; only the `user(correction_block)` feedback (reasons + suggested_correction, no answer quote) continues. Azure accepts the resulting consecutive `user` turns (adapter forwards verbatim; cf. 57.101 injection). `_WITHHELD_PLACEHOLDER` was NOT defined — Day-0 D-azure-role-pairing resolved that no placeholder is needed; it survives as an inline-comment fallback note for a future role-pairing-strict provider (no dead code, AP-2 / Karpathy §3).
2. **`core/config/__init__.py`** (Cat 4): `chat_verification_correction_strategy: str = "keep"` (`:142`; env `CHAT_VERIFICATION_CORRECTION_STRATEGY`). Used `str` not `Literal` so an unknown env value falls back rather than crashing startup.
3. **`handler.py`** (chat main flow): resolves `settings.chat_verification_correction_strategy`, `not in ("keep","summarize") → "keep"` (`:673-676`), threads `correction_context_strategy=` into `AgentLoopImpl(...)` (`:705`) — mirrors the `verification_escalate_on_max` 3-layer wire, minus the per-tenant policy layer (OUT this sprint — anti-AP-6; → C3 follow-up).
4. **`scripts/benchmark_correction_hygiene.py`** (Cat 10 eval, NEW): real-LLM A/B harness mirroring `benchmark_judge.py`. Reproduces the loop's two correction constructions (keep vs drop) WITHOUT the full loop, isolating the failed-answer-in-context as the only variable; both arms share the real `_build_correction_block`. Metrics: `retry_pass_rate` / `repeat_error_rate` (token-Jaccard of retry vs failed answer = self-conditioning signal) / `mean_prompt_tokens`. Plus golden fixture `tests/fixtures/verification/correction_hygiene_cases.yaml` (10 fail-prone cases) + CI-safe unit test `tests/unit/scripts/test_benchmark_correction_hygiene.py` (15 tests, MockChatClient).

## A/B Result (real Azure, 10 cases × 2 arms = 40 LLM calls)

| metric | keep | summarize | delta (summ−keep) |
|--------|------|-----------|-------------------|
| retry_pass_rate | 100% (10/10) | 100% (10/10) | +0.00% |
| repeat_error_rate | 0.207 | 0.165 | **−0.043** |
| mean_prompt_tokens | 80.0 | 62.8 | −17.2 |

**Verdict: `keep` stays default.** The #6 hypothesis is **directionally confirmed** — `summarize` lowers the failed-answer repeat (−4.3pp) and cuts prompt tokens (−17.2) — but the repeat effect is **below the 5% materiality threshold** and both arms' retries pass the judge 100%. So at the 2-turn correction horizon #6 is **low-risk**: `keep` keeps byte-identical behavior; `summarize` ships as a working env opt-in lever for the self-conditioning break + token savings. (Sample-size honesty: 10 controlled-first-fail cases where `suggested_correction` already names the right answer → both arms anchor on correct vocabulary → the effect is compressed. A spike directional read, not a production-distribution statistic; the harness is permanent + re-runnable on a larger/harder fixture.)

## Verification

- **Gate**: pytest **2765 passed + 5 skip** (baseline 2747 + 18 new = 3 gate + 15 hygiene) · mypy `src` **0/374** · v2 lints **10/10** (`python scripts/lint/run_all.py` cwd=root; incl. check_llm_sdk_leak) · black/isort/flake8 clean. Frontend sentinels unchanged (backend-only): Vitest 915 / mockup 51 / wire 25.
- **Unit**: `pytest tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py -k correction` → 3 passed (`test_correction_keep_includes_failed_answer` / `_summarize_drops_failed_answer` / `_unknown_strategy_falls_back_to_keep`); the 5 pre-existing gate tests = the keep byte-identical regression guard.
- **Drive-through PASS** (real UI + real backend + real Azure):
  - **Backend runtime** (real `build_real_llm_handler()` loop + real Azure + controlled fail-once verifier): wiring env→loop (`keep`/`summarize`/`banana`→`keep`); `VerificationFailed → retry → VerificationPassed → LoopCompleted`; keep retry context `[system×3, user, assistant, user]` (assistant_count=1, failed answer re-shown) vs summarize `[system×3, user, user]` (assistant_count=0, dropped; real Azure accepts consecutive user).
  - **UI** (chat-v2, real Azure gpt-5.2 ×2): main flow end-to-end (send→answer render) + verification gate on the main flow (Inspector "claim verified" + Loop visualizer `verification_passed` 0.93) + the 2620 change did NOT break the verification pass path (no-regression). Both real-Azure turns passed the strict judge → no UI correction triggered (the 57.99-documented "real fail can't be forced cleanly"); the correction loop + drop is proven by the deterministic backend runtime drive-through + 57.98/99 prior UI correction-render drive-throughs. Screenshot: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-136/artifacts/dt-57136-keep-verification-passed.jpeg`.

## Impact

Backend-only. Default behavior is byte-identical (`keep`); `summarize` is an env opt-in. No schema, no new wire event, no frontend, no per-tenant surface. Rollback = set/leave `CHAT_VERIFICATION_CORRECTION_STRATEGY=keep` (or revert the 3 src edits) — the keep arm is the pre-sprint code path. Follow-up: per-tenant `correction_context_strategy` (`AD-Verification-Correction-Strategy-PerTenant-Phase58`, → C3 seam).
