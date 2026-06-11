# Sprint 57.103 Plan — chat-user inject-to-teammate: a running teammate gets a live message inbox producer + the injected turn surfaces on the Inspector Tree + the inline block goes mode-aware (B2b: the second half of harness-deepening Workflow B slice B2 — B2a wired the teammate's MessageInbox inert "until B2b"; this sprint is that live UI producer)

**Category / Scope**: 範疇 11 (Subagent Orchestration) × 範疇 1 (loop drain seam, reused) × 範疇 12 (event relay) × Frontend — Phase 57 / Sprint 57.103
**Created**: 2026-06-11
**Status**: Draft
**Plan authority**: mirrors the most-recent completed sprint plan (`sprint-57-102-plan.md`, 9 sections 0-9). Scope differences expressed through content, not structure.

> **Modification History**
> - 2026-06-11: Initial draft (B2b — inject-to-teammate live producer + relay the injected child turn + inline block mode-awareness)

---

## 0. Background

Sprint 57.102 (B2a) made TEAMMATE a real multi-turn child loop and **wired** a `MessageInbox` on the child (`TeammateExecutor._inbox_factory` → `QueueMessageInbox` keyed by `subagent_id`), but with **no live producer** — the child's inbox drains an empty/never-registered queue, so it is inert in production ("the live producer = B2b", `teammate.py:106-110`). This sprint is that producer: a chat user injects a message into a RUNNING teammate, the teammate drains it at its next turn boundary, and the injected turn surfaces on the Inspector Tree node so it is visible (drive-throughable). It also closes the 57.102 🟢 carryover: the inline `SubagentForkBlock` mislabels a teammate spawn as "Fork · concurrent / {turns}t".

