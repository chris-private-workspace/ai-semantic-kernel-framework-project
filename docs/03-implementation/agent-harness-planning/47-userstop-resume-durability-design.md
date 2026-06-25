# Design Note 47 — user Stop→continue durable interrupt-resume (Sprint 57.143)

**Purpose**: Document the SHIPPED contract for durable user-Stop→continue: own-session ledger persistence + the interrupt marker + the Stop→/cancel flow. Closes `AD-UserStop-Resume-Context`.
**Category / Scope**: Cat 7 (State Mgmt) + Cat 1 / api (chat) + chat-v2 ; cross-cutting durability / Sprint 57.143
**Created**: 2026-06-25
**Status**: Active — shipped + drive-through verified
**Verified ratio (estimated)**: ≥ 95% (every claim file:line + drive-through-confirmed)

> **Modification History**
> - 2026-06-25: Initial creation (Sprint 57.143) — extracted from the shipped implementation

> Analysis upstream: `claudedocs/5-status/user-interrupt-resume-context-gap-20260625.md` (drive-through-verified gap + CC blueprint + root-cause of the miss). This note documents the SHIPPED fix.

---

## 1. Spike Summary (US-1 durable ledger · US-2 interrupt marker · US-3 drive-through)

When a chat-v2 user hits **Stop** mid-run then types "continue", the interrupted run must be remembered. The fix adds Claude Code's two disciplines onto V2's existing ledger-replay (`DBMessageStore.load()` at run start, `loop.py:1959-1960`):
1. **US-1**: every ledger append commits in its OWN short-lived tenant-scoped session (durable the moment it runs), not a request-scoped SAVEPOINT that rolls back on the client-disconnect `CancelledError`.
2. **US-2**: the Stop button also calls `POST /sessions/{id}/cancel`, whose handler persists a `[Request interrupted by user]` marker via that same own-session path.

## 2. Decision Matrix

### D-1 — Where to make the user prompt durable

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **Own-session-per-append** (CHOSEN) | `DBMessageStore` opens a fresh session + commits each append (`message_store.py:115-149`) | ✅ backend-only; gets US-1 (prompt) + US-3 (completed tool batches) free; no loop/router coordination |
| Router early-persist | persist the user prompt + `db.commit()` in the send handler before the loop, mirror the sessions-row commit (`router.py:384`) | ❌ the loop's `load()` (`loop.py:1959`) would re-read the early row AND the loop re-appends `user_input` → the LLM sees the prompt twice |
| Keep request-session SAVEPOINT | status quo | ❌ THE bug — `get_db_session` rolls back on `CancelledError` (`session.py:55-56`) |

### D-2 — How Stop records the interrupt

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **Abort + separate /cancel persists marker** (CHOSEN, B-2) | FE `cancel()` aborts the SSE (immediate stop) AND `POST /cancel`; the cancel handler (own session) writes the marker (`router.py` cancel_session) | ✅ robust — the marker write is on a LIVE request session, not the dying SSE request; keeps the immediate-stop feel |
| cancel_event-driven graceful stop | make the loop poll `entry.cancel_event` (`session_registry.py:127`) + end gracefully | ❌ cancel_event is set but never polled (0 consumers); to stop immediately mid-LLM-call still needs the abort → out of scope (`AD-Loop-CancelEvent-Poll-Phase58`) |
| cleanup inside the SSE `CancelledError` handler | persist in `except asyncio.CancelledError` (`router.py:1127`) | ❌ awaiting DB work inside a cancellation is fragile (the task is being torn down) + the request session is rolling back |

### D-3 — Marker role + synthetic tool_results

| Question | Decision | Why |
|----------|----------|-----|
| Marker role | `assistant` | clean alternation `[user(prompt), assistant(marker), user(continue)]`; drive-through proved Azure accepts it |
| Synthetic tool_results for pending tool | **DROPPED** | 57.129 atomic-batch persists `[assistant tool_use, *tool results]` as one unit (`message_store.py` docstring + `loop.py` `_persist_to_ledger`) → the ledger NEVER holds a dangling tool_use → moot (YAGNI) |

