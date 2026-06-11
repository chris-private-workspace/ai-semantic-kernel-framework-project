# Sprint 57.103 Progress — chat-user inject-to-teammate (B2b)

**Branch**: `feature/sprint-57-103-inject-to-teammate`
**Plan**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-103-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-103-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch (2026-06-11)

### Branch
- `git checkout -b feature/sprint-57-103-inject-to-teammate` (HEAD `0209c672`, post-57.102-merge)

### Three-prong verify

**Prong 1 — path verify**: all File Change List paths confirmed (3 Explore recon + personal re-read). No NEW src files (all edits); CHANGE-070 + the memory subfile are the only new files. ✅

**Prong 2 — content verify** (the load-bearing greps):
- `injection_registry.py:73-82` — `put()` returns `False` on no-queue (NOT auto-create). ✅ (the load-bearing fact for US-2)
- B1 parent lifecycle: register `router.py:283`, unregister `router.py:757` (`_stream_loop_events` finally). ✅ (the pattern to mirror)
- `fork.py:80-86` `_TAO_CHILD_EVENT_TYPES` = `(TurnStarted, LLMResponded, ToolCallRequested, ToolCallExecuted, ToolCallFailed)` — `MessageInjected` ABSENT. ✅ (US-3 add it)
- `teammate.py:137` inbox build + `:162` blocking `wait_for` — the `async with` insertion point. ✅
- `dispatcher.py:115` ctor param `inbox_factory: "Callable[[UUID], MessageInbox] | None"` → rename `inbox_scope`; passed to `TeammateExecutor(inbox_factory=…)` `:145-151`. ✅
- `handler.py:388-395` `_make_teammate_inbox` (tenant-None guard) → `_teammate_inbox_scope` async-CM. ✅
- `subagent/types.ts:65-68` `ChildTurnEvent.kind: string` (NOT a union). ✅
- `chatStore.ts:777-821` `subagent_child` reducer is GENERIC (`kind: ev.data.inner_type`, projects turn/text). ✅
- `SubagentForkBlock.tsx:63` "Fork · concurrent" + `:88` "{a.turns}t"; `SubagentEntry` (`types.ts:64-70`) has no `mode`/`tokensUsed`. ✅

**Prong 3 — schema verify**: N/A — no DB / migration / ORM / new wire schema this sprint.

### Drift findings

- **D1** — `ChildTurnEvent.kind` is `string`, not a union (`subagent/types.ts:67`). Implication: US-3 FE needs NO type change for the injected kind; only the reducer text projection + an InspectorTree render branch + a doc-comment update. Scope slightly < plan §3.3.
- **D2 (positive)** — the `subagent_child` chatStore reducer is GENERIC: it keys `kind: ev.data.inner_type` and projects `turn`/`text` from the opaque `inner` (`chatStore.ts:785-790`). Implication: once the backend relays `MessageInjected` as a `SubagentChildEvent`, the chatStore AUTO-creates a `kind:"message_injected"` ChildTurnEvent with (pending) no/near-no chatStore change. US-3 FE shrinks to: an InspectorTree render branch for `kind === "message_injected"` + confirm `inner.text` is projected to `entry.text`. → §8 Risks: scope reduction, not expansion.
- **D3** — the injected child-event kind value will be the wire `inner_type` = `"message_injected"` (NOT a custom `"injected"`). Align plan §3.3's `kind:"injected"` → use `"message_injected"` (the wire inner_type, consistent with the generic reducer). The render LABEL can still read "injected mid-run". No plan §3 rewrite — recorded here + carried to Day-2 implementation.
- **D4 (confirm)** — B1 parent register/unregister live in the ROUTER (api layer) bracketing the SSE stream. For the teammate there is no router bracket (the child runs inside the executor) → the executor's `async with self._inbox_scope` is the bracket; the register/unregister CALLS stay in the api layer (`handler._teammate_inbox_scope`). Layer-neutral. ✅ (validates the §3.0 Option-A choice)
- **D5 (confirm)** — dispatcher ctor param rename `inbox_factory` → `inbox_scope` is a 1-line change at `:115` + `:150`; `TeammateExecutor` ctor + `execute()` carry the reshape.