This reuses three proven assets and adds NO new wire event TYPE:
- **B1 (57.101)** `InjectionRegistry` (cross-request queue, keyed by tenant + a UUID) + `QueueMessageInbox` + the `POST /chat/{id}/inject` endpoint pattern (the new endpoint is a sibling).
- **B2a (57.102)** the teammate child loop with `message_inbox=inbox` already wired + the `inbox_factory` seam built FOR this sprint.
- **57.96** the `SubagentChildEvent` relay (the child's TAO subset → Inspector Tree node). B2b adds ONE type (`MessageInjected`) to the relayed subset; no new event type, no codegen, no event-count bump.

### Ground truth (Day-0 head-start — 3 Explore recon agents + personal re-read of the 3 load-bearing files, file:line anchors on `main` HEAD `0209c672` post-57.102-merge)

- **`InjectionRegistry.put()` does NOT auto-create a queue** — `injection_registry.py:73-82`: returns `False` when `(tenant, key)` has no registered queue. So a queue MUST be `register()`-ed before `put()` can succeed. (Resolves a recon contradiction; this is the load-bearing fact for US-2.)
- `InjectionRegistry.register/drain/unregister` — `injection_registry.py:68-107`, keyed by `(tenant_id, UUID)`. `register` is idempotent (`setdefault`). The B1 parent run registers its own queue at run start + unregisters in the router SSE finally.
- `QueueMessageInbox(registry, tenant_id, key)` — `injection_registry.py:115-124`; `drain()` delegates to `registry.drain(tenant, key)`. The key is generic (session OR subagent UUID) — no shape change needed for B2b.
- `B1 inject endpoint` — `router.py:844-878`: `inject_message(session_id, body: InjectRequestBody, current_tenant=Depends(get_current_tenant))`; `get_default_registry().get(tenant, session_id)`→404; `entry.status != "running"`→409; `get_default_injection_registry().put(tenant, session_id, Message(role="user", content=body.message))`; `put()==False`→409; returns `{"status":"queued"}` (202). Body DTO `InjectRequestBody(message: str, min_length=1, max_length=4096)` at `schemas.py:49-55`.
- `TeammateExecutor` — `teammate.py:83-209`. `__init__(*, teammate_child_loop_factory, mailbox, enforcer, event_emitter, inbox_factory)`. `execute()` builds `inbox = self._inbox_factory(subagent_id) if self._inbox_factory else None` (`:137`), drives the child via `async with asyncio.wait_for(_drive(), timeout=budget.max_duration_s)` (`:162`, BLOCKING), relays `SubagentChildEvent(subagent_id, inner=ev)` for the TAO subset (`:154-155`), fail-closed (`:128-191`). `subagent_id` is PASSED IN (generated at `dispatcher.py:209` via `uuid4()`).
- `_TAO_CHILD_EVENT_TYPES` — `fork.py:80-86`: `(TurnStarted, LLMResponded, ToolCallRequested, ToolCallExecuted, ToolCallFailed)`. **`MessageInjected` is NOT in it** → the child's injection-drain is invisible to the Tree today.
- `_make_teammate_inbox(sid) → QueueMessageInbox(get_default_injection_registry(), tenant_id, sid)` — `handler.py:388-395`, ONLY built when `tenant_id` is present. Shared `teammate_mailbox = MailboxStore()` at `handler.py:362`.
- `SubagentChildEvent` — `events.py:366-380`: `subagent_id: UUID|None`, `inner: LoopEvent|None`. The inner is re-serialized via its own sse branch (`MessageInjected` already has a B1 sse serializer → relaying it serializes for free).
- `SubagentSpawnedEvent` (wire) carries `subagent_id` + `mode` → the FE already knows each teammate's id + that it is a teammate.
- **FE**: B1 composer inject `InputBar.tsx:80` (`canInject = isRunning && mode === "real_llm"`), `inject()` (`:88`); `chatService.ts:142-152` `injectMessage(sessionId, message) → POST /api/v1/chat/{id}/inject`; `useLoopEventStream.ts:131-142` `inject()`. chatStore `message_injected`→`UserTurn(injected)` (`chatStore.ts:343-362`); `subagent_spawned` dual-emit updates `subagents: SubagentNode[]` + the inline block (`:667-715`); `subagent_child`→`ChildTurnEvent` appended to `SubagentNode.childEvents`. `InspectorTree.tsx:174-221` renders `SubagentNode` (mode `:182`, subagentId `:194`, childEvents `:206-218`, status badge `:204`). Inline `SubagentForkBlock.tsx`: MISLABEL "Fork · concurrent" `:63` + "{a.turns}t" `:88`; props `SubagentEntry` (`types.ts:64-70`) has NO `mode` / `tokensUsed`. `SubagentNode` (`subagent/types.ts:83-96`) HAS `mode` + `tokensUsed`.

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

- Exact line of the B1 parent `register()` call + the router SSE `unregister` finally (recon cited `router.py:757` unregister; the register line not pinned) — confirm before mirroring the lifecycle pattern.
- The `dispatcher.py` teammate branch lines (`:231-241`) + `_track_and_emit` SubagentSpawned/Completed bracket (`:209-278`) — confirm the executor is the only place that brackets the child (justifies the `inbox_scope` placement on `TeammateExecutor`, not the mode-agnostic dispatcher).
- The `subagent_child` chatStore reducer + `ChildTurnEvent` kinds (`subagent/types.ts:65-76`) — confirm the kind set before adding an "injected" kind.
- `SubagentEntry` vs `SubagentNode` divergence — confirm the inline block's data source (the `subagent_fork` block's `agents`) so the mode-awareness fix sources `mode`/`tokensUsed` correctly.

---

## 1. Sprint Goal

A chat user injects a message into a RUNNING teammate subagent; the teammate drains it at its next turn boundary, the injected turn shows on the Inspector Tree teammate node, and the teammate's subsequent reasoning reflects it — with the teammate's inbox queue registered only while it is live (no Potemkin dead control) — and the inline conversation block stops mislabelling a teammate as "Fork".

## 2. User Stories

