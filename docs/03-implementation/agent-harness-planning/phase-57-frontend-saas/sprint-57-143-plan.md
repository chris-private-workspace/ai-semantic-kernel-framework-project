# Sprint 57.143 Plan — user Stop→continue durable interrupt-resume

**Summary**: Close `AD-UserStop-Resume-Context` — in chat-v2, a user who hits **Stop** mid-run then types "continue" gets amnesia ("Continue from what?") because the interrupted run persists NOTHING to the `messages` ledger (the per-append SAVEPOINT rides the request DB session, which `rollback()`s on the client-disconnect `CancelledError`). Scope **B (full CC parity, AskUserQuestion 2026-06-25)**: (US-1) make `DBMessageStore` commit each append in its OWN short-lived tenant-scoped session so the user prompt + any completed tool round-trips survive a mid-run stop; (US-2) wire the Stop button to also `POST /cancel`, whose handler persists a `[Request interrupted by user]` marker via a tenant-scoped session. A **drive-through is MANDATORY** (real UI + backend + LLM: Stop mid-run → continue → agent knows what it was doing + ledger holds the marker). This is a spike sprint → **design note 47 required** (8-point gate).

**Status**: Approved-to-execute (user selected Scope B via AskUserQuestion 2026-06-25; user prioritized this AD as a high-impact UX gap)
**Branch**: `feature/sprint-57-143-userstop-resume-context`
**Base**: `main` HEAD `d7d97039` (Sprint 57.142 OTel GenAI semconv flip merged)
**Slice**: closes `AD-UserStop-Resume-Context` (net-new gap; candidate doc `claudedocs/5-status/user-interrupt-resume-context-gap-20260625.md`)
**Scope decisions**: (a) own-session-per-append (NOT router-early-persist) → US-1+US-3 backend-only, zero loop.py/router coordination; (b) Stop → abort (immediate stop, today's feel) **+** `POST /cancel` persists marker via fresh session (B-2, gap doc §4) — NOT cancel_event-driven graceful stop (cancel_event is set but never polled — out of scope); (c) US-2 = marker ONLY, **drop synthetic tool_results** (57.129 atomic-batch guarantees the ledger never holds a dangling tool_use → moot, YAGNI); (d) marker role = `assistant` (clean alternation: [user(q), assistant(marker), user(continue)] — Day-1 confirms provider-validity).

---

## 0. Background

### The gap (`AD-UserStop-Resume-Context`)

- In chat-v2: send → let the agent run → **hit Stop mid-run** → type "continue" → the agent replies "Continue from what, exactly?".
- It remembers earlier **completed** turns (57.127 `DBMessageStore` cross-turn rehydration works) but has **zero** record of the interrupted run — not its answer, not even the user's prompt for that run.
- Drive-through-verified (real Azure gpt-5.2 + direct `messages` ledger DB inspection, 2026-06-25): a turn stopped at 3s persists **0 rows** (polled 40s).

### Why it matters (the missing capability)

This is one of the most visible "feels broken vs Claude Code" behaviors — CC calls out this exact case ("user clicks Stop in cowork seconds after send") and handles it. An enterprise agent platform that forgets what the user just asked the moment they interrupt erodes trust in the core chat loop.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `d7d97039`) | Anchor |
|-------|-------------------------------------|--------|
| FE Stop button | client-side abort ONLY (`abort()` + `setStatus`) — does NOT call the cancel API | `useLoopEventStream.ts:149-152` |
| request DB dep | `commit()` on success; **`rollback()` on ANY exception** (incl. the disconnect `CancelledError`) | `session.py:54-56` |
| ledger append | `DBMessageStore.append` writes via `self._db.begin_nested()` SAVEPOINT on the **request** session; never commits itself | `message_store.py:122` |
| early commit | the sessions row IS committed early (`db.commit()`), but nothing after it | `router.py:384` |
| stream finally | catches the disconnect `CancelledError` → log + re-raise; the `finally` does **NOT** commit | `router.py:1127-1140` |
| cancel_event | `registry.cancel()` sets `entry.cancel_event` but **no code polls it** (grep: 0 consumers in loop/runner) | `session_registry.py:127` |
| `messages` RLS | `FORCE ROW LEVEL SECURITY` + `USING/WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)` → a session without the var set CANNOT insert | `0009_rls_policies.py:97-107` |
| own-session precedent | `retention.py` already writes `messages` from a fresh session via `set_config('app.tenant_id', tid, true)` | `retention.py:91-93` |

