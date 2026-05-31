# CHANGE-031: Production Chat-Path Category Activation (Cat 4 / 7 / 8 / 10)

**Date**: 2026-05-31
**Sprint**: 57.63
**Scope**: Cat 4 (Context Mgmt) + Cat 7 (State Mgmt) + Cat 8 (Error Handling) + Cat 10 (Verification) — wired into the production `POST /api/v1/chat/` flow
**Source**: `claudedocs/5-status/breadth-probe-20260531.md` §4.2 (Potemkin finding: these categories present in the loop but not injected on the production chat path)

## Problem

The breadth-probe (v4.2 §4.2) showed the production chat path (`build_handler` → `build_real_llm_handler` → `AgentLoopImpl.run()`) activated only Cat 1/2/6/9(engine)/HITL. Four categories were built into `AgentLoopImpl` as opt-in deps but **never injected** on the production flow (a Potemkin / AP-4 gap):

- **Cat 4** (context compaction) — no `compactor=`
- **Cat 7** (state reducer + checkpointer) — no `reducer=` / `checkpointer=` / `tenant_id=`
- **Cat 8** (error policy + retry + circuit breaker + budget + terminator) — none injected
- **Cat 10** (verification) — `run_with_verification` always wrapped the loop, but `chat_verification_mode` defaulted to `"disabled"` + a no-op `RulesBasedVerifier(rules=[])` → wired-but-inert

## Root Cause

`build_real_llm_handler` (Sprint 50.2) wired only the minimum (chat_client / parser / tools / system_prompt), later adding Cat 9 guardrails (57.2) + HITL (53.6). The opt-in `| None = None` ctor params for Cat 4/7/8 (added 52.1 / 53.1 / 53.2) were never populated on the production path — they were only exercised by unit tests. Cat 10's chat wiring (55.5) shipped the 2-mode dispatch scaffold but defaulted off with a no-op verifier.

Day-0 verification confirmed the loop body already invokes these deps when present (no loop.py change needed):
- Cat 4: `loop.py:828` `if self._compactor is not None:` → `847` `compact_if_needed` → `861` `yield ContextCompacted`
- Cat 7: `loop.py:1350` three-None guard → `1373` `reducer.merge` → `1381` `checkpointer.save` → `1382` `StateCheckpointed`
- Cat 8: `_handle_tool_error` (`loop.py:265`) is called at `1157` + `1225` (the 53.2 "Day 4 wires" comment was stale; already wired)

