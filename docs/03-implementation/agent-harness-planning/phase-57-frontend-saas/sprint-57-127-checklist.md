# Sprint 57.127 — Checklist (chat-v2 live multi-turn context — rehydrate prior conversation into the live loop. **Approach A** (user-picked): give the existing-but-unwritten `messages` table a real writer + rehydrate on follow-up, via a NEW provider-neutral `MessageStore` ABC (sibling to `Checkpointer`, bound to `(db, session_id, tenant_id)`); the loop **self-loads** prior messages at `run()` start + **appends** the run's NEW messages (a compaction-immune side-list) at completion → `loop.run()`'s ABC signature UNCHANGED (no caller ripple). **Pure backend** (the frontend already continues the session — 57.126); ZERO frontend/CSS/Vitest/wire/codegen change; no table migration (a forward-partition migration only if Day-0 finds the 2026-07 cliff). **Drive-through MANDATORY** — the exact 57.126 failing case: turn 2 "its population?" must now resolve "it"→Paris. CHANGE-094; design note 38 (spike).)

[Plan](./sprint-57-127-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch  ✅ DONE (progress.md Day-0; **US-6 partition migration DROPPED** — `messages_default`+`message_events_default` exist (0028); +`_contracts/message_serde.py` serde-move + `make_chat_message_store` factory added)

### 0.1 Three-prong Day-0 verify (against `main` HEAD `c1d3d1be`)
- [x] **Prong 1 — path verify**: `message_store.py` does NOT exist; `state_mgmt/_abc.py` + `checkpointer.py` + `loop.py` + `orchestrator_loop/_abc.py` + `api/v1/chat/handler.py` + `router.py` + `session_repository.py` + `_contracts/chat.py` + `models/sessions.py` exist; `CHANGE-094` + `38-*.md` free; test paths (`tests/unit/agent_harness/state_mgmt/`, `tests/unit/agent_harness/orchestrator_loop/`, `tests/integration/api/`) exist
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-messagestore-wiring-site** ⚠️ THE feasibility check — grep `build_handler` / where `DBCheckpointer(...)` is constructed for the chat path; confirm `db` + `session_id` + `tenant_id` are ALL in scope there (→ construct `DBMessageStore` at the same site). If `session_id` is router-generated post-build → note the construction must co-locate with `DBCheckpointer`
  - [x] **D-message-helpers-roundtrip** — read `_message_to_dict`/`_message_from_dict` (`loop.py:~305-341`); confirm full round-trip of `role`/`content`/`tool_calls`/`tool_call_id`/`name`/`metadata`; decide exposure (import vs shared module) for `message_store.py`
  - [x] **D-loop-append-sites** — enumerate EVERY site in `loop.py run()`/`_run_turns` that appends a real `Message` to `messages` (assistant response + each tool-result) → the `_record_new` helper covers all; confirm the single LoopCompleted yield/exit (end_turn / max_turns / budget) for the append point
  - [x] **D-checkpointer-binding** — confirm `DBCheckpointer(db, session_id, tenant_id)` bound-at-construction pattern (`checkpointer.py:~94-150`) to mirror for `DBMessageStore`; confirm the loop ctor param style (`checkpointer: Checkpointer | None = None`) to mirror
  - [x] **D-message-orm-shape** — confirm `Message` ORM columns (`role`/`content_type`/`content` JSONB/`sequence_num`/`turn_num`; nullable `model`/`tokens_*`); the UNIQUE `(session_id, sequence_num, created_at)` (seq must be monotonic per session)
  - [x] **D-abc-home** — `MessageStore` ABC home: co-locate in `message_store.py` OR add to `state_mgmt/_abc.py` (pick per where `Checkpointer` ABC lives — match convention)
- [x] **Prong 3 — schema verify**:
  - [x] **D-partition-coverage** — `messages` (+ `message_events`) partition coverage: grep `migrations/versions/*` for `messages_2026_*` / later partition migrations; confirm whether coverage extends past `2026_06`. If it cliffs at 2026-07-01 → plan the conditional forward-partition migration (US-6). Confirm Alembic head + next free revision number
  - [x] **D-no-table-migration** — confirm NO new table/column needed (`messages` exists with all required columns) → only the CONDITIONAL partition migration
  - [x] **D-messages-rls** — confirm the multi-tenant enforcement style on `messages` (FK + explicit `tenant_id` filter at ORM layer per `09-db-schema-design.md`); the writer/reader MUST filter `tenant_id`
- [x] **D-baselines** — re-assert: full pytest **2712+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/370** · run_all **10/10**
- [x] **Catalog drift** — progress.md Day-0 table (D-IDs + finding + implication; cross-ref plan §Risks)
- [x] **Go/no-go** — findings shift scope ≤20% → continue; the wiring-site finding (D-messagestore-wiring-site) is the gate (if infeasible at `build_handler`, relocate the construction — still Approach A)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-127-chatv2-live-multiturn-context` (from `main` `c1d3d1be`) ✅

---

## Day 1 — Backend: `MessageStore` ABC + `DBMessageStore` + loop self-load/append + wiring (US-1..6)  ✅ DONE (gate green; progress.md Day 1-2; US-6 migration DROPPED — default partitions exist)

### 1.1 `MessageStore` ABC (US-1)
- [x] **`message_store.py` (NEW) / `_abc.py`**: `MessageStore(ABC)` — `async def load(self) -> list[Message]`; `async def append(self, messages: list[Message], *, turn_num: int) -> None`; bound to `(session_id, tenant_id)` at construction. Provider-neutral (no DB/provider import in the ABC). File header.
  - DoD: ABC imports only `Message` (Cat-3); LLM-SDK-leak lint clean
  - Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green)

### 1.2 `DBMessageStore` impl (US-2)
- [x] **`message_store.py` (NEW)**: `DBMessageStore(db, session_id, tenant_id)`:
  - `load()`: `select(Message).where(session_id & tenant_id).order_by(sequence_num)` → `[_message_from_dict(r.content) for r in rows]`; `db is None` → `[]`
  - `append(messages, *, turn_num)`: `db is None or not messages` → return; `start = MAX(sequence_num)+1`; per msg `db.add(Message(id=uuid4(), session_id, tenant_id, sequence_num=start+i, turn_num, role, content_type, content=_message_to_dict(m)))`; best-effort `begin_nested()` SAVEPOINT (mirror `_persist_main_event`); `model`/`tokens_*` null
  - DoD: round-trips a `Message` incl. `tool_calls`; seq continues from MAX; cross-tenant load → `[]`
  - Verify: `pytest tests/unit/agent_harness/state_mgmt/test_message_store.py -q`

### 1.3 Loop self-load + seed (US-3)
- [x] **`loop.py` (EDIT)**: ctor `+message_store: MessageStore | None = None`; `run()` start: `prior = await self._message_store.load() if self._message_store else []`; `messages = list(prior)`; insert system (if any); append user_input; `new_this_run = [messages[-1]]`. WHY-comment (Approach A + self-load seam + alternative considered)
  - DoD: no store → `prior=[]` (today's behavior); with store → prior prepended; `run()` ABC signature UNCHANGED
  - Verify: `mypy src` 0; `pytest tests/unit/agent_harness/orchestrator_loop/ -q`

### 1.4 Loop append + compaction-immune side-list (US-4)
- [x] **`loop.py` (EDIT)**: a `_record_new(msg, messages, new_this_run)` helper at EVERY real-message append site (assistant + tool result); at the LoopCompleted exit: `if self._message_store: await self._message_store.append(new_this_run, turn_num=state.transient.current_turn)`. System + prior NEVER re-appended; nothing on error/cancel. MHist + Last Modified
  - DoD: a 2nd send appends ONLY the new rows (no dup of prior/system); compaction-on run still persists verbatim (side-list)
  - Verify: `pytest tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py -q`

### 1.5 Wiring (US-5)
- [x] **`handler.py` (EDIT)**: in `build_handler` (the `DBCheckpointer` construction site per Day-0), construct `DBMessageStore(db, session_id, tenant_id)` + inject `message_store=...` into the loop ctor; subagent child loops inject NONE. MHist
  - DoD: the main-chat loop gets a store; fork/teammate child loops do not (prior=[])
  - Verify: `mypy src` 0; the integration test (1.7-equiv Day 2) exercises the wired path

### 1.6 Partition coverage (US-6, CONDITIONAL)
- [x] **`00XX_messages_forward_partitions.py` (NEW, only if D-partition-coverage found the cliff)**: forward monthly partitions for `messages` + `message_events` (mirror `0002` DDL); else SKIP + note in progress.md
  - DoD: `messages` accepts a row dated today + (if added) post-2026-07-01; Alembic head advances cleanly
  - Verify: `alembic upgrade head` (or the project's migration runner) green; a row insert in the current month succeeds

### 1.7 Backend gate (partial)
- [x] black + isort + flake8 clean · mypy `src` **0** · run_all **10/10** (check_llm_sdk_leak + wire 24) · the Day-1 unit tests pass
  - Verify: `cd backend && black . && isort . && flake8 . && mypy src && python scripts/lint/run_all.py`

---

## Day 2 — Backend tests (US-7) + full gate  ✅ DONE (pytest 2720 passed/5 skipped +8; mypy 0/372; run_all 10/10; flake8 clean)

### 2.1 Store unit tests (US-7 part 1)
- [x] **`test_message_store.py` (NEW)**: append `[user, assistant(+tool_calls), tool]` → load → equal (tool_calls round-trip); 2nd append → seq continues from MAX (monotonic, no UNIQUE violation); cross-tenant load → `[]` (鐵律); `db is None` → `load()==[]` / `append()` no-op
  - Verify: `pytest tests/unit/agent_harness/state_mgmt/test_message_store.py -q` → all pass

### 2.2 Loop unit test (US-7 part 2)
- [x] **`test_loop_multiturn_rehydration.py` (NEW)**: a fake in-memory `MessageStore` → `run()` (prior=[]) asserts `append` got `[user, assistant]` (new_this_run, NOT system); a 2nd `run()` (fake returns the prior) asserts the mock ChatClient saw the prior prepended
  - Verify: `pytest tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py -q` → all pass

### 2.3 Integration test (US-7 part 3)
- [x] **`test_chat_multiturn_context.py` (NEW)**: drive the chat path twice on one session with a recording mock ChatClient → send-2's messages CONTAIN send-1's user+assistant; a cross-tenant 2nd send does NOT see tenant-A history (isolation). Uses the `get_db_session` override (Risk Class C)
  - Verify: `pytest tests/integration/api/test_chat_multiturn_context.py -q` → all pass

### 2.4 Backend gate (full)
- [x] mypy `src` **0/370 + new files** · run_all **10/10** (24) · full pytest **2712+5skip + delta** · black/isort/flake8 clean · LLM-SDK-leak clean · NO frontend/codegen/mockup change (`diff styles-mockup.css` empty; Vitest 904 / mockup 51 UNCHANGED)
  - Verify: `cd backend && mypy src && pytest -q && python scripts/lint/run_all.py` + `cd frontend && git diff --stat src/styles-mockup.css` empty

---

## Day 3 — Drive-through (US-8) — real UI + real backend + real LLM (MANDATORY, multi-turn)

### 3.1 Clean restart (Risk Class E — `loop.py` + `handler.py` changed)
- [x] `Win32_Process` PID/PPID/StartTime sweep → kill stale/orphan uvicorn on :8000 → fresh no-`--reload` `api.main:app` sole owner + "startup complete" + pricing-loader wired; `MAIN_TRANSCRIPT_OBSERVER` on; Vite :3007 NOT stopped
  - DoD: fresh sole :8000 owner; a probe send → a `messages`-table row count > 0 (the writer fires) BEFORE the UI multi-turn test

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] real-LLM chat-v2 (Azure gpt-5.2, dev-login): turn 1 "What is the capital of France?" → "Paris"
- [x] **THE fix**: turn 2 (same session) "What is its population?" → resolves "it"→Paris (~2.1M), NOT "what does 'it' refer to" (the exact 57.126 failing case, now passing)
- [x] isolation: a NEW session "What is its population?" → asks for clarification (does NOT inherit Paris) — proves per-session scoping
- [x] (optional) a tool/`/skill` turn carries forward (tool_calls fidelity); `messages`-row count climbs per turn
- [x] per-control AP-4 walk + screenshots + observed-vs-intended → progress.md Day 3; **PASS** only if turn 2 resolves on real LLM

---

## Day 4 — CHANGE-094 + design note 38 + closeout

### 4.1 CHANGE-094
- [x] **`CHANGE-094-chatv2-live-multiturn-context.md`** (root cause + Approach A + `MessageStore` seam + dual-ledger note + drive-through + AD closed)

### 4.2 Design note 38 (spike — 8-pt gate)
- [x] **`38-chatv2-multiturn-rehydration-spike.md`** (new-domain spike: live-loop message persistence + rehydration; 8-pt quality gate: section header / file:line / decision matrix (A vs B vs C) / verification command / test fixture / open-invariant boundary (backfill, resume, consolidation, pg_partman) / rollback / 17.md cross-ref (`MessageStore` ABC — register the new contract))

### 4.3 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-multiturn-rehydration-spike` 0.60, 1st data point; parent-direct, agent_factor 1.0; ratio + KEEP/re-point) + progress.md final
- [x] Final gate sweep: mypy `src` **0** · run_all **10/10** (24) · pytest **2712+5 + delta** · Vitest **904** UNCHANGED · mockup **51** byte-identical · black/isort/flake8 clean · LLM-SDK-leak clean
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (minimal-touch; post-merge flip per the new §Sprint Closeout rule) · MEMORY.md pointer + subfile `project_phase57_127_*` · next-phase-candidates (**CLOSE `AD-ChatV2-Live-MultiTurn-Context`**; note dual-ledger + pg_partman + resume-persistence carryovers) · sprint-workflow matrix `chatv2-multiturn-rehydration-spike` 0.60 row
- [x] **Anti-pattern self-check** (retro Q5): AP-2 (store on 主流量, wired from build_handler) / AP-3 (one `state_mgmt` home) / AP-4 (real multi-turn context — drive-through proven LIVE) / AP-6 (no speculative `model`/`tokens_*`/backfill) / AP-8 (no bare message assembly — reuses `_message_to_dict`) / AP-11 (no `_v2` suffix) → 0 violations; v2 lints 10/10
- [x] PR (push + open) — **awaiting user confirm before `git push`** (destructive-confirm rule); CI → merge on green (gh-verified MERGED before main sync)
