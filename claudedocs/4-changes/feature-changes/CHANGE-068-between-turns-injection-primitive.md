# CHANGE-068: between-turns message injection primitive (B1)

**Change Date**: 2026-06-11
**Change Type**: New Feature
**Sprint**: 57.101
**Scope**: Cat 1 (Orchestrator) × Cat 12 (Observability/wire) × Cat 9 (Guardrails) × Frontend (chat-v2)
**Status**: ✅ Completed (code + gates green; drive-through PASS both DoD cases)

## Change Summary

A chat-v2 user can now send a **supplementary instruction mid-run** — the running agent picks it up at the next turn boundary. This is the harness-deepening proposal's B1 slice (`claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.2): one loop primitive (`MessageInbox`) that serves both this chat live-injection payoff (cc-parity C-class #3) and the future B2 TEAMMATE parent→child track (same drain seam, different backing).

## Change Reason

Before this change the chat-v2 composer was **hard-disabled during a run** (`InputBar.tsx` `disabled={isRunning}` + the send guard) — there was no way to talk to the agent mid-run; the only mid-run affordance was Stop. The agent could not receive a "also check X" while already working.

## Detailed Changes

### The primitive + the loop drain (Cat 1)
- **NEW `_contracts/inbox.py`** — `MessageInbox` ABC (`async def drain(self) -> list[Message]`). Provider-neutral (imports only `Message`). The loop depends on the ABC, not a concrete backing.
- **`orchestrator_loop/loop.py`** — ctor +`message_inbox: MessageInbox | None = None`; `_run_turns` drains it at the **top of each iteration** (the 57.92 between-turns seam), so an injection lands at the **next turn boundary** (it never interrupts an in-flight LLM/tool call — that would be a lie about what the loop can do). `message_inbox=None` is byte-identical to pre-57.101.
- **D-DAY1-1 (load-bearing correction)**: the proposal assumed draining before the between-turns guardrail makes the injection "Cat 9-checked for free". Reality: that gate checks turn **OUTPUTS** (`_latest_output_text` skips `role="user"` messages). The injection is an **INPUT**, so each drained message runs `engine.check_input`; a non-PASS injection is **DROPPED** (not appended) + a `GuardrailTriggered(input)` event tells the UI, and the run continues without it (a bad side-instruction must not kill the main task).

### The wire event (Cat 12)
- **`_contracts/events.py`** +`MessageInjected(text)` (Cat 1 event; fired on drain — proof it landed in the loop, not when the POST returned).
- **`api/v1/chat/sse.py`** +serializer branch; **`event_wire_schema.py`** +`"message_injected": {"text":"string"}` (count 23→24); **codegen** regenerates `loopEvents.generated.ts` (+`MessageInjectedEvent`). NEW event TYPE → the count moved 23→24 (parity test + `eventSchema.generated.test.ts`).

### The cross-request channel + API (Cat 1 / api)
- **NEW `api/v1/chat/injection_registry.py`** — `InjectionRegistry` (module singleton, tenant-scoped `dict[tenant, dict[session, asyncio.Queue[Message]]]`, mirroring `SessionRegistry`; a per-request mailbox cannot bridge the SEPARATE inject-POST + run requests) + `QueueMessageInbox(MessageInbox)`.
- **`router.py`** — register the queue at chat-POST start, unregister in the stream `finally`; NEW `POST /{session_id}/inject` (202) — auth + active+owner gate via `SessionRegistry.get` (404 absent/cross-tenant, 409 not-running / no-live-queue) → `put(Message(role="user", content=body.message))`. `InjectRequestBody(message, min 1 / max 4096)`.
- **`handler.py`** — `build_real_llm_handler` wires `QueueMessageInbox` into the loop (real_llm only; echo_demo is a scripted mock).

### Frontend (chat-v2)
- **`chatService.ts`** `injectMessage(sessionId, message)` (plain POST; the open run stream delivers `message_injected`). **`useLoopEventStream.ts`** `inject(text)` (valid only while running; failure → setError, run unaffected).
- **`InputBar.tsx`** — composer usable mid-run for **real_llm only** (`canInject = isRunning && mode==="real_llm"` — gating echo_demo avoids a dead control per the Drive-Through rule): textarea enabled, a mid-run send routes to `inject()`, a labelled **Inject** button next to Stop.
- **`chatStore.ts`** `message_injected` → a `UserTurn(injected: true)`; **`types.ts`** `UserTurn` +`injected?`; **`UserTurn.tsx`** an "injected mid-run" tag (reuses `.route-pill`, no new HEX/oklch).

## Modified Files List

Backend (NEW): `_contracts/inbox.py`, `api/v1/chat/injection_registry.py`. Backend (EDIT): `_contracts/events.py`, `_contracts/__init__.py`, `orchestrator_loop/loop.py`, `api/v1/chat/{sse,event_wire_schema,router,handler,schemas}.py`, `scripts/codegen/generate_event_schemas.py`. Frontend: `chat_v2/services/chatService.ts`, `chat_v2/hooks/useLoopEventStream.ts`, `chat_v2/components/InputBar.tsx`, `chat_v2/components/turns/UserTurn.tsx`, `chat_v2/store/chatStore.ts`, `chat_v2/types.ts`, `chat_v2/generated/{loopEvents.generated.ts,events.json}` (codegen). Tests: `test_inbox_drain.py` (NEW), `test_injection_registry.py` (NEW), `test_router.py` (+TestInjectEndpoint), `test_sse.py`, `test_event_wire_schema_parity.py`; `InputBar.test.tsx` (NEW), `chatStore.mergeEvent.test.ts`, `eventSchema.generated.test.ts`.

## Test Checklist

- [x] backend mypy `src` 0/355 + flake8 `src tests` clean + `run_all` 10/10 (check_event_schema_sync / check_ap1 / check_llm_sdk_leak green)
- [x] backend new tests: inbox-drain (3) + injection-registry (9) + inject-endpoint (6) + sse + parity(24)
- [x] backend full pytest **2320 passed + 4 skipped** (+20, 0 deletions); 98.9s
- [x] frontend build (tsc) + Vitest 787 (+5) + lint (no --silent) + check:mockup-fidelity 53 unchanged
- [x] **drive-through PASS** (real UI + Azure gpt-5.2): Case A mid-run inject → agent checks checkout db pool + mentions it (injected UserTurn tag visible); Case B "approval required" inject → dropped + `guardrail_triggered input→escalate`, run continues. artifacts/dt57101-{A,B}.png

## Related

- `claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.2 (B1), §2.6 (DoD)
- `docs/03-implementation/agent-harness-planning/26-between-turns-injection-design.md` (design note)
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` (MessageInbox + message_injected registration)
- Carryover: **B2 TEAMMATE** reuses the `MessageInbox` ABC (child-loop inbox backed by the parent mailbox)
