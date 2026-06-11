---
title: 26-between-turns-injection design note
purpose: Spike-extract design note from Sprint 57.101 (B1); documents verified runtime invariants for the between-turns message injection primitive
category: V2 extension docs (post-22-sprint era)
created: 2026-06-11 (Sprint 57.101 Day 4 closeout)
sprint_source: 57.101
verified_ratio: ≥ 95% (per 8-Point Quality Gate; the end-to-end drive-through is the single live-path verification, §2.6)
status: Active
---

# 26 — Between-Turns Message Injection Primitive Design Note (Sprint 57.101 B1 extract)

## 0. Spike Summary

- **Sprint scope (user stories)**: US-1 `MessageInbox` contract + loop drain seam / US-2 `MessageInjected` wire event / US-3 the cross-request injection channel + `POST /{id}/inject` / US-4 the chat-v2 composer usable mid-run / US-5 the injected message renders / US-6 drive-through.
- **One primitive, two payoffs** (proposal §2.2 收斂洞察 2): the same between-turns drain seam serves the chat live-injection payoff (this slice) AND the B2 TEAMMATE parent→child track (future — different `MessageInbox` backing, same loop seam).
- **Calibration**: scope class `loop-injection-primitive-spike` (NEW, mult 0.55). Bottom-up ~18.5 hr → committed ~10 hr. `agent_factor = 1.0` (parent-direct). Actual recorded in retrospective.md Q2.
- **Verification**: backend pytest +19 (inbox-drain 3 + injection-registry 9 + inject-endpoint 6 + sse 1) + parity 32→33; frontend Vitest +5 (chatStore 1 + InputBar 3 + eventSchema 1). Drive-through §2.6.

## 1. Decision Matrix

### 1.1 Cross-request channel: module-level registry vs per-request mailbox

| Option | Bridges 2 HTTP requests? | Precedent | Decision |
|--------|--------------------------|-----------|----------|
| **Module-level `InjectionRegistry` singleton** | ✅ yes (process-level) | `SessionRegistry` (`session_registry.py`) | ✅ **chosen** |
| Per-request `MailboxStore` (`subagent/mailbox.py`) | ❌ no — state dies with the request | — | ❌ rejected |
| DB-persisted queue | ✅ yes (+ durable) | — | ❌ over-engineered for an ephemeral per-run channel (YAGNI; AP-6) |

**Why chosen**: the inject POST and the streaming run are SEPARATE HTTP requests. `subagent/mailbox.py:46-100` is explicitly per-request ("no state survives across requests" — AD-Test-1 53.6), so it cannot carry a message from the inject request to the run request. A module-level singleton keyed by `(tenant_id, session_id)` — exactly the `SessionRegistry` shape — bridges them while preserving the multi-tenant 鐵律.

### 1.2 Guardrail check on the injection: INPUT chain vs between-turns chain (D-DAY1-1)