- **US-1 (backend endpoint)** — As a chat user, I want `POST /chat/{session_id}/subagents/{subagent_id}/inject` so that I can send a mid-run instruction to a specific running teammate; it gates the parent session (active + owned) + the teammate's live queue, returns 202 on success, 404 for missing/cross-tenant session, 409 when the parent is not running OR the teammate has no live queue, 422 for an empty message.
- **US-2 (spawn-time queue lifecycle — no Potemkin)** — As a platform, I want the teammate's `InjectionRegistry` queue (keyed by `subagent_id`) registered at child-start and unregistered at child-end, so that `put()` succeeds only while the teammate is live (a late/unknown inject 409s instead of silently leaking into an undrained queue).
- **US-3 (the injected turn is visible)** — As a chat user, I want the teammate's injection-drain to surface on its Inspector Tree node ("injected mid-run: …"), so that I can SEE my message landed in the running teammate (not infer it).
- **US-4 (FE inject control)** — As a chat user, I want a small inject input on a running teammate node in the Inspector Tree, so that I can target that teammate; it is shown only while the node is running and the parent is in `real_llm` mode (no dead control).
- **US-5 (inline block mode-awareness — 🟢, 57.102 carryover)** — As a chat user, I want the inline conversation fork-block to say "Teammate" (not "Fork · concurrent") and show real tokens (not "{turns}t") for a teammate spawn, so that the inline render matches the authoritative Inspector Tree.
- **US-6 (drive-through)** — As the developer, I want a real UI + real Azure run where I spawn a multi-turn teammate, inject mid-run via the Tree, and observe the teammate drain + react, so that the feature is proven driven (not gate-only).

## 3. Technical Specifications

### 3.0 Architecture (the teammate gets a registered queue for its lifetime; the inject endpoint is a B1 sibling; `loop.py` untouched)