**Go/no-go**: all drifts REDUCE scope (D1+D2+D3) or confirm the design (D4+D5); 0 scope expansion. → continue to Day 1.

### Day-0 time
- recon (3 Explore agents parallel) + personal re-read of 3 load-bearing files + plan + checklist + drift catalog ≈ ~2 hr.

---

## Day 1 — Backend: endpoint + inbox_scope lifecycle + relay (2026-06-11)

### Accomplishments (US-1 / US-2 / US-3 backend)

- **US-2 `inbox_scope` lifecycle** — replaced the B2a sync `inbox_factory: Callable[[UUID], MessageInbox]` with `TeammateInboxScope = Callable[[UUID], AbstractAsyncContextManager[MessageInbox | None]]` (`_contracts/subagent.py` + export). `TeammateExecutor.execute` now brackets the child drive in `async with self._inbox_scope(subagent_id) as inbox:` (None scope → no-inbox path byte-identical). Threaded `inbox_factory` → `inbox_scope` rename through `dispatcher.py` + `_category_factories.py`.
- **Refactor (cleaner than plan §3.5)** — extracted the register/unregister CM into `injection_registry.make_teammate_inbox_scope(registry, tenant_id)` (an `@asynccontextmanager` that registers on enter / unregisters on exit) instead of a nested closure in `handler.py`. Co-locates the lifecycle with `QueueMessageInbox` (the injection machinery) AND makes it directly unit-testable (the register/unregister/exception invariants test the REAL code, not a test-local copy). `handler.py` now just calls `make_teammate_inbox_scope(get_default_injection_registry(), tenant_id)`.
- **US-1 endpoint** — `POST /chat/{session_id}/subagents/{subagent_id}/inject` (`router.py`), a B1 sibling: parent gate via `SessionRegistry.get` (404 missing/cross-tenant) + `status != "running"` (409) + `put(tenant, subagent_id, ...)` (409 on False = teammate not live); reuses `InjectRequestBody` (empty → 422).
- **US-3 backend relay** — added `MessageInjected` to `fork.py::_TAO_CHILD_EVENT_TYPES` (shared by FORK + TEAMMATE); a child's injection-drain `MessageInjected` now relays as a `SubagentChildEvent` (no new event type, no codegen).

### Tests (+9 net backend, 0 deletions)

- `test_teammate_inbox.py` CONVERTED to `inbox_scope` (3 → 6): sid-keyed scope open, inbox drain (B1 seam), no-inbox runs, `make_teammate_inbox_scope` register-on-enter+concurrent-put-reaches-inbox+unregister-on-exit, unregister-on-exception, **MessageInjected relayed as SubagentChildEvent** (US-3).
- `test_router.py::TestInjectToSubagentEndpoint` (+6): 202 / 404 missing / 404 cross-tenant / 409 parent-not-running / 409 teammate-no-queue / 422 empty.
- `test_teammate.py` unchanged (didn't use the old `inbox_factory`); `_child_loop_helpers.py` unchanged (uses `TeammateChildLoopFactory`, not the renamed param).

### Gate (Day-1 partial)

- mypy `src` **0/355** ✅ (the `inbox_scope` async-CM + the extracted `make_teammate_inbox_scope` type-check cleanly)
- black / isort / flake8 on 9 changed src + 2 test files ✅
- `pytest tests/unit/agent_harness/subagent/ tests/unit/api/v1/chat/test_router.py` → **101 passed** ✅
- `loop.py` diff = 0 (the child reuses the B1 drain seam unchanged)

### Drift note (positive, vs plan §3.5)

The plan's nested-closure `_teammate_inbox_scope` in `handler.py` was extracted to `injection_registry.make_teammate_inbox_scope` — cleaner + testable. No scope change, just a better seam. Recorded as the Day-1 implementation refinement.