→ Cat 4/7/8 activate by **injection alone**. Cat 10 needed the verifier registry threaded from the handler (the verifier needs the loop's adapter).

## Solution

**NEW** `backend/src/api/v1/chat/_category_factories.py` (api layer; LLM-neutral — receives the adapter as the `ChatClient` ABC, so `agent_harness/**` keeps zero SDK imports):
- `make_chat_compactor(chat_client)` → `HybridCompactor(structural=StructuralCompactor(), semantic=SemanticCompactor(chat_client=...), token_budget=100_000, token_threshold_ratio=0.75)` (Cat 4)
- `make_chat_state_deps(db, session_id, tenant_id)` → `(DefaultReducer(), DBCheckpointer(db, session_id=, tenant_id=))` or `(None, None)` when any input missing (Cat 7 all-three-or-nothing)
- `make_chat_error_deps()` → the 5 Cat 8 deps; terminator composes the same breaker + budget instances
- `make_chat_verifier_registry(chat_client, judge_template)` → `VerifierRegistry` with one real `LLMJudgeVerifier` (Cat 10)

**EDIT** `backend/src/api/v1/chat/handler.py`:
- `build_real_llm_handler` + `build_handler` accept `db` / `session_id` / `tenant_id`
- real_llm handler injects compactor + reducer + checkpointer + tenant_id + 5 error deps
- **Cat 10 approach A** (user-confirmed): the 3 builders now return `(loop, verifier_registry)`. real_llm builds a real-verifier registry when `chat_verification_mode == "enabled"` (sharing the loop's adapter), else `None`. echo_demo returns `(loop, None)` — predictable fixtures, no verification.

**EDIT** `backend/src/api/v1/chat/router.py`:
- `session_id` generation moved **before** `build_handler` (ordering fix — the checkpointer binds to it)
- `loop, verifier_registry = build_handler(...)`; `verifier_registry` threaded into `_stream_loop_events`
- removed the in-function `select_verifier_registry(...)` call + the now-unused `from ._verifier_factory import select_verifier_registry`

**EDIT** `backend/src/core/config/__init__.py`:
- new `chat_verification_judge_template: str = "safety_review"`
- `chat_verification_mode` kept default `"disabled"` (safe rollout — production behavior unchanged until validated)

### `_verifier_factory.py` disposition (deferred)

Approach A makes `select_verifier_registry` / `build_default_verifier_registry` production-unused (only `test_verification_wire.py` references them). **Kept intact** (not deleted) — touches the "never delete tests" rule and was not authorized for deletion. Revisit in a later sprint: either delete + retire its 4 tests, or keep as a documented helper.

## Verification

All from real tool output (grep-filtered summary lines are authoritative):

- **NEW** `backend/tests/integration/api/test_chat_category_activation_wiring.py` — **8 passed** (2 groups, both Azure-call-free + deterministic):
  - Group A (6) — handler injection completeness: loop carries Cat 4 compactor / Cat 8 5-dep chain / Cat 7 deps (wired with db, no-op without); Cat 10 registry follows `chat_verification_mode` (None disabled / 1 real `LLMJudgeVerifier` enabled). Uses fake `AZURE_OPENAI_*` env (config object only, no network).
  - Group B (2) — Cat 7 real DB persistence: `make_chat_state_deps`-built `DBCheckpointer.save()` writes a real `StateSnapshot` row; cross-tenant `load()` → `StateNotFoundError`. Real `db_session` + `seed_tenant`/`seed_user`.
- **NEW** `backend/tests/unit/api/test_category_factories.py` — 8 unit tests (compactor type / Cat 7 all-three-or-nothing matrix / Cat 8 5-dep + terminator composition / Cat 10 registry).
- Existing `test_chat_e2e.py` (9) + `test_handler.py` + `test_partial_swap.py` + `test_chat_hitl_production_wiring.py` updated for the `(loop, registry)` return shape — all green.
- Full backend: **`pytest -q` → 1928 passed, 0 failed, 4 skipped** (verified via JUnit XML — `failures=0 errors=0`; the 4 skipped are pre-existing, unrelated to this change).
- `mypy src/` → **Success: no issues found in 320 source files**.
- `python scripts/lint/run_all.py` → **9/9 V2 lints green** — incl. `check_llm_sdk_leak` (LLM-neutrality preserved: `agent_harness/**` has no `import openai/anthropic`) + `check_ap4_frontend_placeholder`. This closes an AP-4 (Potemkin) instance rather than adding one.
- flake8 / black / isort on changed files → clean.

**Not yet verified** (deferred — needs a real Azure key, MISSING in this environment): the full `real_llm` SSE e2e proving `StateCheckpointed` / `ContextCompacted` / `VerificationPassed` events on the streaming path. echo_demo SSE intentionally does NOT inject these categories (predictable fixtures), so it cannot substitute. Tracked for an env with `AZURE_OPENAI_*` configured.

## Impact

- Backend only; no frontend change; no DB migration (Cat 7 reuses the existing `StateSnapshot` ORM / `append_snapshot`).
- Production behavior change: real_llm chat now compacts context (Cat 4), checkpoints state per turn to `state_snapshots` (Cat 7, tenant-scoped), and runs the error-handling chain on tool failures (Cat 8).
- Cat 10 verification remains **off by default** (`chat_verification_mode="disabled"`); flipping to `"enabled"` activates a real `LLMJudgeVerifier` (safety_review template, final-output only) sharing the loop's adapter — an extra LLM call per verification (latency + cost), so it is gated until validated.

## Files Changed

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/_category_factories.py` | **NEW** — 4 LLM-neutral chat-path category factories |
| `backend/src/api/v1/chat/handler.py` | thread db/session_id/tenant_id; inject Cat 4/7/8; Cat 10 return `(loop, registry)` |
| `backend/src/api/v1/chat/router.py` | session_id ordering fix; unpack + thread verifier_registry; drop in-fn select_verifier_registry |
| `backend/src/core/config/__init__.py` | + `chat_verification_judge_template`; mode kept default disabled |
| `backend/tests/integration/api/test_chat_category_activation_wiring.py` | **NEW** — 8 tests (handler injection + Cat 7 real DB) |
| `backend/tests/unit/api/test_category_factories.py` | **NEW** — 8 unit tests |
| `backend/tests/unit/api/v1/chat/test_handler.py` | updated for `(loop, registry)` return shape |