→ The fix: persistence must NOT live on the request session (deferred commit + rollback-on-disconnect). Each ledger write commits in its **own short tenant-scoped transaction** (immediately durable); the Stop interrupt is recorded by a **separate `/cancel` request** with its own live session.

### The design (own-session ledger + /cancel marker; backend-heavy + 1 FE wire)

```
US-1 (Cat 7) message_store.py: DBMessageStore holds a session FACTORY (not a bound session)
  load():   async with factory() as s: set_config(app.tenant_id) ; SELECT ; (read-only)
  append(): async with factory() as s: set_config(app.tenant_id) ; INSERT rows ; await s.commit()
  _category_factories.make_chat_message_store: pass get_session_factory() (mirror memory-layer `del db`)
  → loop.py turn-0 persist (loop.py:1978) + tool-batch + final-answer ALL become immediately durable. loop.py UNTOUCHED.

US-2 (Cat 1 / api): router.cancel_session → after registry.cancel, persist the marker
  db = Depends(get_db_session_with_tenant)  # already SET LOCAL app.tenant_id
  DBMessageStore(... ).append([Message(role="assistant", content="[Request interrupted by user]")], turn_num=...)

FE: chatService.cancelSession(id) → POST /sessions/{id}/cancel ; useLoopEventStream.cancel → abort() + void cancelSession(sid)
```

