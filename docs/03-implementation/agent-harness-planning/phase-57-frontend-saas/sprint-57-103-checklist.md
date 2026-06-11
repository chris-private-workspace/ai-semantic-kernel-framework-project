# Sprint 57.103 — Checklist (chat-user inject-to-teammate: live MessageInbox producer + injected child turn on the Tree + inline block mode-awareness — B2b: the live UI producer the B2a teammate inbox was wired "until B2b" for)

[Plan](./sprint-57-103-plan.md)

**Status**: In progress
**Branch**: `feature/sprint-57-103-inject-to-teammate`

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (re-confirm against HEAD `0209c672` before Day-1 code)
- [x] **Prong 1 — path verify**: Glob-confirm every File Change List path exists/absent as expected (router.py / teammate.py / fork.py / dispatcher.py / _category_factories.py / handler.py / _contracts/subagent.py; FE chatService.ts / InspectorTree.tsx / chatStore.ts / subagent/types.ts / chat_v2/types.ts / SubagentForkBlock.tsx; test files)
- [x] **Prong 2 — content verify** (the load-bearing greps):
  - `injection_registry.py:73-82` `put()` returns False on no-queue (NOT auto-create) — re-confirm
  - B1 parent `register()` call line + the router SSE `unregister` finally line (pin both for the lifecycle mirror)
  - `_TAO_CHILD_EVENT_TYPES` (`fork.py:80-86`) — confirm `MessageInjected` absent + the tuple membership
  - `teammate.py:137` inbox build site + `:162` the blocking `wait_for` (confirm the `async with` insertion point)
  - `handler.py:388-395` `_make_teammate_inbox` (confirm the rename target + the tenant-None guard)
  - `dispatcher.py` teammate branch + the `inbox_factory` thread param name
  - `chatStore.ts` `subagent_child` reducer + `ChildTurnEvent.kind` set (`subagent/types.ts:65-76`)
  - `SubagentForkBlock.tsx:63` "Fork · concurrent" + `:88` "{a.turns}t" + `SubagentEntry` (`types.ts:64-70`) field set
