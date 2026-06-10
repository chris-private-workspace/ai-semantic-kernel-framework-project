# CHANGE-066: Verification-ESCALATE human-in-the-loop — the max-fail terminal becomes a pause

**Change Date**: 2026-06-10
**Change Type**: Feature continuation (A2 — harness-deepening Workflow A; extends the A1 in-loop gate from CHANGE-065)
**Sprint**: 57.99 (A2)
**Scope**: agent_harness/orchestrator_loop (Cat 1) × agent_harness/verification (Cat 10) × Cat 9 HITL pause infra × Cat 7 State × api/v1/chat (handler) × core/config
**Status**: ✅ Complete — gate-green + the A2 escalate→APPROVE path drive-through-verified (real UI + real Azure + a real LLM judge); REJECT-with-note unit-proven + a documented chat-v2 frontend follow-up

## Change Summary

CHANGE-065 (A1) made Cat 10 verification an in-loop pre-delivery gate: on a FINAL answer the loop verifies; on FAIL with budget left it self-corrects in-loop; on FAIL at the budget it emits `LoopCompleted(stop_reason="verification_failed")` — a hard terminal that silently drops the answer.

This change makes that max-attempts terminal **conditionally ESCALATE to a durable human pause** instead. Behind a global `chat_verification_escalate_on_max` toggle (default **OFF** = A1 byte-identical), when in-loop self-correction is exhausted AND the full deferred-HITL wiring is present, the loop pauses (mirroring the 57.91-93 Cat 9 ESCALATE pauses) and emits `ApprovalRequested(HIGH)` + `LoopCompleted(awaiting_approval)`, holding the failed answer in the pause checkpoint. The human then decides via `resume()`:

- **APPROVE** — the human OVERRIDES the verifier → the held failed answer is delivered verbatim (terminal replay, no LLM re-call, NOT re-verified; reuses the 57.93 `_replay_approved_output`).
- **REJECT-with-note** — the reviewer's note re-injects as a `user` correction Message + the loop runs EXACTLY ONE human-coached turn. If that turn fails the gate again it takes the A1 `verification_failed` terminal (no second pause).

Because `resume()` drives the SAME `_run_turns` and the durable `verification_escalated` flag rides the pause checkpoint metadata, the one-coached-turn bound survives pause→resume. **No new event type** (reuses `ApprovalRequested`/`ApprovalReceived`/`LLMResponded`/`LoopCompleted`).

## Change Reason

`claudedocs/1-planning/harness-deepening-proposal-20260610.md` Workflow A listed verification-ESCALATE as the A1 follow-up (design-note 25 §4 "A2" Open Invariant). A1's hard terminal is correct as a default but, for high-stakes flows, dropping a max-fail answer with no human off-ramp is worse than letting a reviewer either ship it (override) or coach one more attempt. The 57.91-93 deferred-HITL pause infra + the A1 in-loop gate made A2 a toggle + one pause method + one resume branch, not loop surgery.

## Detailed Changes

### Day-1 — the config toggle + the escalate pause (US-1 / US-2)
- `core/config/__init__.py` — NEW `chat_verification_escalate_on_max: bool = False` (env `CHAT_VERIFICATION_ESCALATE_ON_MAX`), in the `chat_verification_*` cluster.
- `orchestrator_loop/loop.py` — `AgentLoopImpl.__init__` gains `verification_escalate_on_max: bool = False` (stored). NEW `_cat10_verification_escalate_pause()` (the verification analogue of `_cat9_output_hitl_pause`: builds a `verification`-kind `pending_approval` with the held-answer snapshot + the verifier reasons, emits `ApprovalRequested(HIGH)`, persists `verification_escalated=True`; fails closed to the A1 terminal on no-identity / persist-fail). The FAIL==max swap-point (`_run_turns`) gains a conditional: `if self._verification_escalate_on_max and not verification_escalated and <full HITL wiring> → escalate pause + return; else → A1 verification_failed terminal` (byte-identical). `_emit_deferred_pause` / `_emit_state_checkpoint` thread a new `verification_escalated: bool = False` param → `metadata["verification_escalated"]` (rides metadata, no migration — the 57.98 `verification_attempts` precedent).
- `api/v1/chat/handler.py` — the MAIN real_llm `AgentLoopImpl(...)` reads `verification_escalate_on_max=settings.chat_verification_escalate_on_max` (echo-demo + child-loop sites unchanged).