## 3. Verified Invariants (file:line)

- `DBMessageStore.__init__` takes `session_factory: async_sessionmaker[AsyncSession]`; `_set_tenant` runs `SELECT set_config('app.tenant_id', :tid, true)`; `append()` ends with `await db.commit()` — `message_store.py:82-149`.
- FORCE-RLS requires the tenant var: `messages` has `FORCE ROW LEVEL SECURITY` + `USING/WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)` — `migrations/versions/0009_rls_policies.py:97-107`. Same-table own-session precedent: `transcripts/retention.py:91-93`.
- `make_chat_message_store` passes `get_session_factory()` (`_category_factories.py:392-394`); the None-guard still returns None for subagent child loops / legacy callers.
- `cancel_session` persists the marker after `registry.cancel` True, best-effort try/except, never failing the 204 — `router.py` (`INTERRUPT_MARKER` const + cancel_session).
- FE `cancel()` = `abort()` + `setStatus("cancelled")` + `void cancelSession(sid).catch(()=>{})` — `useLoopEventStream.ts:149-158`; `cancelSession` = `POST /api/v1/chat/sessions/{id}/cancel` — `chatService.ts`.
- `loop.py` UNTOUCHED — the turn-0 persist (`loop.py:1974-1978`) becomes durable purely via the own-session store.

## 4. Cross-Category Contracts (17.md single-source)

**N/A — no new cross-category contract.** US-1 is an internal behavioral change to the existing **Cat 7 `MessageStore` ABC** impl (`state_mgmt/_abc.py §MessageStore`); the ABC signature (`load()`/`append(messages, *, turn_num)`) is unchanged — only the ctor (now a factory) + the commit discipline changed. US-2 reuses the same ABC from the api layer. No new ABC, event type, or wire-schema entry → nothing to register in `17-cross-category-interfaces.md`.

## 5. Open Invariants (verified vs deferred)

**Verified in this spike**: own-session append durability (survives a request rollback — `test_append_survives_request_session_rollback`); cross-tenant isolation under FORCE RLS; the marker persists on /cancel + cross-tenant 404 writes none; FE Stop fires /cancel; the full real-Azure drive-through (durable prompt + marker + correct continue).

**Deferred (NOT verified — Phase 58)**:
- graceful cancel_event-driven loop stop + in-flight LLM cancel (`AD-Loop-CancelEvent-Poll-Phase58`).
- partial assistant-answer streaming capture (the in-flight LLM output on abort).
- `message_events` (57.125/126 replay ledger) disconnect durability — this spike fixes only the `messages` Cat-3 rehydration ledger.
- sub-second race: Stop before the turn-0 persist → ledger leads with the assistant marker; Azure is lenient, but a leading-assistant guard is unverified.

## 6. Rollback

Revert is low-risk + localized: `git revert` the 5 source edits (`message_store.py` ctor→factory, `_category_factories.py` factory arg, `router.py` cancel marker + imports + const, `chatService.ts` cancelSession, `useLoopEventStream.ts` cancel wiring). No migration / schema / wire change to undo. The DB rows already written (durable prompts + markers) are harmless legacy data (valid `messages` rows). Est. < 1 hr. The own-session change is behind the same `make_chat_message_store` None-guard, so subagent/legacy callers are unaffected either way.

## 7. References

- Gap analysis: `claudedocs/5-status/user-interrupt-resume-context-gap-20260625.md`
- CC blueprint: `reference/claude-code-source-cdoe/src/QueryEngine.ts:436-463`, `utils/messages.ts:207-209`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-110-userstop-resume-context.md`
- Drive-through evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-143/artifacts/`
- Related shipped: Sprint 57.127 (`DBMessageStore` rehydration), 57.129 (atomic tool batch), 57.88 (durable HITL pause-resume — different trigger)
- Own-session RLS precedent: `platform_layer/transcripts/retention.py:91-93`

## 8. Modification History

- 2026-06-25: Initial creation (Sprint 57.143) — shipped own-session ledger + interrupt marker + Stop→/cancel