- [x] **Prong 3 — schema verify**: N/A (no DB / migration / ORM / new wire schema this sprint) — record "N/A: no schema change"
- [x] **Catalog drift** in progress.md Day 0 (`D{N}` + finding + implication; do NOT silently rewrite plan §3 — add to §8 Risks)
- [x] **Go/no-go**: scope shift ≤20% → continue; 20-50% → re-confirm §5/§7; >50% → abort + redraft

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-103-inject-to-teammate` (done; HEAD `0209c672`)

---

## Day 1 — Backend: endpoint + `inbox_scope` lifecycle + relay (US-1/US-2/US-3 backend)

### 1.1 The `inbox_scope` contract + executor bracket (US-2)
- [x] **`TeammateInboxScope` contract** (`_contracts/subagent.py` + `__init__.py` export)
  - `Callable[[UUID], "AbstractAsyncContextManager[MessageInbox | None]]"`; TYPE_CHECKING-safe import
  - DoD: mypy green; `check_cross_category_import` green (no api import into agent_harness)
- [x] **`TeammateExecutor` `inbox_factory` → `inbox_scope`** (`teammate.py`)
  - `__init__` param rename + type; `execute()` brackets the child drive in `async with self._inbox_scope(subagent_id) as inbox:` (None scope → inbox None, byte-identical no-op path)
  - fail-closed returns stay inside the `async with`; mailbox-report drain + success return after it closes
  - DoD: mypy green; the no-scope path is byte-identical to the no-inbox path

### 1.2 Handler + dispatcher wiring (US-2)
- [x] **`_teammate_inbox_scope` async-CM** (`handler.py`)
  - `@asynccontextmanager`: `await registry.register(tenant, sid)` → `yield QueueMessageInbox(registry, tenant, sid)` → `await registry.unregister(tenant, sid)`; tenant-None guard preserved
  - thread `inbox_scope=` through `make_chat_subagent_dispatcher`
- [x] **Thread `inbox_scope`** (`_category_factories.py` + `dispatcher.py` rename of the `inbox_factory` param)
  - DoD: mypy green; the dispatcher passes `inbox_scope` to `TeammateExecutor`

### 1.3 The inject-to-teammate endpoint (US-1)
- [x] **`POST /{session_id}/subagents/{subagent_id}/inject`** (`router.py`)
  - parent gate via `get_default_registry().get(tenant, session_id)` → 404; `status != "running"` → 409
  - `put(tenant, subagent_id, Message(...))`; `put()==False` → 409; return `{"status":"queued"}` (202)
  - reuse `InjectRequestBody`; empty message → 422 (Field min_length)
  - DoD: mypy green; route registered (no new DTO)

### 1.4 Relay `MessageInjected` to the Tree (US-3 backend)
- [x] **Add `MessageInjected` to `_TAO_CHILD_EVENT_TYPES`** (`fork.py`)
  - DoD: a child `MessageInjected` produces a `SubagentChildEvent` (emitter assertion); `check_event_schema_sync` count UNCHANGED (no new type)

---

## Day 2 — Frontend: inject control + injected-turn render + inline mode-awareness + tests (US-3 FE/US-4/US-5)

### 2.1 FE service + inject control + injected child row (US-4 + US-3 FE)
- [ ] **`injectToSubagent`** (`chatService.ts`) → `POST /chat/{id}/subagents/{subagentId}/inject` body `{message}`
- [ ] **Inject control on running teammate node** (`InspectorTree.tsx`)
  - shown only for `status === "running"` && parent `mode === "real_llm"` (no dead control); small input + button → `injectToSubagent`
  - error via `setError` (no status change)
- [ ] **`kind:"injected"` child row** (`InspectorTree.tsx` + `chatStore.ts` `subagent_child` reducer + `subagent/types.ts` `ChildTurnEvent.kind`)
  - maps inner `message_injected` → `{kind:"injected", text}`; renders "injected mid-run: {text}"

### 2.2 Inline block mode-awareness (US-5 — 🟢 carryover)
- [ ] **`SubagentEntry` += `mode` + `tokensUsed`** (`chat_v2/types.ts`) + source them at the `subagent_spawned`/`subagent_completed` dual-emit (`chatStore.ts`)
- [ ] **Mode-aware label + real tokens** (`SubagentForkBlock.tsx`): `"teammate"` → "Teammate"; show `tokensUsed` (fallback turn count only when null) — surgical (label + count line only)

### 2.3 Tests (US-1..US-5)
- [ ] **Backend** `test_router.py::TestInjectToSubagentEndpoint` (202 / 404 missing / 404 cross-tenant / 409 parent-not-running / 409 teammate-no-queue / 422 empty)
- [ ] **Backend** `test_teammate_inbox.py` CONVERT to `inbox_scope` + ADD register-on-enter / unregister-on-exit / unregister-on-timeout / unregister-on-exception; keep `test_teammate_child_loop_drains_queued_inbox_message`
- [ ] **Backend** `test_teammate.py` + `_child_loop_helpers.py` CONVERT `inbox_factory` ctor usages → `inbox_scope`
- [ ] **Backend** relay assertion (child `MessageInjected` → `SubagentChildEvent`)
- [ ] **Frontend Vitest**: chatStore injected-kind mapping; InspectorTree inject control gating + injected row; SubagentForkBlock "Teammate" + tokens

---

## Day 3 — Full regression + drive-through (US-6) + CHANGE-070 + 17.md

### 3.1 Full gate sweep
- [ ] `black . && isort . && flake8 .` (src tests) clean
- [ ] `mypy src` 0 errors
- [ ] `python scripts/lint/run_all.py` 10/10 (event count UNCHANGED; `check_llm_sdk_leak` 0; `check_cross_category_import` green; `check_ap1` green)
- [ ] full `pytest -q` green (+N, 0 deletions) — confirm baseline delta
- [ ] frontend `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` (Vitest) + `npm run check:mockup-fidelity` (unchanged)
- [ ] `git diff` confirms `loop.py` / DB / migration / generated wire schema diff = 0

### 3.2 Drive-through (US-6 — inject into a running multi-turn teammate)
- [ ] Clean restart (Risk Class E): kill stale uvicorn reloader + spawn-worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime), confirm fresh PID sole :8000 owner; do not touch frontend node
- [ ] Real UI (real_llm) + real Azure gpt-5.2: spawn a multi-turn teammate (a task with several tool-call turns for an injection window)
- [ ] Inject mid-run via the Tree node control (Playwright: snapshot running node → fill + click inject)
- [ ] Observe: the Tree shows the injected child turn ("injected mid-run: …") + the teammate's later turn reflects it + the parent integrates
- [ ] Screenshot (`artifacts/dt57103-inject-teammate.png`) + observed-vs-intended into progress.md
- [ ] Walk every new control: clickable / effect / label real / result renders (Drive-Through DoD)

### 3.3 CHANGE-070 + 17.md + design note 20
- [ ] `CHANGE-070-inject-to-teammate.md` (problem / design / verification / impact)
- [ ] 17.md Cat 11: `TeammateInboxScope` contract + MessageInjected-in-relay note (single-source)
- [ ] design note 20 §5: B2b shipped (teammate inbox now has a live producer)

---

## Day 4 — Closeout (composition continuation — no new design note)

### 4.1 Closeout
- [ ] progress.md Day 0-3 + drive-through complete
- [ ] retrospective.md Q1-Q7 (Q2 calibration ratio vs the 0.55 `subagent-inject-to-teammate` class; Q7 no-design-note rationale)
- [ ] CLAUDE.md Current Sprint + Last Updated (lean, per §Sprint Closeout policy)
- [ ] MEMORY.md pointer + `project_phase57_103_inject_to_teammate.md` subfile
- [ ] next-phase-candidates.md: B2b → done; remaining carryovers (detached teammate / depth>1 / inline-block already in US-5)
- [ ] sprint-workflow.md calibration row `subagent-inject-to-teammate 0.55` (1st data point)
- [ ] all checklist items `[x]` (never delete unchecked; mark 🚧 + reason if deferred)