Own-session-per-append is chosen over a router-early-persist because the latter forces loop/router coordination (the loop's `load()` would re-read the early-persisted prompt AND the loop would re-append it → double-send to the LLM). Own-session localizes the fix to Cat 7 + gets US-1 (remember the question) and US-3 (incremental durability of completed tool work) for free.

### Ground truth (recon head-start — code read on `main` HEAD `d7d97039`; ALL re-verified §checklist 0.1)

- `message_store.py:115-141` — `append` uses `self._db.begin_nested()`; ctor takes `db_session` (must become a factory).
- `_category_factories.py:298` — `get_session_factory()` already imported (L93) + the memory-layer factories already `del db` and self-manage sessions (the precedent to mirror).
- `retention.py:91-93` — the `set_config('app.tenant_id', :tid, true)` own-session write-to-`messages` template.
- `tenant_context.py:243` — `get_db_session_with_tenant` FastAPI dep (opens AsyncSession + SET LOCAL app.tenant_id) for the `/cancel` handler.
- `router.py:1167-1183` — `cancel_session` today only flips registry status (no persistence).
- `chatService.ts:245` — `injectMessage` (the service idiom to mirror for `cancelSession`); `useLoopEventStream.ts:149` `cancel` is abort-only; Stop button `InputBar.tsx:288 onClick={cancel}` (unchanged).
- 57.129 atomic-batch: `_persist_to_ledger` writes `[assistant tool_use, *tool results]` as ONE well-formed unit → no dangling tool_use → US-2 needs no synthetic tool_results.

**Baselines (57.142 closeout)**: pytest 2877+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/381 · run_all (v2 lints) 21. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-rls-own-session** — confirm `set_config('app.tenant_id', tid, true)` is required + sufficient for own-session INSERT/SELECT on `messages` (retention.py precedent) → core of US-1.
- **D-get-db-tenant-commit** — confirm `get_db_session_with_tenant` commit/rollback semantics (does it commit at request end like `get_db_session`?) → shapes US-2 commit path.
- **D-atomic-batch** — confirm 57.129 guarantees no dangling tool_use in `messages` → justifies dropping synthetic tool_results.
- **D-factory-ctor** — confirm no OTHER caller constructs `DBMessageStore(db, ...)` besides `make_chat_message_store` (grep) → ctor signature change is safe.
- **D-test-paths** — confirm test file paths for `DBMessageStore` (57.127) + chat router cancel + `chatService` (Vitest).
- **D-marker-role** — confirm an `assistant`-role marker between two user turns yields a provider-valid message sequence on the next real_llm send.

## 1. Sprint Goal

Deliver durable user-Stop→continue: after a mid-run Stop, a subsequent "continue" send rehydrates the interrupted run's user prompt + an explicit `[Request interrupted by user]` marker, so the agent continues with context instead of asking "continue from what?". Proven by gates (mypy/pytest/Vitest/lint/build/llm_sdk_leak) **plus a MANDATORY drive-through** (real UI + backend + real Azure gpt-5.2: Stop mid-run → continue → agent knows the task + DB shows the marker). Produces **CHANGE-110** + **design note 47** (spike, 8-point gate).

## 2. User Stories

- **US-1** (Cat 7 durable ledger): 作為使用者，我希望中途按 Stop 後送出的提問仍被記住，以便我接著「continue」時 agent 知道我問過什麼（且已完成的 tool 回合也保留）。
- **US-2** (Cat 1 / api interrupt marker): 作為使用者，我希望按 Stop 在對話紀錄留下「被中斷」的明確標記，以便 transcript 連貫、agent 明確知道自己被打斷而非收到兩條相連的 user 訊息。
- **US-3** (drive-through, MANDATORY): 作為開發者，我要用真 UI + 真後端 + 真 LLM 實際 Stop 中途→continue 走一遍，確認 agent 接續正確 + DB ledger 含 marker，不只 gate 綠。
- **US-4** (closeout): 作為維護者，我要 CHANGE-110 + design note 47 + calibration + navigators 更新，讓此修復可溯、可重現。

## 3. Technical Specifications

### 3.0 Architecture (backend Cat 7 + Cat 1/api + 1 FE wire; NO migration / NO new table / NO new wire event / NO codegen)

```
EDIT  agent_harness/state_mgmt/message_store.py   — DBMessageStore: bound session → session FACTORY; load()/append() own session + set_config + (append) commit
EDIT  api/v1/chat/_category_factories.py          — make_chat_message_store: pass get_session_factory() (del db, mirror memory-layer precedent)
EDIT  api/v1/chat/router.py                        — cancel_session: + Depends(get_db_session_with_tenant) ; persist [interrupted] marker via DBMessageStore
EDIT  frontend/.../services/chatService.ts         — + cancelSession(sessionId): POST /sessions/{id}/cancel
EDIT  frontend/.../hooks/useLoopEventStream.ts     — cancel(): abort() + void cancelSession(sid)
NEW   tests/unit/agent_harness/state_mgmt/test_message_store_durability.py  — own-session commit survives a request-txn rollback + multi-tenant + RLS
EDIT  tests/.../test for cancel_session            — marker persisted + tenant-scoped + 404 cross-tenant
NEW/EDIT frontend test for chatService.cancelSession + cancel wiring
UNTOUCHED  orchestrator_loop/loop.py               — own-session DBMessageStore makes turn-0/tool/final persist durable with ZERO loop change
UNTOUCHED  session_registry.py                     — cancel_event left as-is (not polled; B-2 uses abort + /cancel marker)
```

### 3.1 Durable per-append ledger (US-1) — `message_store.py` + `_category_factories.py`

- `DBMessageStore.__init__` takes `session_factory: async_sessionmaker[AsyncSession]` (was a bound `AsyncSession`), keeps `session_id` + `tenant_id`.
- `load()`: `async with self._factory() as s:` → `await s.execute(set_config('app.tenant_id', tid, true))` → SELECT (read-only, no commit needed). Best-effort → [].
- `append()`: `async with self._factory() as s:` → set_config → `s.add(...)` rows (sequence_num = MAX+1 within the same session) → `await s.commit()`. Best-effort swallow+log.
- `_next_sequence_num()` runs inside the same own session (MAX+1 on committed rows; each append commits before the next → monotonic).
- `make_chat_message_store(db, session_id, tenant_id)`: `del db` + `DBMessageStore(get_session_factory(), session_id=..., tenant_id=...)` (mirror the memory-layer `del db # reserved` precedent at `_category_factories.py:297`).
- Result: `loop.py:1978` turn-0 user-prompt persist + tool-batch + final-answer persist ALL become immediately durable, independent of the SSE request txn. **loop.py untouched.**

### 3.2 Interrupt marker on Stop (US-2) — `router.py` + `chatService.ts` + `useLoopEventStream.ts`

- `cancel_session`: add `db: AsyncSession = Depends(get_db_session_with_tenant)`. After `registry.cancel(...)` returns True, construct `DBMessageStore` (own factory, this tenant+session) and `append([Message(role="assistant", content="[Request interrupted by user]")], turn_num=<next>)`. Best-effort (a marker-persist failure must not fail the 204). Cross-tenant still 404 (unchanged).
- `chatService.cancelSession(sessionId)`: `POST /api/v1/chat/sessions/{id}/cancel` (204), mirror `injectMessage` (auth header / error shape).
- `useLoopEventStream.cancel`: `abortRef.current?.abort(); setStatus("cancelled"); const { sessionId } = useChatStore.getState(); if (sessionId) void cancelSession(sessionId);` (fire-and-forget; a cancel API failure must not change the UI cancelled state).

### 3.x What is explicitly NOT done

- **synthetic tool_results** — 57.129 atomic-batch ⇒ the ledger never holds a dangling tool_use; moot (Day-0 confirms).
- **cancel_event-driven graceful loop stop** — cancel_event is set but unpolled; making the loop poll it (+ cancel the in-flight LLM await) is a separate hardening slice → `AD-Loop-CancelEvent-Poll-Phase58`.
- **partial assistant answer capture** — the in-flight LLM call is abandoned on abort; there is no partial to persist (out of scope; the marker covers coherence).
- **NO new migration / table / wire event / codegen / mockup change.**

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 0/381 · run_all 21/21 (incl. llm_sdk_leak) · pytest 2877+new · Vitest 920+new · mockup 51 (`diff` empty — UNTOUCHED) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.2 / US-3 **MANDATORY drive-through**.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/state_mgmt/message_store.py` | EDIT (ctor → factory; load/append own session + set_config; append commits) |
| 2 | `backend/src/api/v1/chat/_category_factories.py` | EDIT (`make_chat_message_store` → `get_session_factory()`) |
| 3 | `backend/src/api/v1/chat/router.py` | EDIT (`cancel_session` persists marker via `get_db_session_with_tenant`) |
| 4 | `frontend/src/features/chat_v2/services/chatService.ts` | EDIT (+ `cancelSession`) |
| 5 | `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts` | EDIT (`cancel` → abort + `cancelSession`) |
| 6 | `backend/tests/unit/agent_harness/state_mgmt/test_message_store_durability.py` | NEW |
| 7 | `backend/tests/.../test_chat_cancel_marker.py` (path Day-0) | NEW/EDIT |
| 8 | `frontend/tests/.../chatService` + `useLoopEventStream` cancel test (path Day-0) | NEW/EDIT |
| — | `backend/src/agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** |
| — | `backend/src/api/v1/chat/session_registry.py` | **UNTOUCHED** |
| — | migrations / wire schema / codegen / mockup CSS | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `DBMessageStore.append` commits in its own tenant-scoped session: a row written during a request that later `rollback()`s STILL persists (unit test simulates the request-txn rollback).
2. `messages` own-session INSERT/SELECT succeed under FORCE RLS via `set_config('app.tenant_id', …, true)`; cross-tenant load returns [] / never leaks.
3. `POST /sessions/{id}/cancel` persists an `assistant` `[Request interrupted by user]` marker for the session's tenant; cross-tenant cancel → 404, no marker; marker-persist failure does not fail the 204.
4. Frontend Stop calls both `abort()` and `cancelSession`; a cancel API failure leaves the UI in `cancelled` (no throw).
5. **Drive-through PASS (MANDATORY, real UI + backend + real Azure gpt-5.2)** — send → Stop mid-run → "continue" → the agent continues the ORIGINAL task (not "continue from what?"); DB `messages` shows [user(orig), assistant(marker), user(continue)]; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-UserStop-Resume-Context` CLOSED; CHANGE-110 + design note 47 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 durable own-session `DBMessageStore` (load/append + RLS set_config + factory wiring)
- [ ] US-2 `/cancel` interrupt marker (backend) + Stop→/cancel (frontend service + hook)
- [ ] US-3 drive-through (real UI + backend + LLM; screenshot + DB ledger evidence)
- [ ] US-4 closeout (CHANGE-110 + design note 47 + calibration + navigators)

## 7. Workload Calibration

- Scope class **NEW `chatv2-userstop-resume-durability` 0.60** (1st data point). Real-code core (Cat 7 own-session refactor + RLS set_config + cancel-handler persistence + FE service/hook + durability tests ≥ ~3 hr) anchors to the 57.137 lesson "a >~3 hr real implementation core holds the 0.60 spike multiplier" + the `chatv2-resume-persistence-wiring` 0.55 (57.128) family. **Ceremony risk**: the Stop-mid-run drive-through is fiddly to stage (precise Stop timing on a long generation) — per the 57.120/122/123/126/129/132 ceremony-not-code-accelerated pattern, if the drive-through staging dominates and the ratio lands > 1.20, re-point to 0.85.
- **Agent-delegated: no** (parent-direct — RLS/transaction-semantics correctness + drive-through judgment). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10.5 hr (US-1 ~2.5 · US-2 backend ~1.5 · US-3-fold/incremental verify ~0.5 · FE ~1 · tests ~2 · drive-through ~1.5 · docs ~1.5) → class-calibrated commit ~6.3 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| `messages` FORCE RLS blocks own-session writes | `set_config('app.tenant_id', tid, true)` per own session — `retention.py:91-93` is the exact same-table precedent; Day-0 D-rls-own-session confirms |
| `get_db_session_with_tenant` commit semantics differ from `get_db_session` | Day-0 D-get-db-tenant-commit reads the dep; if it does not auto-commit, the cancel handler commits explicitly |
| own-session-per-append cost (N short txns/run) | acceptable (retention/skills/identity all use per-call sessions); ~2-3 appends/turn; CC notes ~4ms; no hot-loop |
| ctor signature change breaks another `DBMessageStore(db,…)` caller | Day-0 D-factory-ctor grep (expect only `make_chat_message_store`; subagent child loops pass None) |
| Risk Class C (module-level singleton across test event loops) | own-session tests open real sessions; use the suite's session fixtures + autouse resets; tenant-scoped + RLS test mirrors retention/skills test patterns |
| Risk Class E (stale `--reload` masks the startup-wired factory change) | drive-through does a CLEAN restart (kill stale reloader + orphan spawn-workers; confirm sole port owner) before verifying |
| marker role yields invalid provider sequence | Day-0 D-marker-role + the drive-through real_llm "continue" send proves the sequence is accepted |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- cancel_event-driven graceful loop stop + in-flight LLM cancel → `AD-Loop-CancelEvent-Poll-Phase58`.
- synthetic tool_results for a dangling tool_use → moot under 57.129; revisit only if Day-0 D-atomic-batch finds a gap.
- partial assistant-answer streaming capture → separate (would need a new partial-persist seam).
- `message_events` (57.125/126 replay ledger) durability on disconnect → separate from the `messages` Cat-3 ledger; this sprint fixes the rehydration ledger only.