### Day-2 — resume APPROVE / REJECT + the durable bound (US-3 / US-4 / US-5)
- `orchestrator_loop/loop.py` — `resume()` rehydrates `verification_escalated = bool(metadata.get("verification_escalated", False))` at the top (mirrors the `verification_attempts` read) + threads it into the shared `_run_turns` drive. NEW `elif kind == "verification":` branch (between the 57.93 `output` branch and the 57.88 `tool` `else`): APPROVE → `_replay_approved_output` (terminal, no re-verify) + `return`; REJECT → append `Message(role="user", "[Verification rejected by reviewer: {reason}. Please revise the answer.]")` + force `verification_attempts = max` + `verification_escalated = True` → fall through to the `_run_turns` drive.
- **D-DAY2-1**: the REJECT branch sets both `verification_attempts = max` and `verification_escalated = True` explicitly even though the metadata top-read already supplies both — defensive (the bound is airtight regardless of the persisted values) + matches the locked decision; one redundant line. The metadata top-read remains THE durable mechanism US-5 tests.

### Day-3 — the full-sweep escape fix
- **D-DAY3-1**: the Day-1 `handler.py:474` new read of `settings.chat_verification_escalate_on_max` broke 2 Sprint-57.97 multi-model-profile tests whose `_force_verification_enabled` helper stubs `get_settings` with a `SimpleNamespace` that didn't carry the new attribute (the Day-1 scoped regression run missed it; the Day-3 full sweep caught it). Fix: add `chat_verification_escalate_on_max=False` to that stub (mirror real `Settings`, default OFF). Test-only; no production change.

## Modified Files List

| File | Change |
|------|--------|
| `backend/src/core/config/__init__.py` | EDIT — NEW `chat_verification_escalate_on_max` setting |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT — ctor toggle + `_cat10_verification_escalate_pause` + FAIL==max conditional + durable flag threading + `resume()` `kind="verification"` branch |
| `backend/src/api/v1/chat/handler.py` | EDIT — thread the toggle into the MAIN real_llm loop ctor |
| `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` | EDIT — `_paused_state_verified` `kind="verification"` branch + `_CapturingChatClient` + 5 tests (2 Day-1 escalate + 3 Day-2 resume) |
| `backend/tests/unit/api/v1/chat/test_handler.py` | EDIT — stub the new setting (D-DAY3-1) |

## Verification

- `pytest backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` — **31 passed** (28 prior + 3 Day-2 resume): toggle-OFF A1-byte-identical, toggle-ON escalate pause, resume APPROVE replays held, resume REJECT coaches one turn, reject-then-fail binds to A1.
- **Gate**: `mypy src` 0/353 · `python scripts/lint/run_all.py` 10/10 (AP-1 — the escalate is a conditional `return` in the while-driven `_run_turns`; `check_event_schema_sync` green = no new event; SDK-leak 0) · `pytest -m "not real_llm"` **2299 passed + 4 skipped** (Day-0 baseline 2298 + 5; zero deletion) · black/isort/flake8 clean.
- **Drive-through (Day-3 US-6) — APPROVE path VERIFIED**: real UI (jamie@acme.com/acme-prod, chat-v2, real_llm) + a fresh backend (`CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + a forced-fail real-LLM judge via `CHAT_VERIFICATION_JUDGE_TEMPLATE` env) + real Azure gpt-5.2. 3 final-answer attempts each `verification_failed` → attempt 2==max → `approval_requested risk=HIGH` + `loop_end stop=awaiting_approval` → kind-agnostic HITL card (severity HIGH, tool: —) → Approve → `resume()` → `_replay_approved_output` → turn flips to `stop: end_turn` + the held answer renders + "Decision: APPROVED". Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-99/artifacts/dt5799-{A-escalate-pause,B-approved-delivered}.png`.
- **Drive-through — REJECT-with-note: backend proven, frontend gap**: A2's backend reject-with-note + resume is unit-proven (`test_verify_escalate_resume_reject_coaches_one_turn` + `_reject_then_fail_binds_to_a1_terminal`), but NOT UI-drivable — `HITLTurn` deliberately does NOT `resume()` on reject (built for tool-kind reject=terminate) + the reject button has no note input. Wiring the chat-v2 UI (verification-kind resume-on-reject + a coaching-note input) is a documented frontend follow-up (out of A2's backend scope; user-confirmed Option A).
- **D-DAY3-2**: a forced-fail correction mentioning "approval" led gpt-5.2 to call the `request_approval` tool (a tool-kind 57.88 pause, NOT A2) — a tool-call turn is not a FINAL answer so the verify gate never reached failed_max. A neutral "no tools, just re-answer" correction kept 3 final answers → clean A2 escalate. Finding: a tool-equipped agent may ACT on a forced fail rather than re-answer.

## Impact

- **Behavioral (production)**: with the toggle ON, a max-attempts verification failure pauses for a human (held answer + override / coach-one-turn) instead of silently dropping the answer. With the toggle OFF (default) the A1 `verification_failed` terminal is byte-identical. No SSE wire / event-schema / DB-migration / frontend change.
- **Test-env**: any test that stubs `get_settings` for the real_llm handler must include `chat_verification_escalate_on_max` (D-DAY3-1).
- **Rollback**: the toggle is the kill-switch (default OFF = A1). Revert the commit to remove the branch entirely; `verification_escalated` metadata on any in-flight checkpoint is simply ignored by the A1 resume path.