Two separate HTTP requests, one process-singleton bridge — exactly the B1 shape, but per-subagent:
- The **run request** (the parent's streaming `POST /chat/`) is BLOCKED in `dispatcher.wait_for()` while the teammate child loop runs (`teammate.py:162` awaits the child to completion). During that window the teammate's queue is registered.
- The **inject request** (`POST /chat/{id}/subagents/{subagent_id}/inject`) is a SEPARATE concurrent request on the same FastAPI loop; it `put()`s onto the module `InjectionRegistry` queue keyed by `(tenant, subagent_id)`; the child's `QueueMessageInbox.drain()` (same key) picks it up at its next turn boundary (`loop.py:2026-2054` drain seam — UNCHANGED).

**Key design decision — where register/unregister live** (the queue must exist only while the teammate is live, else `put()` can't tell live from dead → Potemkin):

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **A. `inbox_scope` async-CM on `TeammateExecutor` (CHOSEN)** | Replace the B2a sync `inbox_factory: Callable[[UUID], MessageInbox]` with `inbox_scope: Callable[[UUID], AbstractAsyncContextManager[MessageInbox \| None]]`. `__aenter__`: `await registry.register(tenant, subagent_id)` + return `QueueMessageInbox(...)`. `__aexit__`: `await registry.unregister(tenant, subagent_id)`. The executor brackets the child drive in `async with`. | ✅ The lifecycle is TEAMMATE-specific → belongs on `TeammateExecutor` (the teammate-specific component), not the mode-agnostic dispatcher. Co-locates the inbox view + its queue lifecycle (they are inseparable — building the inbox without registering its queue is the B2a no-op). `async with` guarantees unregister on success / timeout / exception. B2a's `inbox_factory` was an explicit "inert until B2b" placeholder → reshaping it COMPLETES the intended design, not a gratuitous refactor (Karpathy §3 OK). Layer-neutral: the executor depends only on the ABC + an async-CM callable; the concrete registry stays in the api layer (handler builds the scope). |
| B. Keep `inbox_factory` + add `register`/`unregister` async callables, try/finally in the executor | 2 new injected deps; wrap the existing body in try/finally | ❌ 2 deps where 1 suffices; splits "build the inbox" from "register its queue" across two seams that must agree on the key; the inbox built without a registered queue is a half-object. A is more DRY. |
| C. Register/unregister in the dispatcher's `_track_and_emit` bracket, mode-gated | The dispatcher emits SubagentSpawned/Completed around the task | ❌ Couples the mode-agnostic dispatcher to inbox semantics (FORK has no inbox → needs `if mode == TEAMMATE`); the dispatcher would need the api-layer registry callables too; the bracket is further from the inbox it governs. |
| D. Lazy-register in the inject endpoint (`put` False → register+put) | No spawn-time register | ❌ Can't distinguish a live teammate from a never-spawned / already-dead one → a put to a dead `subagent_id` creates an undrained queue (silent loss + leak). Rejected — register-at-spawn + put-False-if-dead is the correct liveness signal (the B1 parent precedent). |

`loop.py` diff = 0 (the child reuses the B1 drain seam unchanged). No new event TYPE, no codegen, no DB, no migration.

### 3.1 The inject-to-teammate endpoint (US-1)

- `backend/src/api/v1/chat/router.py` — new `@router.post("/{session_id}/subagents/{subagent_id}/inject", status_code=202)`; `async def inject_to_subagent(session_id: UUID, subagent_id: UUID, body: InjectRequestBody, current_tenant=Depends(get_current_tenant)) -> dict[str, str]`.
  - Gate parent session: `entry = await get_default_registry().get(current_tenant, session_id)` → 404 if None (cross-tenant 404, never 403 — multi-tenant 鐵律); `entry.status != "running"` → 409 (parent not running → no live teammate).
  - `queued = await get_default_injection_registry().put(current_tenant, subagent_id, Message(role="user", content=body.message))`; `put()==False` → 409 (teammate not running / already finished).
  - Return `{"status": "queued"}`.
  - Reuse `InjectRequestBody` (`schemas.py`) verbatim (same `message` shape; no new DTO).
- The endpoint keys the registry by `subagent_id`, NOT `session_id` — the parent-session gate uses `session_id` (auth + liveness of the owning run); the queue lookup uses `subagent_id`. Both are tenant-scoped.

### 3.2 The `inbox_scope` lifecycle seam (US-2)

- `backend/src/agent_harness/_contracts/subagent.py` — change/extend the teammate inbox contract: `TeammateInboxScope = Callable[[UUID], "AbstractAsyncContextManager[MessageInbox | None]]"` (replaces the implicit `Callable[[UUID], MessageInbox]` shape B2a's `inbox_factory` used). Export from `_contracts/__init__.py`.
- `backend/src/agent_harness/subagent/modes/teammate.py` — `__init__` param `inbox_factory` → `inbox_scope: TeammateInboxScope | None`; `execute()` brackets the child drive: `async with self._inbox_scope(subagent_id) as inbox:` (when scope is None → `inbox=None`, byte-identical to today's no-inbox path). The fail-closed `return`s stay inside the `async with` (exit still unregisters). The mailbox-report drain + success return happen AFTER the `async with` closes (the queue is dead once the child finishes).
- `backend/src/api/v1/chat/handler.py` — replace `_make_teammate_inbox` with an `@asynccontextmanager` `_teammate_inbox_scope(sid)` that `await registry.register(tenant, sid)` on enter, `yield QueueMessageInbox(registry, tenant, sid)`, `await registry.unregister(tenant, sid)` on exit; pass `inbox_scope=_teammate_inbox_scope` through `make_chat_subagent_dispatcher`.
- `backend/src/api/v1/chat/_category_factories.py` + `backend/src/agent_harness/subagent/dispatcher.py` — thread `inbox_scope` (rename of the `inbox_factory` param) to `TeammateExecutor`.

### 3.3 Relay the injected child turn to the Tree (US-3)

- `backend/src/agent_harness/subagent/modes/fork.py` — add `MessageInjected` to `_TAO_CHILD_EVENT_TYPES` (the relayed subset). Justified: the injection-drain is HIGH-signal for B2b (the whole point is proving the inject landed); the 2026-06-09 "locked scope" excluded LOW-signal noise, which `MessageInjected` is not. `teammate.py` + `fork.py` both relay via the shared tuple → FORK gets it too (harmless; FORK has no producer, so it never fires there).
- The sse serialization for the inner `MessageInjected` already exists (B1) → `SubagentChildEvent` relays it for free; no `sse.py` change beyond what 57.96 already does for the wrapper.
- **FE** `chatStore.ts` — in the `subagent_child` reducer, map an inner `message_injected` to a new `ChildTurnEvent` kind (e.g. `kind: "injected"`, `text: inner.text`). `subagent/types.ts` — extend `ChildTurnEvent.kind` union with `"injected"`.
- **FE** `InspectorTree.tsx` — render a `kind: "injected"` child row as "injected mid-run: {text}" (reuse the existing child-row styling; a small tag like the B1 ".route-pill" / "injected" tag for consistency).

### 3.4 The FE inject control on a running teammate node (US-4)

- `frontend/src/features/chat_v2/services/chatService.ts` — `injectToSubagent(sessionId, subagentId, message) → POST /api/v1/chat/{sessionId}/subagents/{subagentId}/inject` body `{ message }` (mirror `injectMessage`).
- `frontend/src/features/chat_v2/components/inspector/InspectorTree.tsx` — on a node with `mode === "teammate"` (or any inbox-bearing mode) AND `status === "running"` AND the parent `mode === "real_llm"`, render a small inline inject input + button → `injectToSubagent(...)`. Gate exactly like B1's `canInject` to avoid a dead control (echo runs have no real teammate loop). On success the injected child turn (US-3) renders under the node as confirmation.
- Error handling mirrors B1: surface via `setError`, do not change run status.

### 3.5 Inline block mode-awareness (US-5 — 🟢 carryover)

- `frontend/src/features/chat_v2/types.ts` — extend `SubagentEntry` with `mode: string` + `tokensUsed: number | null` (sourced from the store's `SubagentNode` at the `subagent_spawned` / `subagent_completed` dual-emit, `chatStore.ts:667-715`).
- `frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx` — dispatch the header on `mode` (`"teammate"` → "Teammate", else "Fork · concurrent") and show `tokensUsed` (falling back to a turn count only when tokens are null) instead of the hardcoded "{a.turns}t".
- Keep the change surgical: do not restructure the block; only the label + the count line + the type fields.

### 3.6 What is explicitly NOT done + Lint / neutrality / 17.md / docs

- NO new event TYPE / NO codegen / NO event-count bump (relaying an existing `MessageInjected` through the existing `SubagentChildEvent` wrapper). NO DB / migration. `loop.py` diff = 0.
- LLM provider neutrality: `agent_harness/**` never imports the api-layer `InjectionRegistry` — the executor depends only on `MessageInbox` (ABC) + the `TeammateInboxScope` callable; the concrete registry stays in the api layer (`check_llm_sdk_leak` + `check_cross_category_import` stay green).
- 17.md: register the `TeammateInboxScope` contract reshape + the `MessageInjected`-in-relay note in the Cat 11 section (single-source).
- Docs: CHANGE-070 + design note 20 §5 light edit (B2b shipped — the teammate inbox now has a live producer) + 17.md. NO new design note (composition continuation of design note 20 + B1, per `sprint-workflow.md §Step 5.5`).

### 3.7 Validation (US-1..US-6)

- Backend unit: endpoint 202 / 404 (missing) / 404 (cross-tenant) / 409 (parent not running) / 409 (teammate no live queue) / 422 (empty). Reuse + extend `test_router.py::TestInjectEndpoint` pattern → a new `TestInjectToSubagentEndpoint`.
- Backend unit: `inbox_scope` registers on enter / unregisters on exit / unregisters on timeout / unregisters on exception (convert B2a's `test_teammate_inbox.py` to the scope shape; the existing `test_teammate_child_loop_drains_queued_inbox_message` proves the drain seam end-to-end through the scope).
- Backend unit: `MessageInjected` IS relayed (an emitter assertion that a child `MessageInjected` produces a `SubagentChildEvent`).
- Frontend Vitest: `chatStore` maps an inner `message_injected` to a `kind:"injected"` ChildTurnEvent; `InspectorTree` renders the inject control only for running teammate nodes in real_llm + renders the injected child row; `SubagentForkBlock` shows "Teammate" + tokens for a teammate entry.
- Drive-through (US-6): real UI + real Azure gpt-5.2 → spawn a multi-turn teammate (a task that does several tool-call turns so there is an injection window) → inject mid-run via the Tree node → the Tree shows the injected child turn → the teammate's later turn reflects the injection → the parent integrates. Screenshot + observed-vs-intended into progress.md.

## 4. File Change List

**Backend (src) — ~6 files**
- `api/v1/chat/router.py` — EDIT: new `POST /{session_id}/subagents/{subagent_id}/inject` endpoint (US-1)
- `agent_harness/_contracts/subagent.py` — EDIT: `TeammateInboxScope` contract (replaces the implicit B2a inbox_factory shape) (US-2)
- `agent_harness/_contracts/__init__.py` — EDIT: export `TeammateInboxScope`
- `agent_harness/subagent/modes/teammate.py` — EDIT: `inbox_factory` → `inbox_scope` async-CM bracket (US-2)
- `agent_harness/subagent/modes/fork.py` — EDIT: add `MessageInjected` to `_TAO_CHILD_EVENT_TYPES` (US-3)
- `agent_harness/subagent/dispatcher.py` — EDIT: thread `inbox_scope` (rename) (US-2)
- `api/v1/chat/_category_factories.py` — EDIT: thread `inbox_scope` (US-2)
- `api/v1/chat/handler.py` — EDIT: `_make_teammate_inbox` → `_teammate_inbox_scope` async-CM (register/unregister) (US-2)

**Frontend (src) — ~6 files**
- `features/chat_v2/services/chatService.ts` — EDIT: `injectToSubagent` (US-4)
- `features/chat_v2/components/inspector/InspectorTree.tsx` — EDIT: inject control on running teammate node + render the injected child row (US-3 FE + US-4)
- `features/chat_v2/store/chatStore.ts` — EDIT: map inner `message_injected` → `kind:"injected"` ChildTurnEvent; source `mode`/`tokensUsed` into `SubagentEntry` (US-3 FE + US-5)
- `features/subagent/types.ts` — EDIT: `ChildTurnEvent.kind` += `"injected"` (US-3 FE)
- `features/chat_v2/types.ts` — EDIT: `SubagentEntry` += `mode` + `tokensUsed` (US-5)
- `features/chat_v2/components/blocks/SubagentForkBlock.tsx` — EDIT: mode-aware label + real tokens (US-5)

**Tests — ~4 files (convert + extend; 0 deletions)**
- `backend/tests/unit/api/v1/chat/test_router.py` — EXTEND: `TestInjectToSubagentEndpoint` (6 cases)
- `backend/tests/unit/agent_harness/subagent/test_teammate_inbox.py` — CONVERT to `inbox_scope` + ADD register/unregister/timeout/exception cases
- `backend/tests/unit/agent_harness/subagent/test_teammate.py` — CONVERT the `inbox_factory` ctor usages to `inbox_scope`
- `backend/tests/unit/agent_harness/subagent/_child_loop_helpers.py` — EDIT: `make_teammate_child_loop_factory` helper → emit an `inbox_scope`
- `frontend/src/features/chat_v2/**/*.test.{ts,tsx}` — EXTEND: chatStore injected-kind + InspectorTree inject control/row + SubagentForkBlock mode label

**Docs**
- `claudedocs/4-changes/feature-changes/CHANGE-070-inject-to-teammate.md` — NEW
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — EDIT (Cat 11: `TeammateInboxScope` + MessageInjected-in-relay)
- `docs/03-implementation/agent-harness-planning/20-subagent-child-loop-design.md` — EDIT §5 (B2b shipped: live inbox producer)
- progress.md / retrospective.md / checklist / CLAUDE.md (Current Sprint + Last Updated) / MEMORY.md pointer + subfile / next-phase-candidates (B2b → done; remaining carryovers) / sprint-workflow.md calibration row

## 5. Acceptance Criteria

1. `POST /chat/{id}/subagents/{subagent_id}/inject` returns 202 + queues for a running teammate; 404 missing/cross-tenant; 409 parent-not-running / teammate-no-live-queue; 422 empty. (US-1)
2. The teammate's queue is registered while the child runs and unregistered on every exit path (success / timeout / exception) — proven by unit tests. (US-2)
3. A message injected into a running teammate is drained by the child at its next turn boundary and the teammate's subsequent reasoning can reference it. (US-1+US-3)
4. The injected turn renders on the Inspector Tree teammate node ("injected mid-run: …"). (US-3)
5. The FE inject control appears only on a running teammate node in `real_llm` mode (no dead control). (US-4)
6. The inline block shows "Teammate" + real tokens for a teammate spawn. (US-5)
7. Gates: mypy `src` 0 errors · flake8 clean · `run_all` 10/10 (event count UNCHANGED) · full pytest green (+N, 0 deletions) · frontend build + lint (no `--silent`) + Vitest green · `check:mockup-fidelity` unchanged.
8. `loop.py` / DB / migration / generated wire schema diff = 0.
9. Drive-through PASS (real UI + real Azure; screenshot + observed-vs-intended). (US-6)

## 6. Deliverables

- [ ] US-1 inject-to-teammate endpoint (202/404/404/409/409/422)
- [ ] US-2 `inbox_scope` register/unregister lifecycle (all exit paths)
- [ ] US-3 `MessageInjected` relayed → Tree injected child row
- [ ] US-4 FE inject control on running teammate node (gated)
- [ ] US-5 inline block mode-aware label + real tokens (🟢 carryover)
- [ ] US-6 drive-through PASS (screenshot)
- [ ] Backend unit tests (endpoint 6 + scope lifecycle 4 + relay 1)
- [ ] Frontend Vitest (chatStore injected-kind + Tree control/row + block label)
- [ ] Full gate sweep green (event count unchanged; loop.py/DB diff 0)
- [ ] CHANGE-070 + 17.md + design note 20 §5 edit
- [ ] Closeout (progress / retrospective / CLAUDE.md lean / MEMORY pointer + subfile / next-phase-candidates / calibration row)

## 7. Workload Calibration

- Scope class **`subagent-inject-to-teammate` (NEW, 0.55, 1st data point)** — a cross-stack feature (backend endpoint + a layer-neutral lifecycle seam + a 1-type relay extension + FE control + FE render + a 🟢 inline polish) reusing three proven assets (B1 registry/endpoint pattern + B2a teammate child loop + 57.96 relay). Same shape + size band as Sprint 57.101 (`loop-injection-primitive-spike` 0.55) — cross-stack, new-domain wiring, but each layer thin over proven machinery.
- **Agent-delegated: no** (parent-direct; `agent_factor = 1.0`) — consistent with the 57.98-57.102 streak; the cross-layer `inbox_scope` seam design needs careful hands.
- Bottom-up est ~13 hr → class-calibrated commit ~7 hr (mult 0.55). Day 4 retro Q2 verifies the ratio.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| **Drive-through injection window** — the parent BLOCKS on the teammate to completion; a fast teammate (3 turns) leaves a tiny window for a human to inject. | Use a multi-turn teammate task (several tool-call turns, e.g. repeated `mock_patrol_check_servers`) so the window is several seconds; drive via Playwright (snapshot running node → fill+click inject → assert the injected child row) for reliable timing. Inject must land BEFORE the teammate's last turn (else nothing to apply it to) — design the task long enough. |
| **`put()` non-auto-create** (resolved Day-0) — if register-at-spawn is missed, every inject 409s → dead control (Potemkin). | US-2 `inbox_scope` registers on `__aenter__` before the child runs; unit test asserts a put succeeds only between enter/exit. |
| **Layer neutrality** — `teammate.py` must not import the api `InjectionRegistry`. | The executor depends only on `MessageInbox` (ABC) + the `TeammateInboxScope` callable; the concrete registry + register/unregister stay in `handler.py`. `check_cross_category_import` must stay green. |
| **Risk Class C (module-singleton across test loops)** — `InjectionRegistry` + `SessionRegistry` are module singletons; new endpoint tests reuse them. | Reuse the existing autouse reset fixtures (the B1 `test_router.py` pattern seeds registries via direct dict manipulation to avoid the asyncio.Lock binding to the TestClient loop). |
| **Risk Class E (stale `--reload` worker)** — drive-through verifies startup-wired handler behavior. | Clean restart before the drive-through: kill stale uvicorn reloader + spawn-worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime), confirm a fresh PID is the sole :8000 owner; do not touch frontend node. |
| **B2a contract churn** (`inbox_factory` → `inbox_scope`) — a just-shipped seam reshaped. | The B2a `inbox_factory` was an explicit "inert until B2b" placeholder built FOR this sprint; reshaping COMPLETES the intended design. Convert (do not delete) the 3 B2a tests; mypy + the converted tests catch regressions. |
| **Echo-mode dead control** — a teammate has no real loop in echo. | Gate the FE inject control on `mode === "real_llm"` + `node.status === "running"` (B1 `canInject` precedent). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Detached / non-blocking teammate** (live parent→child injection while the parent reasons in parallel) — proposal §2.5; needs non-blocking spawn + teammate lifecycle mgmt. YAGNI until a real use case.
- **depth>1 (child-of-child) inject routing** — the teammate is recursion-bounded at 1; nested `subagent_id` routing is a separate slice.
- **Durable teammate transcript / checkpoint** — `AD-Subagent-Transcript-Isolation` (the child is ephemeral).
- **Per-tenant teammate inject policy / guardrail tier** — C3.
- **HANDOFF real child loop** — separate (design note 20 §5).
- **C1 model policy, B3/C3/C2/B4/A3** — later slices in the 10-slice order.