| Option | Checks the injected user text? | Reality |
|--------|-------------------------------|---------|
| Rely on the between-turns guardrail (the proposal's assumption) | ❌ NO | `_cat9_between_turns_check` checks `_latest_output_text(messages)` (`loop.py:1311`), which skips `role="user"` messages (`:1283-1285`) — it gates CONTINUATION on the just-completed turn's OUTPUT |
| **Run the Cat 9 INPUT chain (`engine.check_input`) on each drained message** | ✅ YES | the injection IS an input |

**Why chosen** (the load-bearing Day-1 finding): the proposal §2.2 assumed "drain before the between-turns guardrail → injected content checked for free". Reading the real code disproved it (the between-turns gate inspects OUTPUTS, not user inputs). The honest realization of the intent is to run the INPUT guardrail (`engine.check_input`, `guardrails/engine.py:119-126`) on each drained message. This is more faithful to "注入內容自動受 Cat 9 檢查" AND realizes the DoD "guardrail-on-injected case".

### 1.3 A blocked injection: drop vs pause vs terminate

| Option | Effect on the run | Decision |
|--------|-------------------|----------|
| **Drop the injection + emit `GuardrailTriggered(input)`** | run continues without it | ✅ **chosen** |
| Pause the run (HITL) on a blocked injection | run halts for a human | ❌ deferred (pause-on-injection is a follow-on; a side-instruction shouldn't trigger a full pause) |
| Terminate the run | the main task dies | ❌ rejected — a bad side-instruction must NOT kill the main task |

## 2. Verified Invariants

### 2.1 The loop drains the inbox at the top of each turn iteration
- **Implementation**: `loop.py` `_run_turns` drain block (after the 3 termination checks, before the between-turns gate) — `if self._message_inbox is not None: for injected in await self._message_inbox.drain(): …`. Ctor `message_inbox: MessageInbox | None = None` (TYPE_CHECKING import, like 57.98 `VerifierRegistry`).
- **Behavior**: an injection lands at the NEXT turn boundary (it never interrupts an in-flight LLM/tool call). The drain runs every iteration (gated only on `inbox is not None`, NOT on `turn_count`).
- **Verification**: `pytest tests/unit/agent_harness/orchestrator_loop/test_inbox_drain.py::test_injection_lands_at_next_turn_boundary` — asserts the injected text is in turn N+1's LLM request, NOT turn N's, + a `MessageInjected` event fires.
- **Test fixture**: `ScriptedInbox([[], [Message(role="user", content="…")]])` (drains nothing on turn 0's top, the note on turn 1's top) + `CapturingChatClient` (records `request.messages` per call).

### 2.2 `message_inbox=None` is byte-identical
- **Implementation**: the `if self._message_inbox is not None` guard.
- **Verification**: `pytest …::test_no_inbox_yields_no_message_injected` (no `MessageInjected`); reinforced by the full existing loop suite (199 passed) which never passes an inbox.

### 2.3 An injected message runs the Cat 9 INPUT guardrail; a non-PASS injection is dropped
- **Implementation**: `loop.py` drain block — `if self._guardrail_engine is not None: inj_g = await self._guardrail_engine.check_input(injected_text, …); if inj_g.action != GuardrailAction.PASS: yield GuardrailTriggered(guardrail_type="input", …); continue`.
- **Behavior**: a blocked injection is NOT appended to `messages` (never reaches the LLM); a `GuardrailTriggered(input)` event tells the UI; the run continues.
- **Verification**: `pytest …::test_guardrail_tripping_injection_is_dropped_not_appended` — a `BlockOnKeyword` (GuardrailType.INPUT) on "FORBIDDEN" → no `MessageInjected`, a `GuardrailTriggered(input, block)`, the forbidden text absent from turn 1's request, the run still completes 2 turns.

### 2.4 The cross-request channel is tenant-scoped + bridges the two requests
- **Implementation**: `api/v1/chat/injection_registry.py` `InjectionRegistry` (`dict[tenant_id, dict[session_id, asyncio.Queue[Message]]]`); `register`/`put`(put_nowait)/`drain`(get_nowait loop)/`unregister`(prune). `router.py` registers at chat-POST start + unregisters in the stream `finally`.
- **Verification**: `pytest tests/unit/api/v1/chat/test_injection_registry.py` (9) — register/put/drain/unregister + FIFO + cross-tenant put rejected + two-tenants-same-sid independence + prune + `QueueMessageInbox` delegation.

### 2.5 `POST /{id}/inject` is auth + tenant + active-session gated
- **Implementation**: `router.py` `inject_message` — `Depends(get_current_tenant)` + `SessionRegistry.get(current_tenant, session_id)` → 404 (absent/cross-tenant — the 鐵律), 409 (not-running / no-live-queue), 202 (`put`). `InjectRequestBody(message, min 1 / max 4096)`.
- **Verification**: `pytest tests/unit/api/v1/chat/test_router.py::TestInjectEndpoint` (6) — 202+queued / 404 missing / 404 cross-tenant / 409 completed / 409 no-live-queue / 422 empty. Risk Class C: a `_reset_injection_registry` autouse fixture; sync seeding by direct dict avoids the cross-loop lock bind (`put_nowait`/`get_nowait` are loop-agnostic).

### 2.6 Drive-through (the live-path verification — the one end-to-end gate)
- **Method**: real UI (`/chat-v2`, real_llm) + real backend (CLEAN restart — Risk Class E) + real Azure → a multi-turn tool-using run → mid-run type an instruction → **Inject** → the next turn acknowledges + incorporates it + the injected `UserTurn(injected)` appears; PLUS inject content that trips the input guardrail → dropped + `GuardrailTriggered`.
- **Result**: see §2.6 in progress.md Day-3 (observed-vs-intended + screenshots `artifacts/dt57101-*.png`).

## 3. Cross-Category Contracts

- **`MessageInbox`** (Cat 1) — `_contracts/inbox.py`; `async def drain(self) -> list[Message]`. Registered at `17-cross-category-interfaces.md` §2.1 (contracts table). The loop depends on the ABC; the chat backing is `QueueMessageInbox` (`injection_registry.py`); B2 will provide a TEAMMATE-mailbox backing — same ABC.
- **`MessageInjected`** (Cat 1 event) — `_contracts/events.py`; `text: str`. Wire type `message_injected` = `{text}` (count 23→24). Registered at `17-cross-category-interfaces.md` §4.1 (LoopEvent table). Codegen: `event_wire_schema.py` → `loopEvents.generated.ts` (`MessageInjectedEvent`).

## 4. Open Invariants (deferred — NOT verified in this spike)

- [ ] **B2 TEAMMATE backing** — the `MessageInbox` ABC is built for reuse, but the child-loop-inbox-backed-by-parent-mailbox path is B2 (NOT wired here).
- [ ] **echo_demo injection** — the FE gates the Inject affordance to real_llm (`canInject = isRunning && mode==="real_llm"`); the echo handler does NOT wire an inbox (a scripted 2-turn mock cannot act on a mid-run note). echo-mode mid-run injection is intentionally NOT supported.
- [ ] **Pause-on-injection** — a blocked injection is dropped, not paused (HITL pause-on-injection is a follow-on).
- [ ] **Persistence** — the inject queue is in-memory, per-run (the mailbox precedent); durable injection across a resume is a follow-on.
- [ ] **Per-tenant injection policy** (rate-limit / disable) — workflow C (C3).
- [ ] **Optimistic FE echo** — the injected message renders on the `message_injected` drain event (proof it landed), NOT on the POST returning.

## 5. Rollback / Fallback

- **If the design proves wrong**: revert the Sprint 57.101 commits. The loop change is gated `if self._message_inbox is not None` — passing `message_inbox=None` (or reverting the `handler.py` wiring line) makes the loop byte-identical to pre-57.101 WITHOUT reverting the contract/event/registry. The `POST /{id}/inject` route + the codegen are additive; removing the route + reverting the wire-schema entry (re-run codegen) restores the 23-event wire.
- **Sentinel / fallback already in place**: yes — `message_inbox=None` is the dormant default; the FE `canInject` gate means the Inject affordance never appears unless a real_llm run is live.
- **Estimated rollback effort**: ~30 min (revert the handler wiring line for an immediate no-op; full revert ~1 hr including the codegen regen).

## 6. References

- Sprint plan: `phase-57-frontend-saas/sprint-57-101-plan.md`
- Sprint checklist: `phase-57-frontend-saas/sprint-57-101-checklist.md`
- Sprint progress + retrospective: `agent-harness-execution/phase-57/sprint-57-101/{progress,retrospective}.md`
- Proposal: `claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.2 / §2.6
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-068-between-turns-injection-primitive.md`
- Contracts: `17-cross-category-interfaces.md` §2.1 (`MessageInbox`) + §4.1 (`MessageInjected`)
- Related: `04-anti-patterns.md` AP-6 (no speculative abstraction — the ABC has a real B2 consumer) / `.claude/rules/multi-tenant-data.md` (tenant-scoped channel)

## Modification History

- 2026-06-11: Initial extract from Sprint 57.101 closeout (Day 4) — B1 between-turns injection primitive
