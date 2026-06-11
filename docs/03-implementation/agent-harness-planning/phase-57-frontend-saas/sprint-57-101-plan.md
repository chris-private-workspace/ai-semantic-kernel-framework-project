# Sprint 57.101 Plan — between-turns message injection primitive (B1: a user can send a supplementary instruction MID-RUN; it drains at the next turn boundary, is guardrail-checked, and the agent picks it up the next turn — one primitive, designed so B2 TEAMMATE parent→child reuses the same drain seam)

**Purpose**: The harness-deepening proposal (`claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.2) identifies a single loop primitive that closes two gaps at once: cc-parity C-class #3 **live message injection** (the user wants to add an instruction while the agent is already running) and the B2 TEAMMATE track (parent wants to message a long-lived child mid-task) are **the same between-turns drain seam**. B1 builds that primitive for the chat live-injection payoff (B2 wires TEAMMATE onto it later). Today the chat-v2 composer is **hard-disabled during a run** (`InputBar.tsx:169 disabled={isRunning}` + the `:79` send guard) — there is no way to talk to the agent mid-run; the only mid-run affordance is Stop. This slice: (1) a provider-neutral Cat 1 contract `MessageInbox` (one method `drain()`), optionally injected into the loop; (2) the loop drains the inbox at the **top of each turn iteration in `_run_turns`** (the 57.92 between-turns seam) — **before** the between-turns guardrail, so injected content is Cat 9-checked for free — appends each as a `user` `Message`, and emits a new `MessageInjected` SSE event (honest "it landed at this turn boundary" semantics, matching CC's drain-at-flush-point); (3) a module-level `InjectionRegistry` (a singleton keyed by `session_id`, like the existing `SessionRegistry` — the inject POST and the streaming run are **separate HTTP requests**, so a per-request mailbox cannot bridge them) backs a `QueueMessageInbox`; (4) `POST /api/v1/chat/{session_id}/inject` (auth + tenant + session-active gated) puts a message on the queue; (5) the chat-v2 composer stays usable mid-run → a mid-run send routes to `inject()` (NOT `send()`, which would start a new run); the injected message renders in the timeline as a `UserTurn` (tagged injected) when the `message_injected` event arrives (rendered on drain, not optimistically — it proves the message actually landed in the loop, not just that the POST returned). This is a **new-domain loop spike** (touches `_run_turns` control flow + a new Cat 1 contract + a NEW SSE event TYPE → codegen + count bump 23→24) → it gets a **design note** (the 57.94/97/98 new-domain-spike precedent); record = CHANGE-068 + design note 26 + update `17-cross-category-interfaces.md` (the new `MessageInbox` contract + the `message_injected` wire). TEAMMATE wiring is explicitly **B2** (out of scope here); B1 only proves the chat live-injection payoff but builds the `MessageInbox` ABC so B2 reuses it.

**Category / Scope**: Cat 1 (Orchestrator — new `MessageInbox` contract + `_run_turns` drain seam) × Cat 12 (Observability/wire — new `MessageInjected` event + codegen, count 23→24) × Cat 9 (Guardrails — injected content rides through the existing between-turns guardrail for free) × Frontend (chat-v2 — composer usable mid-run + inject client + `message_injected` → `UserTurn` render). Backend new files: `_contracts/inbox.py` (`MessageInbox` ABC), `api/v1/chat/injection_registry.py` (`InjectionRegistry` singleton + `QueueMessageInbox`). Backend edits: `_contracts/events.py` (+`MessageInjected`), `orchestrator_loop/loop.py` (ctor +`message_inbox`; `_run_turns` drain seam), `api/v1/chat/sse.py` (+serializer branch), `api/v1/chat/event_wire_schema.py` (+`message_injected`, count→24), `api/v1/chat/router.py` (+`POST /{id}/inject` + register/unregister the queue), `api/v1/chat/handler.py` (construct `QueueMessageInbox`, pass to the loop). Frontend: `chat_v2/services/chatService.ts` (+`injectMessage`), `chat_v2/hooks/useLoopEventStream.ts` (+`inject`), `chat_v2/components/InputBar.tsx` (composer usable mid-run → inject), `chat_v2/store/chatStore.ts` (+`message_injected` case → `UserTurn`), `chat_v2/types.ts` (`UserTurn` +`injected?`), `chat_v2/generated/loopEvents.generated.ts` (codegen regen), the `UserTurn` render component (injected tag). Phase 57.101

**Created**: 2026-06-11
**Status**: Draft (scope below; code execution gated on Day-0 GO — Day-0 Explore recon already run inline, findings in §0)
**Source**: `claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.2 (B1) + §2.6 (DoD) + §4.2 (slice #3) + `next-phase-candidates.md` (B1 carryover). User selected B1 as the next slice (2026-06-11).

> **Modification History**
> - 2026-06-11: Initial creation — between-turns injection primitive; `MessageInbox` Cat 1 contract + `_run_turns` drain seam (before the between-turns guardrail) + module-level `InjectionRegistry` + `POST /{id}/inject` + new `MessageInjected` wire event (codegen, count 23→24) + chat-v2 composer-usable-mid-run → inject + `UserTurn(injected)` render; new-domain spike → design note 26; CHANGE-068 + 17.md. TEAMMATE wiring = B2 (out of scope).

---

## 0. Background

The harness-deepening proposal's収斂洞察 2: TEAMMATE multi-turn ("parent mid-task messages child") and the C-class "user mid-run adds an instruction" are the **same loop primitive** — drain a message inbox at the between-turns seam (57.92 opened it). Build it once, two payoffs. B1 = the chat live-injection payoff + the reusable `MessageInbox` ABC; B2 = TEAMMATE onto it.

The honest delivery semantics (the proposal §2.2): the loop is usually blocked inside an LLM call or a tool exec when an injection arrives; the injection lands at the **next turn boundary** (it cannot interrupt an in-flight LLM call — that would be a lie about what the loop can do). Draining at the top of `_run_turns`, **before** the between-turns guardrail, means injected content is Cat 9-checked for free (a between-turns ESCALATE on an injected instruction pauses durably, same as any other) — that is the "free safety composition" the proposal calls out.

### Ground truth (Day-0 head-start — Explore recon, file:line anchors on `main` post-57.100-merge `71336195`)

A read-only recon mapped the real code; Day-0 Prong 1/2/3 re-confirm these exactly:

- **The between-turns seam — `orchestrator_loop/loop.py:1944-1983` + `:2020-2034`.** `async def _run_turns(...)` (the re-enterable method 57.89/90/98/99 share) starts its `while True:` at `:1983`. The between-turns guardrail check `_cat9_between_turns_check()` runs at `:2022`, gated `turn_count > 0 and not skip_between_turns_once` at `:2020`; `skip_between_turns_once` resets at `:2034`. → drain the inbox at the TOP of the loop body (before `:2020`), append drained messages, then the existing guardrail runs over the appended context. The drain runs every iteration (gated only on inbox presence, NOT on `turn_count`), so an injection during turn 1 lands at the turn-1→2 boundary.
- **The message-append precedent — `loop.py:2490-2493`.** After a verify-fail correction, `messages.append(Message(role="assistant", content=parsed.text))` + `messages.append(Message(role="user", content=verdict.correction_block or ""))`. → injected messages append the same way (`Message(role="user", content=<injected text>)`).
- **The ctor optional-dep DI pattern — `loop.py:373-431` + `:470-483`.** `AgentLoopImpl.__init__` takes `guardrail_engine: GuardrailEngine | None = None` (`:397`) + `verifier_registry: VerifierRegistry | None = None` (`:420`, the 57.98 precedent); assigns `self._guardrail_engine`/`self._verifier_registry` (`:470`/`:480`); guards `if self._guardrail_engine is None: return` (`:1293`). → add `message_inbox: MessageInbox | None = None`; `self._message_inbox`; `if self._message_inbox is None: skip drain`.
- **The `Message` contract — `_contracts/chat.py:75-96`.** frozen dataclass; `role: Literal["system","user","assistant","tool"]`, `content: str | list[ContentBlock]`, `metadata: dict[str,Any] = field(default_factory=dict)`. → `Message(role="user", content=<text>)`.
- **The new-contract home — `_contracts/` (15 files).** `hitl.py` / `verification.py` / `subagent.py` hold small ABCs/Protocols. → new `_contracts/inbox.py` with `MessageInbox` (one method `async def drain(self) -> list[Message]`).
- **The event count — `event_wire_schema.py` WIRE_SCHEMA = 23 entries; `test_event_wire_schema_parity.py:142` `assert len(WIRE_SCHEMA) == 23`.** (57.96 added `subagent_child` 22→23; some doc comments still say "22" — STALE, see §8.) → adding `message_injected` makes it **24**; bump the assertion + the WIRED_EVENT_INSTANCES set + the doc count comments in `event_wire_schema.py` (the file I'm editing) and `_contracts/events.py`.
- **The event base + subclasses — `_contracts/events.py:57-64` (`LoopEvent` base, frozen) + subclasses `:69+`.** e.g. `LoopStarted(session_id)`, `ApprovalRequested(...)`. → add `MessageInjected(LoopEvent)` with `text: str = ""`.
- **The codegen — `scripts/codegen/generate_event_schemas.py` (`WIRE_TYPE_TO_INTERFACE` map) → `events.json` + `frontend/src/features/chat_v2/generated/loopEvents.generated.ts`.** Parity guarded by `test_event_wire_schema_parity.py` + `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` + `scripts/lint/check_event_schema_sync.py` (in `run_all.py`). → add `"message_injected": "MessageInjectedEvent"` to the interface map; run the generator.
- **The sse serializer — `api/v1/chat/sse.py`** (the `ApprovalRequested` branch lives `:229-238`). → add a `MessageInjected` branch emitting `{"type":"message_injected","data":{"text":event.text}}`.
- **The router — `api/v1/chat/router.py:148-350` (chat POST; registers `get_default_registry().register(current_tenant, session_id)` at `:273-274`) + `:832-886` (resume) + `:807-829` (`_stream_resume_events`).** Auth `Depends(get_current_tenant)` (`:151`). `SessionRegistry` (module-level, `session_registry.py`, `get_default_registry()`) tracks active `(tenant, session_id)`. → NEW `POST /{session_id}/inject` (auth + tenant + session-active gated via the SessionRegistry) puts onto a NEW `InjectionRegistry` queue; register the queue at run start (alongside `:273-274`), unregister in the stream `finally`.
- **The mailbox (B2 reference, NOT used in B1) — `subagent/mailbox.py:46-100`.** `MailboxStore._queues: dict[UUID, dict[str, asyncio.Queue[Message]]]`; **per-request** ("no state survives across requests"). → cannot bridge the inject POST (a separate request) ⇒ B1 needs a **module-level** `InjectionRegistry` (the SessionRegistry shape). B2 will give the child loop a `MessageInbox` backed by the parent's mailbox channel — same ABC, different backing.
- **The handler — `api/v1/chat/handler.py:247-259` (`build_real_llm_handler`) + `:514-572` (`build_handler` dispatcher).** constructs `AgentLoopImpl(...)` with optional deps; has `session_id`/`tenant_id`. → construct `QueueMessageInbox(get_default_injection_registry(), session_id)` and pass `message_inbox=` to the loop.

### Frontend ground truth

- **The production composer — `chat_v2/components/InputBar.tsx`** (NOT `Composer.tsx`, which is mockup-only disabled scaffolding `:50-56`, unused by `chat-v2/index.tsx`). The blockers: `:169 disabled={isRunning}` (textarea) + `:77-82 if (!trimmed || isRunning) return;` (send guard) + the send button shows **Stop** when `isRunning` (`:178-188`). → mid-run: keep Stop; enable the textarea; a mid-run send routes to `inject()`.
- **The stream client — `chat_v2/services/chatService.ts:64-92` (`streamChat` POST `/api/v1/chat/`) + `:107-131` (`resumeChat` POST `/{id}/resume`) + `:140+` (`consumeSSEStream`).** The SSE stream stays open until `loop_end`. → add `injectMessage(sessionId, text)` POST `/{id}/inject` (a side POST; the OPEN stream picks up `message_injected` — no new stream).
- **The hook — `chat_v2/hooks/useLoopEventStream.ts:60-92 (send) / :98-120 (resume) / :127 (isRunning = status==="running")`.** → add `inject(text)` calling `injectMessage(sessionId, text)`.
- **The store — `chat_v2/store/chatStore.ts:298-620 (mergeEvent switch)`** (e.g. `loop_start :302`, `turn_start :324` pushes `AgentTurn`, `approval_requested :454-491`). → new `message_injected` case appends a `UserTurn` (with `injected: true`).
- **The types — `chat_v2/types.ts:123-128` (`UserTurn {role,id,at,text}`) + the generated re-export.** → `UserTurn` +`injected?: boolean`; codegen adds `MessageInjectedEvent`.
- **The render — the `UserTurn` render in TurnList** (Day-0 locate the exact component) → show an "injected" tag when `turn.injected`.
- **Tests — `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` + `eventSchema.generated.test.ts`** exist → EXTEND (the 57.100 D-DAY0-2 lesson); NO InputBar component test exists → NEW.
- **GREENFIELD**: no existing inject / mid-run-send pattern.

### STALE anchors flagged by recon (fix the ones in files I edit)

- `event_wire_schema.py` count comments say "22" in places (`:40` "no new wire-type; 22 unchanged") — actual is 23 since 57.96. Since I edit this file to add the 24th entry, I correct its count comments to 24. The `_contracts/events.py` subclass-count comment likewise gets bumped. Unrelated stale comments in files I do NOT edit → noted, not touched (Karpathy §3).

---

## 1. Sprint Goal

Make a chat-v2 user able to inject a supplementary instruction mid-run and see the agent pick it up the next turn: (1) a Cat 1 `MessageInbox` ABC (`_contracts/inbox.py`, one method `drain()`); (2) the loop drains it at the top of `_run_turns` (before the between-turns guardrail), appends each drained message as a `user` `Message`, and yields a `MessageInjected` event (new wire type, codegen 23→24); (3) a module-level `InjectionRegistry` + `QueueMessageInbox` bridge the inject POST and the streaming run; (4) `POST /api/v1/chat/{session_id}/inject` (auth + tenant + active-session gated) queues the message; (5) the chat-v2 composer stays usable mid-run — a mid-run send calls `inject()` (not `send()`); the `message_injected` event renders the injected text as a `UserTurn(injected)` in the timeline. Tests: the inbox drains at the next turn boundary + the drained content passes through the between-turns guardrail; the inject endpoint is tenant-safe (404 cross-tenant, 409 not-running); the wire carries `message_injected`; the store renders the `UserTurn`; the mid-run composer routes to inject (not a new run). **Drive-through**: real UI + backend + Azure — start a multi-turn investigation, mid-run inject "also check X", watch the next turn acknowledge + incorporate it, and the injected message appears in the timeline; plus the guardrail-on-injected case (inject content that trips the between-turns guardrail → pause/block). Out of scope: TEAMMATE wiring (B2 — the child-loop inbox backing); detached long-lived teammates; injection during a HITL pause (the loop is paused, not running — inject is rejected 409); optimistic echo (render on drain, not on POST — honesty); editing/cancelling a queued injection.

---

## 2. User Stories

- **US-1 (the `MessageInbox` contract + loop drain seam)** — As the orchestrator, I want an optional message inbox I drain at each turn boundary, so a mid-run instruction joins the conversation at the next turn without interrupting an in-flight call. → `_contracts/inbox.py` `MessageInbox` (ABC, `async def drain(self) -> list[Message]`); `loop.py` ctor +`message_inbox: MessageInbox | None = None`; `_run_turns` drains at the top (before the between-turns guardrail `:2022`), appends each as `Message(role="user", …)`, yields `MessageInjected(text=…)`.
- **US-2 (the `MessageInjected` wire event)** — As the chat-v2 UI, I want to know when an injection actually landed in the loop. → `_contracts/events.py` +`MessageInjected(text)`; `event_wire_schema.py` +`"message_injected": {"text":"string"}` (count 23→24); `sse.py` +serializer branch; codegen regen (`loopEvents.generated.ts` gains `MessageInjectedEvent`; `test_event_wire_schema_parity.py:142` →24 + a wired instance).
- **US-3 (the injection channel + API)** — As a user with an active session, I want to POST a mid-run instruction. → `api/v1/chat/injection_registry.py` `InjectionRegistry` (module singleton, `dict[UUID, asyncio.Queue[Message]]`) + `QueueMessageInbox(MessageInbox)`; `router.py` `POST /{session_id}/inject` (auth `get_current_tenant` + active-session check via `SessionRegistry` → 404 cross-tenant / 409 not-running) puts onto the queue + registers/unregisters the queue around the run; `handler.py` constructs the inbox + passes it to the loop.
- **US-4 (the composer usable mid-run)** — As a user, I want to type + send while the agent is running. → `InputBar.tsx`: the textarea is enabled during a run; a mid-run send routes to `inject()` (NOT `send()`, which would start a new run); the Stop button stays; the affordance is clearly labelled (so the user understands mid-run send = a note to the running agent, not a new turn). `chatService.injectMessage` + `useLoopEventStream.inject`.
- **US-5 (the injected message renders)** — As a user, I want to see my injection in the timeline once it lands. → `chatStore.ts` `message_injected` case appends a `UserTurn` (`injected: true`) on the drain event (not optimistically); `types.ts` `UserTurn` +`injected?: boolean`; the `UserTurn` render shows an "injected" tag.
- **US-6 (drive-through — mid-run injection + guardrail-on-injected)** — As the user, I want to SEE the agent pick up my mid-run instruction. → drive-through (real UI + backend + Azure): a multi-turn run → mid-run inject "also check X" → the next turn acknowledges + incorporates it + the injected `UserTurn` appears; AND inject content that trips the between-turns guardrail → the guardrail acts on it (pause/block). Screenshot + observed-vs-intended in progress.md. (No "gate-only" claimed.)

---

## 3. Technical Specifications

### 3.0 Architecture (one drain seam; the inject POST and the run are separate requests bridged by a module registry)

```
RUN REQUEST (open SSE stream)                 INJECT REQUEST (separate POST)
  POST /api/v1/chat/  ──► loop.run()            POST /api/v1/chat/{id}/inject
   handler builds QueueMessageInbox(reg, sid)    auth + tenant + active-session(SessionRegistry)
   register reg[sid] = Queue()                   reg[sid].put(Message(role="user", content=msg))  ──┐
   loop._run_turns:                                                                                  │
     while True:                                                                                     │
       drained = await inbox.drain()  ◄───────────────────────────────────────────────────────────┘ (next turn boundary)
       for m in drained:
         messages.append(m); yield MessageInjected(text=m.content)
       _cat9_between_turns_check()   # injected content guardrail-checked for free
       ... LLM call (now sees the injected instruction) ...
   stream finally: unregister reg[sid]

FRONTEND
  InputBar: isRunning ? inject(text) : send(text)     # textarea enabled mid-run; Stop stays
  open stream receives message_injected ──► chatStore appends UserTurn(injected) ──► timeline tag
```

The drain runs **every** iteration top (gated only on `inbox is not None`, not on `turn_count`), so an injection during turn N lands at the N→N+1 boundary. The injected message is appended **before** the between-turns guardrail, so Cat 9 sees it. `message_inbox is None` (echo path, tests without an inbox) → the loop is byte-identical to today.

### 3.1 The `MessageInbox` contract + loop drain (US-1)
- `backend/src/agent_harness/_contracts/inbox.py` — NEW. `class MessageInbox(ABC)` with `@abstractmethod async def drain(self) -> list[Message]` ("return all currently-queued messages non-blocking; `[]` if none"). Provider-neutral (imports only `Message`). File header per convention.
- `backend/src/agent_harness/orchestrator_loop/loop.py`:
  - ctor: +`message_inbox: "MessageInbox | None" = None` (after `verifier_registry`); `self._message_inbox = message_inbox`.
  - `_run_turns` top of the `while` body (before the `:2020` between-turns gate): `if self._message_inbox is not None: drained = await self._message_inbox.drain(); for m in drained: messages.append(m); yield MessageInjected(text=<m.content as str>)`. (Guard `content` is a str — inject is always text; coerce/skip non-str defensively.)
  - MHist 1-line on loop.py + the new `MessageInjected` import.
- DoD: `mypy src` 0; a loop unit feeds a stub `MessageInbox` returning a message on the 2nd drain → asserts it appears in `messages` before turn 2's LLM call + a `MessageInjected` event is yielded + the between-turns guardrail saw it. `message_inbox=None` → no behavior change (existing loop tests green).

### 3.2 The `MessageInjected` wire event + codegen (US-2)
- `backend/src/agent_harness/_contracts/events.py` — +`MessageInjected(LoopEvent)` with `text: str = ""`. Bump the subclass-count doc comment.
- `backend/src/api/v1/chat/event_wire_schema.py` — +`"message_injected": {"text": "string"}`; update the count comments (23→24).
- `backend/src/api/v1/chat/sse.py` — +a `MessageInjected` serializer branch → `{"type":"message_injected","data":{"text":event.text}}`.
- `scripts/codegen/generate_event_schemas.py` — +`"message_injected": "MessageInjectedEvent"` in `WIRE_TYPE_TO_INTERFACE`; run it → `events.json` + `loopEvents.generated.ts` regenerate (new `MessageInjectedEvent` interface + union + `KNOWN_LOOP_EVENT_TYPES` 24).
- `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` — `:142` `assert len(WIRE_SCHEMA) == 24` + add a `MessageInjected(text="hi")` wired instance.
- DoD: `python scripts/codegen/generate_event_schemas.py` clean regen (only `message_injected` added); `check_event_schema_sync` green; parity tests green; count 24 everywhere.

### 3.3 The injection channel + API (US-3)
- `backend/src/api/v1/chat/injection_registry.py` — NEW. `InjectionRegistry` (module singleton via `get_default_injection_registry()`, mirroring `session_registry.get_default_registry`): `_queues: dict[UUID, asyncio.Queue[Message]]`; `register(session_id)` (create queue), `put(session_id, message)` (raise/return False if not registered), `drain(session_id) -> list[Message]` (`get_nowait` loop until `QueueEmpty`), `unregister(session_id)`. `class QueueMessageInbox(MessageInbox)` binds `(registry, session_id)` → `drain()` calls `registry.drain(session_id)`. Risk Class C: the singleton needs an autouse reset fixture in the affected test suites.
- `backend/src/api/v1/chat/router.py`:
  - the chat POST: alongside the SessionRegistry `register` (`:273-274`), `get_default_injection_registry().register(session_id)`; in the stream's `finally`, `unregister(session_id)`.
  - NEW `@router.post("/{session_id}/inject", status_code=202)` `async def inject_message(session_id, body: InjectRequestBody, current_tenant = Depends(get_current_tenant), …)`: verify the session is active + owned by `current_tenant` via the SessionRegistry (404 if absent / cross-tenant — the multi-tenant 404-hiding rule; 409 if registered-but-not-running, e.g. paused/completed); `get_default_injection_registry().put(session_id, Message(role="user", content=body.message))`; return `{"status":"queued"}`. A small `InjectRequestBody(BaseModel)` with `message: str` (max length bound, e.g. 4096, mirroring `DecisionRequestBody.reason`).
- `backend/src/api/v1/chat/handler.py` — construct `QueueMessageInbox(get_default_injection_registry(), session_id)` and pass `message_inbox=` into `AgentLoopImpl(...)` (real_llm path; echo path leaves it None or also wires it — decide Day-1, default real_llm only).
- DoD: `mypy src` 0; endpoint tests — 202 on active+owned; 404 cross-tenant; 409 not-running; the put lands on the queue; an autouse reset fixture clears the singleton between tests.

### 3.4 The composer usable mid-run + inject client (US-4)
- `frontend/src/features/chat_v2/services/chatService.ts` — +`injectMessage(sessionId: string, message: string): Promise<void>` → POST `/api/v1/chat/${sessionId}/inject` body `{message}` (auth header as the others; no SSE — a plain POST).
- `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts` — +`inject(text: string)` → `if (!sessionId) return; await injectMessage(sessionId, text)`. Return it alongside `send`/`resume`/`cancel`/`isRunning`.
- `frontend/src/features/chat_v2/components/InputBar.tsx`:
  - the textarea `disabled={isRunning}` (`:169`) → enabled during a run.
  - the send guard (`:77-82`): when `isRunning && trimmed`, call `inject(trimmed)` + clear the input (do NOT call `send`); when `!isRunning && trimmed`, call `send` as today.
  - the affordance: keep the Stop button when running; the Enter key + a clearly-labelled inject action (e.g. a small send icon next to Stop, or a hint) routes to inject. The label/aria must make clear it's a note to the running agent, not a new turn (drive-through honesty). `data-testid="inject-send"` for the mid-run send.
- DoD: a Vitest InputBar test — when `isRunning`, Enter/send calls `inject` (not `send`); when idle, calls `send`. The textarea is interactable during a run.

### 3.5 The injected message renders (US-5)
- `frontend/src/features/chat_v2/types.ts` — `UserTurn` +`injected?: boolean` (optional; absent/false = a normal user message).
- `frontend/src/features/chat_v2/store/chatStore.ts` — NEW `message_injected` case in `mergeEvent`: append a `UserTurn` `{ role:"user", id: nextTurnId(), at: nowIso(), text: ev.data.text, injected: true }`. (Rendered on drain — the event proves it landed; no optimistic echo.)
- the `UserTurn` render component (Day-0 locate, likely `chat_v2/components/turns/UserTurn.tsx` or inline in TurnList) — when `turn.injected`, show a small "injected mid-run" tag (mockup vocab / `var(--*)` tokens — NEW element, no mockup source, stay in design system, no new HEX/oklch → `check:mockup-fidelity` baseline unchanged).
- DoD: a chatStore unit — a `message_injected` event → a `UserTurn` with `injected===true` + the text; the render test (or the existing TurnList test) shows the tag.

### 3.6 What is explicitly NOT done + Lint / neutrality / 17.md / docs
- **NOT done (separate slices)**: TEAMMATE wiring (B2 — the child-loop inbox backed by the parent mailbox; B1 only builds the ABC + the chat backing); detached long-lived teammates; depth>1; injection during a HITL pause (the loop is paused → not "running" → 409, not a drain); optimistic FE echo (render on drain); edit/cancel a queued injection; multi-message batching beyond drain-all; persistence of the inject queue (in-memory, per-run, like the mailbox).
- **Lint / neutrality**: backend `check_llm_sdk_leak` 0 (`inbox.py` imports only `Message`; the registry uses `asyncio` only — no SDK). `check_event_schema_sync` green (codegen regenerated; count 24). `check_ap1` — the drain is a `for m in drained: messages.append` + `yield`; it is NOT a fixed-step pipeline (the loop is still `while True` driven by stop_reason) → confirm the AP-1 detector stays green (the drain is data-flow, not control-flow restructure). Frontend `npm run lint` (NO `--silent` — the 57.40 lesson) + `npm run build` + `npm run check:mockup-fidelity` (the inject affordance + injected tag use mockup vocab + `var(--*)` → baseline unchanged; confirm Day-1).
- **17.md (registration)**: register the new `MessageInbox` Cat 1 contract (owner Cat 1; one method `drain`) + the `message_injected` wire event (Cat 12) + note the loop drains the inbox at the between-turns seam before the Cat 9 guardrail.
- **Design note (YES — new-domain spike)**: per `sprint-workflow.md §Step 5.5`, this introduces a NEW Cat 1 primitive + a new loop control-flow seam + a new wire event (not a continuation of a shipped feature) → **design note 26** (`docs/03-implementation/agent-harness-planning/26-between-turns-injection-design.md`), extracted from the real implementation, passing the 8-point quality gate. Record = CHANGE-068 + design note 26 + update 17.md.

### 3.7 Validation (US-1..US-6)
- **Backend**: `mypy src` 0; `run_all` 10/10 (esp. `check_event_schema_sync` + `check_ap1` + `check_llm_sdk_leak`); `black`/`isort`/`flake8 src/ tests/` clean (run INDEPENDENTLY, FULL scope — the 57.95 + 57.98 CI lessons). `python scripts/codegen/generate_event_schemas.py` → clean regen. pytest:
  - **NEW** `test_inbox_drain.py` (or extend a loop test) — a stub `MessageInbox` returns a message on the 2nd drain → it appears in `messages` before turn 2 + a `MessageInjected` event + the between-turns guardrail saw it; `message_inbox=None` → no change.
  - **NEW** `test_injection_registry.py` — register/put/drain/unregister; `put` on an unregistered session is rejected; autouse reset fixture.
  - **NEW** `test_inject_endpoint.py` (or extend the chat router tests) — 202 active+owned; 404 cross-tenant; 409 not-running.
  - **EDIT** `test_event_wire_schema_parity.py` — count 24 + a `MessageInjected` instance.
  - **EDIT/NEW** an sse-serializer test — `MessageInjected(text="x")` → `{"type":"message_injected","data":{"text":"x"}}`.
  - Full backend suite green (NET delta documented — expect +N, 0 deletions).
- **Frontend**: `npm run lint` (no `--silent`) + `npm run build` + `npm run check:mockup-fidelity` (baseline unchanged) + `npm run test` (Vitest):
  - **EDIT** `eventSchema.generated.test.ts` — regenerated parity (message_injected; count 24).
  - **EDIT** `chatStore.mergeEvent.test.ts` — `message_injected` → `UserTurn(injected:true, text)`.
  - **NEW** `InputBar` test — mid-run send → `inject` (not `send`); idle send → `send`; textarea interactable during a run.
  - The existing chat-v2 e2e/unit contracts preserved (the run/resume/approval flows unchanged — inject is additive).
- **Drive-through** (US-6): real UI + real backend + real Azure — a multi-turn investigation prompt (a tool-using task that runs ≥3 turns) → mid-run type "also check the database connection pool" → inject → the next turn acknowledges + incorporates it + the injected `UserTurn(injected)` appears in the timeline; PLUS inject content that trips the between-turns guardrail (a policy-violating instruction) → the guardrail pauses/blocks it. Screenshot + observed-vs-intended in progress.md. Clean restart first (Risk Class E — the new endpoint + the inbox wiring are read at startup). (Per CLAUDE.md §Drive-Through — "the next turn picks up the injection" is the leg-specific assertion; the composer accepting text alone is gate/probe, not drive-through.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/_contracts/inbox.py` | **NEW** — `MessageInbox` ABC (`async def drain(self) -> list[Message]`). File header. |
| `backend/src/agent_harness/_contracts/events.py` | **EDIT** — +`MessageInjected(LoopEvent)` (`text: str = ""`); bump subclass-count comment. MHist 1-line. |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — ctor +`message_inbox: MessageInbox | None = None`; `_run_turns` drains at the top (before the between-turns guardrail) → append `Message(role="user")` + yield `MessageInjected`. MHist 1-line. |
| `backend/src/api/v1/chat/injection_registry.py` | **NEW** — `InjectionRegistry` (module singleton) + `QueueMessageInbox(MessageInbox)` + `get_default_injection_registry()`. File header. |
| `backend/src/api/v1/chat/sse.py` | **EDIT** — +`MessageInjected` serializer branch. MHist 1-line. |
| `backend/src/api/v1/chat/event_wire_schema.py` | **EDIT** — +`"message_injected": {"text":"string"}`; count comments 23→24. MHist 1-line. |
| `backend/src/api/v1/chat/router.py` | **EDIT** — register/unregister the injection queue around the run; NEW `POST /{session_id}/inject` (auth + tenant + active-session → 404/409) + `InjectRequestBody`. MHist 1-line. |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — construct `QueueMessageInbox` + pass `message_inbox=` to the loop. MHist 1-line. |
| `scripts/codegen/generate_event_schemas.py` | **EDIT** — +`"message_injected": "MessageInjectedEvent"` in `WIRE_TYPE_TO_INTERFACE`. MHist 1-line. |
| `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` + `generated/events.json` | **REGEN** — `python scripts/codegen/generate_event_schemas.py`. Generated — no manual edit. |
| `frontend/src/features/chat_v2/types.ts` | **EDIT** — `UserTurn` +`injected?: boolean`. MHist 1-line. |
| `frontend/src/features/chat_v2/services/chatService.ts` | **EDIT** — +`injectMessage(sessionId, message)`. MHist 1-line. |
| `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts` | **EDIT** — +`inject(text)`. MHist 1-line. |
| `frontend/src/features/chat_v2/components/InputBar.tsx` | **EDIT** — textarea enabled mid-run; mid-run send → `inject` (not `send`); keep Stop; labelled inject affordance (`data-testid="inject-send"`). MHist 1-line. |
| `frontend/src/features/chat_v2/store/chatStore.ts` | **EDIT** — +`message_injected` case → append `UserTurn(injected:true)`. MHist 1-line. |
| `frontend/src/features/chat_v2/components/turns/UserTurn.tsx` (or the TurnList user render — Day-0 locate) | **EDIT** — show an "injected" tag when `turn.injected`. MHist 1-line. |
| `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` | **EDIT** — count 24 + `MessageInjected` instance. |
| `backend/tests/.../test_inbox_drain.py` (loop) | **NEW** — inbox drains at the next turn boundary + guardrail-checked; None = no change. |
| `backend/tests/.../test_injection_registry.py` | **NEW** — register/put/drain/unregister + reset fixture. |
| `backend/tests/.../test_inject_endpoint.py` (or extend router tests) | **NEW/EDIT** — 202 / 404 cross-tenant / 409 not-running. |
| `backend/tests/.../test_*sse*` | **EDIT (light)** — `MessageInjected` serializes. |
| `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` | **EDIT** — regenerated parity (message_injected; count 24). |
| `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` | **EDIT** — `message_injected` → `UserTurn(injected)`. |
| `frontend/tests/unit/chat_v2/**/InputBar*` | **NEW** — mid-run inject vs idle send. |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-101-plan.md` + `-checklist.md` | **NEW** — this plan + checklist. |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-101/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro. |
| `claudedocs/4-changes/feature-changes/CHANGE-068-between-turns-injection-primitive.md` | **NEW** — the change record. |
| `docs/03-implementation/agent-harness-planning/26-between-turns-injection-design.md` | **NEW** — design note 26 (new-domain spike; 8-point gate). |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** — register `MessageInbox` (Cat 1) + `message_injected` wire (Cat 12). |

**NOT in this list (unchanged)**: `subagent/mailbox.py` (B2 reference, not touched) · `TeammateExecutor` (B2) · `resume()` (inject is rejected during a pause, not drained) · DB/migration (the inbox is in-memory, per-run) · `ModelProfile`/`ChatClient` ABC · `ApprovalCard.tsx`/`HITLTurn.tsx` (HITL unchanged).

---

## 5. Acceptance Criteria

- `MessageInbox` ABC (`_contracts/inbox.py`); the loop drains it at the top of `_run_turns` before the between-turns guardrail → appends `user` Messages + yields `MessageInjected`; `message_inbox=None` byte-identical (US-1).
- `MessageInjected` wire type (events.py + event_wire_schema 23→24 + sse serializer + codegen regen + parity tests at 24); clean regen (only `message_injected` added) (US-2).
- `InjectionRegistry` + `QueueMessageInbox` + `POST /{id}/inject` (auth + tenant + active-session → 202 / 404 cross-tenant / 409 not-running); register/unregister around the run; reset fixture (US-3).
- `InputBar` usable mid-run → a mid-run send calls `inject()` (not `send()`); Stop stays; idle send unchanged; `injectMessage` + `inject` (US-4).
- `message_injected` → a `UserTurn(injected:true)` in the timeline with an "injected" tag; `UserTurn` +`injected?` (US-5).
- Backend `mypy src` 0 + `run_all` 10/10 (`check_event_schema_sync` + `check_ap1` + `check_llm_sdk_leak` green) + `black`/`isort`/`flake8 src/ tests/` clean (independent, FULL scope) + full pytest green (NET documented); frontend `lint` (no `--silent`) + `build` + `check:mockup-fidelity` (baseline unchanged) + Vitest green; CHANGE-068 + design note 26 + 17.md.
- **Drive-through PASS**: real UI + backend + Azure → a multi-turn run → mid-run inject → the next turn picks it up + the injected `UserTurn` appears; + the guardrail-on-injected case acts; screenshot + observed-vs-intended. (No "gate-only" claimed.)

---

## 6. Deliverables

- [ ] `MessageInbox` ABC + loop ctor + `_run_turns` drain seam (append + yield `MessageInjected`) (US-1)
- [ ] `MessageInjected` event + event_wire_schema (23→24) + sse serializer + codegen regen + parity 24 (US-2)
- [ ] `InjectionRegistry` + `QueueMessageInbox` + `POST /{id}/inject` (tenant-safe) + register/unregister + handler wiring (US-3)
- [ ] `InputBar` mid-run inject + `injectMessage` client + `useLoopEventStream.inject` (US-4)
- [ ] `chatStore` `message_injected` → `UserTurn(injected)` + `types.ts` `UserTurn.injected?` + the injected tag render (US-5)
- [ ] Tests: backend inbox-drain + injection-registry + inject-endpoint + parity(24) + sse; frontend parity(24) + chatStore + InputBar (US-1..US-5)
- [ ] backend mypy 0 + run_all 10/10 + format chain (independent, FULL scope) + frontend lint(no `--silent`)/build/check:mockup-fidelity/Vitest (validation)
- [ ] **drive-through PASS** (real UI + backend + Azure; multi-turn → mid-run inject → next turn picks up + injected UserTurn; + guardrail-on-injected; screenshot + observed-vs-intended) (US-6)
- [ ] CHANGE-068 + design note 26 + 17.md + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`loop-injection-primitive-spike` (NEW, 0.55) — 1st data point, pending 2-3 sprint validation**. The work is a cross-stack multi-layer feature like Sprint 57.96 (`subagent-child-turnstream-nesting` 0.55: new wrapper event + executor forward + frontend store/render) but with MORE surface: a NEW Cat 1 contract (`MessageInbox`) + a NEW `_run_turns` control-flow seam (the drain — new-domain loop touch, like 57.94/98's 0.60) + a NEW SSE event TYPE (codegen + count bump 23→24, heavier than 57.100's additive field) + a NEW module-level registry + a NEW API endpoint (tenant-safe) + the FE composer-during-run rework (un-disabling the input + routing mid-run send to inject without regressing idle send) + store/render. The work splits: the `MessageInbox` ABC + loop drain seam (~2 hr) / the `MessageInjected` event + event_wire_schema + sse + codegen regen + parity (~2 hr) / the `InjectionRegistry` + `QueueMessageInbox` + inject endpoint (tenant-safe) + register/unregister + handler wiring (~3 hr) / the FE composer-mid-run + inject client + hook + store + render (~3.5 hr) / tests — backend inbox/registry/endpoint/parity/sse, frontend parity/chatStore/InputBar (~3 hr) / drive-through — multi-turn → mid-run inject → next-turn-picks-up + guardrail-on-injected + clean restart (~2.5 hr) / docs — CHANGE-068 + design note 26 (8-point gate) + 17.md + progress + retro (~2.5 hr). Bottom-up ~18.5 hr. Dominant costs = the loop drain correctness (lands at the next boundary, guardrail-checked, None byte-identical) + the inject endpoint tenant-safety + the composer-mid-run UX without regressing idle send + the drive-through (forcing a clean mid-run inject that the next turn provably incorporates). **Agent-delegated: no** (parent-direct) — the loop control-flow seam, the cross-request channel + tenant-safety, the composer-mid-run routing (must NOT regress the idle send / start-a-new-run path), and the drive-through are correctness work the parent must drive. `agent_factor = 1.0`; does NOT extend any AgentDelegated streak.

> Bottom-up est ~18.5 hr → class-calibrated commit ~10 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the wiring ripples wider than the spec'd files (e.g. the codegen regen touches more than `message_injected`; the `_run_turns` drain can't be placed cleanly before the between-turns gate without reordering the resume re-entry; the InjectionRegistry singleton can't be reset without touching multiple suites; the composer-mid-run can't route to inject without a refactor that touches the idle send path; the drive-through can't force a clean mid-run inject the next turn provably picks up), STOP and re-scope rather than rush. This is a larger slice than 57.98-100 — if Day-1 reveals it's two sprints, split (the backend primitive + API as B1a, the FE composer + render as B1b) and re-confirm with the user.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **The drain must land at the next turn boundary, not interrupt an in-flight call** | Drain at the TOP of the `_run_turns` `while` body (before the between-turns gate), NOT inside the LLM/tool await. The injection is honestly "next-turn"; the `MessageInjected` event fires on drain (proof it landed), not on POST. A loop unit asserts the message appears in `messages` before turn N+1's LLM call. |
| **Injected content must be guardrail-checked** | Append the drained messages BEFORE `_cat9_between_turns_check` (`:2022`) so Cat 9 sees them. A drive-through case injects a policy-violating instruction → the between-turns guardrail pauses/blocks. |
| **`message_inbox=None` must be byte-identical** | The drain is gated `if self._message_inbox is not None`. The echo path + all existing loop tests (no inbox) are unchanged; assert the existing loop suite stays green. |
| **The inject POST and the run are SEPARATE requests** | A per-request mailbox (`subagent/mailbox.py`) cannot bridge them → use a MODULE-level `InjectionRegistry` (the `SessionRegistry` precedent). Register the queue at run start, unregister in the stream `finally`. A `put` on an unregistered/closed session is rejected (409 — the run ended). |
| **Tenant safety on `/inject`** | `Depends(get_current_tenant)` + verify the session is active AND owned by `current_tenant` via the SessionRegistry; 404 (not 403) for cross-tenant (the multi-tenant 404-hiding rule); 409 for registered-but-not-running. An endpoint test covers cross-tenant + not-running. |
| **Risk Class C (the InjectionRegistry singleton across test event loops)** | An autouse `reset_injection_registry` fixture in the affected suites (the `session_registry`/`service_factory` reset precedent — `.claude/rules/testing.md` §Module-level Singleton Reset). The new endpoint tests + any loop test using a real registry reset it. |
| **The event count must move 23→24 everywhere** | `event_wire_schema.py` (entry + count comment) + `test_event_wire_schema_parity.py:142` (`== 24`) + the WIRED_EVENT_INSTANCES set + `_contracts/events.py` subclass comment + the regenerated `loopEvents.generated.ts` KNOWN set. `git diff` the generated `.ts` → only `message_injected` added (no spurious reformat). `check_event_schema_sync` green. |
| **The composer-mid-run must NOT regress the idle send / not start a new run** | The mid-run branch calls `inject()` (a plain POST), NOT `send()` (which opens a new stream / pushes a UserMessage / starts a run). A Vitest asserts: `isRunning` → `inject` called, `send` NOT called; idle → `send` called, `inject` NOT. Keep the Stop button. The textarea un-disable is the only change to the idle path's markup. |
| **The injected tag / inject affordance have no mockup source** | NEW elements (no `page-chat.jsx` counterpart) → reuse mockup `.btn`/`.user-turn` vocab + `var(--*)` tokens; do NOT invent colors. `check:mockup-fidelity` HEX_OKLCH baseline unchanged (Day-1 confirm). |
| **AP-1 (the drain is not a pipeline)** | The drain is `for m in drained: append + yield` data-flow at the loop top; the loop is still `while True` driven by stop_reason. Confirm `check_ap1` stays green (no fixed-step restructure). |
| **Risk Class E (stale `--reload` backend masks the new endpoint + wiring)** | Clean restart before the drive-through — the `/inject` route, the `message_inbox` wiring, and the registry are constructed at startup. Kill the uvicorn reloader + the `multiprocessing.spawn` worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime + `Stop-Process -Force`; verify the FRESH PID is the SOLE :8000 owner; do NOT touch the frontend node :3007 / claude-code node). The 57.91-100 streak (10 consecutive). |
| **CI black/lint on the FULL scope (the 57.95 + 57.98 lessons)** | `black --check src/ tests/` (FULL scope) before push; frontend `npm run lint` WITHOUT `--silent` (the 57.40 lesson). |
| **Over-engineering (scope creep into TEAMMATE / edit-queue / optimistic echo / persistence)** | This slice is ONLY: the `MessageInbox` ABC + the loop drain + the `MessageInjected` event + the InjectionRegistry + the inject endpoint + the composer-mid-run + the `UserTurn(injected)` render. NO TEAMMATE wiring (B2), NO queued-injection edit/cancel, NO optimistic echo, NO persistence, NO depth>1 (Karpathy §2/§3). |
| **Smuggling unrelated change** | The diff is exactly the §4 list. `mailbox.py`/`TeammateExecutor`/`resume()`/DB/`ModelProfile`/`HITLTurn.tsx`/`ApprovalCard.tsx` diff = 0. |

---

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **TEAMMATE wiring (B2)** — giving a child loop a `MessageInbox` backed by the parent's mailbox channel. B1 builds the ABC + the chat backing so B2 reuses it; B2 does the TEAMMATE multi-turn (`harness-deepening-proposal §2.3`).
- **Detached long-lived teammates / depth>1** — YAGNI until a real use case (`proposal §2.5`).
- **Injection during a HITL pause** — the loop is paused (not running) → the inject endpoint returns 409; re-injecting into a paused loop is a separate concern (the reviewer note path is already 57.99's REJECT-with-note).
- **Optimistic FE echo** — render the injected message on the `message_injected` drain event (it proves the loop took it), NOT on the POST returning (which would be a Potemkin "it landed" before it did).
- **Edit / cancel a queued injection** — once POSTed, it drains; an edit/cancel UX is a follow-on.
- **Persistence of the inject queue** — in-memory, per-run (the mailbox precedent); durable injection across a resume is a follow-on.
- **Per-tenant injection policy** (rate-limit / disable) — workflow C (C3).
