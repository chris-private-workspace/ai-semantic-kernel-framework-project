# Sprint 57.127 Plan — chat-v2 live multi-turn context (rehydrate prior conversation into the live loop). Closes `AD-ChatV2-Live-MultiTurn-Context` — the real product bug the 57.126 drive-through surfaced: a follow-up message in an EXISTING session starts the loop WITHOUT the prior conversation, so the LLM loses context (turn 2 "its population?" couldn't resolve "it"→Paris). Root cause (grep-confirmed): `loop.run()` (`loop.py:~1983`) builds `messages` from scratch — system prompt + the NEW `user_input` ONLY — and the router never loads prior messages; the 57.125/126 `message_events` are persist-only for frontend replay/audit, NOT fed to the live loop; `state_data` EXCLUDES messages (`checkpointer.py:217`); the `messages` table EXISTS but has NO writer; only HITL-paused sessions rehydrate (via `metadata["resume_messages"]` + `messages_from_metadata`). **User decision (2026-06-16 AskUserQuestion): Approach A** — give the existing `messages` table a real writer (production-grade, O(N) storage; the path the `loop.py:248` SPIKE NOTE itself recommends) + rehydrate on follow-up. **Seam (refined past the Explore's `run(prior_messages=)` proposal): a NEW provider-neutral `MessageStore` ABC** (sibling to `Checkpointer`, bound to `(db, session_id, tenant_id)` at construction like `DBCheckpointer`), injected into the loop; the loop **self-loads** prior messages at `run()` start + **appends** the run's NEW messages at completion — so **`loop.run()`'s ABC signature is UNCHANGED** (no ripple to subagent fork/teammate callers or tests) and the router needs no reader. A compaction-immune `new_this_run` side-list keeps the durable ledger faithful (compaction edits the in-context `messages`, not the ledger). **Pure backend** (the frontend already continues the same `session_id` — 57.126); NO frontend/CSS/Vitest change. **Drive-through MANDATORY** (the exact 57.126 failing case: a 2-turn real chat where turn 2 references turn 1 must now resolve). CHANGE-094; **design note 38** (spike — new domain: live-loop message persistence + rehydration).

**Status**: Approved-to-execute (user 2026-06-16: "現在開始執行 AD-ChatV2-Live-MultiTurn-Context" → investigation surfaced a 3-way design fork → AskUserQuestion picked **Approach A — new messages-table writer**).
**Branch**: `feature/sprint-57-127-chatv2-live-multiturn-context`
**Base**: `main` HEAD `c1d3d1be` (post-#302 — the 57.126 merge `d4f1a580` + the chore-docs status-refresh `c1d3d1be`).
**Slice**: closes `AD-ChatV2-Live-MultiTurn-Context` (NEW in the 57.126 carryover; pre-existing product gap surfaced by the 57.126 drive-through). A standalone backend spike (no arc).
**Scope decisions**: (a) **Approach A** (messages-table writer) over B (reconstruct from `message_events`, ~80% fidelity — REJECTED: silently drops tool/system context = the looks-done-but-incomplete trap of `feedback_foundation_slice_verify_against_consumer`) and C (checkpoint-metadata, O(turns²)). (b) **Seam = a new `MessageStore` ABC self-loaded by the loop** (NOT a `loop.run(prior_messages=)` param — avoids the ABC-signature ripple to every caller). (c) **No `loop.run()` signature change**; **no migration for the table** (`messages` exists) — but Day-0 Prong-3 verifies partition coverage (0002 created partitions only through `2026_06`; if the table cliffs at 2026-07-01 a small forward-partition migration is added, since this sprint makes `messages` load-bearing). (d) **Pure backend** — ZERO frontend / CSS / Vitest / wire / codegen change. (e) Old sessions (no message rows) gracefully degrade to `prior=[]` (same as today; no backfill). (f) The run's NEW messages are persisted at clean completion (a compaction-immune side-list preserves verbatim fidelity); child loops (fork/teammate) inject NO store → unaffected. (g) User-facing behavior change (multi-turn context now works) → a real UI + real backend + real LLM **drive-through is MANDATORY**.

---

## 0. Background

### The bug (the 57.126 drive-through finding)

The 57.126 drive-through (real Azure gpt-5.2) logged: turn 1 "capital of France?" → "Paris" ✅; turn 2 "its population?" → the agent answered *"missing what 'it' refers to"* ❌. The same `session_id` was used (57.126 continuation works), but the agent had **no memory of turn 1**. Multi-turn chat is effectively single-turn for context.

### Root cause (grep-confirmed, Day-0 head-start — re-verified in §checklist 0.1)

| Layer | Reality (grep-verified on `main` HEAD `c1d3d1be`) | Anchor |
|-------|---------------------------------------------------|--------|
| Loop builds messages from scratch | `messages: list[Message] = []` → append system (if any) → append the new `user_input`. **No prior load.** | `loop.py:~1983-1986` |
| Router never loads prior | `_stream_loop_events` calls `loop.run(session_id, user_input, trace_context)`; no prior-message query before it | `router.py:~724` |
| `state_data` excludes messages | `_serialize_state_for_db` docstring "Excludes messages + pending_tool_calls"; `_deserialize` `messages=[]  # caller rehydrates` | `checkpointer.py:217/258` |
| `messages` table has no writer | every `Message(...)` in `backend/src` is the Cat-3 in-memory dataclass; **no `db.add(Message(...))`** for the ORM | `infrastructure/db/models/sessions.py:163-217` (ORM) |
| HITL-only rehydration | normal completed sessions never stash messages; only the deferred-pause branch writes `metadata["resume_messages"]` | `loop.py:~305-341` `messages_from_metadata`; `resume/service.py:~190` |

→ The fix must **rehydrate prior conversation into the live loop on a follow-up send**. Approach A persists each turn's Cat-3 `Message` objects to the `messages` table and loads them back at the next send.

### The design (Approach A — `MessageStore` ABC, loop self-load + append)

```
# Construction (per request, where DBCheckpointer is built — handler.py build_handler):
DBMessageStore(db, session_id, tenant_id)   # bound, mirrors DBCheckpointer
  → injected into AgentLoopImpl(message_store=...)   # optional, like checkpointer

# loop.run() start (loop.py ~1983):
prior = await self._message_store.load() if self._message_store else []   # ORDER BY sequence_num → _message_from_dict
messages = list(prior)
if self._system_prompt: messages.insert(0, Message(role="system", ...))    # system NEVER persisted (reconstructed)
messages.append(Message(role="user", content=user_input))
new_this_run = [messages[-1]]                                              # compaction-immune side-list

# during the run: whenever a real message is appended to `messages` (assistant / tool result),
#   ALSO append it to new_this_run (the ledger snapshot — immune to compaction editing `messages`)

# loop completion (the LoopCompleted yield site):
if self._message_store: await self._message_store.append(new_this_run, turn_num=state.transient.current_turn)
  # DBMessageStore.append: seq = MAX(sequence_num)+1.. for the session; db.add(Message(role, content=_message_to_dict(m), ...));
  #   best-effort begin_nested() SAVEPOINT (mirrors _persist_main_event); db None → no-op
```

**Why this seam (vs the Explore's `loop.run(prior_messages=)` param)**: a `run()` signature change ripples to the ABC (`orchestrator_loop/_abc.py`) + the impl + EVERY caller (router + subagent `fork.py`/`teammate.py` + the unit tests). Self-loading via an injected ABC (the loop already has `session_id` and an injected `Checkpointer`; `DBMessageStore` is bound to `tenant_id` at construction exactly like `DBCheckpointer` at `checkpointer.py:107-116`) keeps `run()` UNCHANGED and is symmetric (the store both reads and writes). Child loops (fork/teammate) inject NO store → `prior=[]`, no persistence — unaffected. **Alternative considered + rejected**: (i) router-loads-and-passes — the router only sees SSE events, not the internal `Message` list, so it can't write the ledger cleanly (would need the loop to expose messages); (ii) extend `Checkpointer` — conflates the durable-state snapshot with the message ledger (the SPIKE NOTE explicitly wants them separate to avoid `state_snapshots` JSONB bloat).

**Why a compaction-immune side-list**: Cat 4 compaction (`compactor/`) edits `state.transient.messages` in place (summarizes old turns). If we persisted the post-run `messages`, a compacted session would write the *summary* to the durable ledger, losing fidelity. `new_this_run` accumulates each NEW message at creation (before any compaction touches `messages`) → the ledger stays verbatim. The rehydrated `prior` still flows through compaction normally in-context (a long session self-compacts at the 75% threshold — expected).

### Dual-ledger note (not accidental duplication)

After this sprint two tables persist overlapping-but-distinct data: `message_events` (57.125/126 — serialized SSE frames, for the **frontend replay UI**) and `messages` (this sprint — Cat-3 `Message` objects, for **live-loop rehydration**). Different shapes, different consumers, both endorsed by the `loop.py:248` SPIKE NOTE. A future consolidation (one canonical ledger projecting both views) is a deferred AD, not this sprint.

### Ground truth (Day-0 head-start — direct reads + 2 Explore sweeps on `main` HEAD `c1d3d1be`; ALL re-verified in §checklist 0.1)

- `infrastructure/db/models/sessions.py:163-217` — `Message` ORM (`role` String(32), `content_type` String(32), `content` JSONB, `sequence_num`, `turn_num`, `model`/`tokens_in`/`tokens_out` nullable, `is_compacted`; composite PK `(id, created_at)`; UNIQUE `(session_id, sequence_num, created_at)`; RANGE(created_at) monthly partitions). Migration `0002_sessions_partitioned.py` created partitions `messages_2026_04/05/06` ONLY → **Day-0 Prong-3 verifies forward coverage**.
- `agent_harness/state_mgmt/_abc.py:~30-57` — `Checkpointer` ABC (`save`/`load`/`time_travel`) — the sibling pattern `MessageStore` mirrors.
- `agent_harness/state_mgmt/checkpointer.py:~94-150` — `DBCheckpointer(db, session_id, tenant_id)` bound-at-construction pattern to mirror; `:217` `_serialize_state_for_db` "Excludes messages".
- `agent_harness/orchestrator_loop/loop.py:~1974-1986` — `run()` impl (the message-seed site); `~305-341` `_message_to_dict`/`_message_from_dict`/`messages_from_metadata` (the row-serialization helpers to reuse); the LoopCompleted yield site (the append point); the ctor (`~397`, where `checkpointer` is injected → add `message_store`).
- `agent_harness/orchestrator_loop/_abc.py:~47-62` — `run()` ABC signature (UNCHANGED this sprint).
- `api/v1/chat/handler.py` — `build_handler` (where `DBCheckpointer` is constructed with db/session/tenant → construct `DBMessageStore` here too) — **Day-0 confirms db/session_id/tenant_id are all in scope at this site** (the key wiring uncertainty).
- `api/v1/chat/router.py:~570-603` — `_persist_main_event` (the best-effort SAVEPOINT tenant-scoped writer pattern to mirror); `~724` the `loop.run(...)` call (UNCHANGED).
- `infrastructure/db/repositories/session_repository.py:~123-131` — the tenant-scoped `SELECT ... WHERE id & tenant_id` pattern to mirror for `load()`.
- `agent_harness/_contracts/chat.py:~76-95` — the Cat-3 `Message` dataclass (`role`/`content`/`tool_calls`/`tool_call_id`/`name`/`metadata`).
- `compactor/` — Cat 4 compaction operates on `state.transient.messages` (rehydrated prior compacts normally; the side-list is immune).

**Baselines (57.126 closeout + #302)**: full pytest **2712+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/370** · run_all **10/10**. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-messagestore-wiring-site** — confirm `build_handler` (or wherever the loop + `DBCheckpointer` are constructed for the chat path) has `db` + `session_id` + `tenant_id` in scope to build a bound `DBMessageStore` (the key feasibility check for the self-load seam).
- **D-partition-coverage** (Prong 3) — verify whether `messages` (and `message_events`) partitions extend past `2026_06`; if they cliff at 2026-07-01, add a forward-partition migration (both tables are now load-bearing).
- **D-loop-completion-append-point** — confirm the single LoopCompleted yield site (and that max_turns/budget terminations route through it) so the append fires on every clean completion (not on error/cancel — acceptable).
- **D-message-helpers-roundtrip** — confirm `_message_to_dict`/`_message_from_dict` round-trip a full `Message` incl. `tool_calls`/`tool_call_id`/`name`/`metadata` (the ledger fidelity guarantee).
- **D-baselines** — re-assert the 6 gate baselines.

## 1. Sprint Goal

Close `AD-ChatV2-Live-MultiTurn-Context`: a follow-up message in an existing chat session now carries the prior conversation into the live loop. A NEW provider-neutral `MessageStore` ABC (`DBMessageStore` bound to `(db, session_id, tenant_id)`, mirroring `DBCheckpointer`) is injected into the main-chat loop; the loop **self-loads** prior `Message` objects from the `messages` table at `run()` start (ordered by `sequence_num`, via `_message_from_dict`) and **appends** the run's NEW messages (a compaction-immune side-list, serialized via `_message_to_dict`, `sequence_num` continuing from the session `MAX`, tenant-scoped, best-effort SAVEPOINT) at clean completion — so `loop.run()`'s ABC signature is UNCHANGED (no caller ripple) and child loops (no store injected) are unaffected. Pure backend (the frontend already continues the same `session_id`); ZERO frontend/CSS/Vitest/wire/codegen change; no table migration (a forward-partition migration only if Day-0 finds the table cliffs at 2026-07). Proven by backend unit tests (store load/append round-trip + seq-from-MAX + tenant isolation + db-None no-op), a backend integration test (a 2-send flow → the 2nd run's LLM call receives the prior messages), **and a MANDATORY real UI + real backend + real LLM drive-through** (the exact 57.126 case: "capital of France?"→"Paris", then "its population?" → now resolves "it"→Paris, ~2.1M). CHANGE-094; design note 38 (spike).

## 2. User Stories

- **US-1** (ABC): 作為 Cat-1 provider-neutral loop，我希望有一個 `MessageStore` ABC（`load()` + `append(messages, *, turn_num)`，綁定 `(session_id, tenant_id)` 於建構，sibling to `Checkpointer`），以便 loop 透過注入的抽象做訊息持久化/重載而不直接碰 DB（保持中性）。
- **US-2** (impl): 作為持久化層，我希望 `DBMessageStore` 實作 `load`（`SELECT ... WHERE session_id & tenant_id ORDER BY sequence_num` → `_message_from_dict`）+ `append`（seq 從 `MAX(sequence_num)` 續，`_message_to_dict` 寫 `content` JSONB，best-effort SAVEPOINT，mirror `_persist_main_event`；`db is None` → no-op/[]），以便忠實 round-trip Cat-3 `Message`（含 tool_calls）。
- **US-3** (loop self-load): 作為 loop，我希望 `run()` 開頭 `prior = await self._message_store.load()`（無 store → []）並以 `prior` seed `messages`（system 永遠重建、不持久化；user_input append），以便 follow-up 帶前文。
- **US-4** (loop append + side-list): 作為 loop，我希望維護一個 compaction-immune `new_this_run` side-list（每新增真實 message 時同步 append），並在 clean completion 呼叫 `message_store.append(new_this_run, turn_num=current_turn)`，以便 durable ledger 保留 verbatim（不被 compaction 改寫），且不重複持久化 prior/system。
- **US-5** (wiring): 作為 chat 主流量，我希望在建構 loop + `DBCheckpointer` 的同一處（`build_handler`）建構並注入 `DBMessageStore(db, session_id, tenant_id)`；subagent child loops 不注入 store（prior=[]，零影響）。
- **US-6** (partition coverage): 作為現在開始寫入 `messages` 的主流量，我希望 Day-0 確認分區涵蓋到當前月；若 cliff 在 2026-07，加一個 forward-partition migration（`messages` + `message_events`，mirror 0002 DDL），以便寫入不在 7/1 失敗。
- **US-7** (tests): backend 單元（store load/append round-trip incl. tool_calls / seq-from-MAX / **cross-tenant load → []（鐵律）** / db-None no-op）+ 整合（2-send → 2nd run 的 LLM 呼叫收到 prior messages，mock ChatClient 擷取）+ loop 單元（注入 fake store → seed prior + append new_this_run）。
- **US-8** (drive-through — MANDATORY): 真 UI + 真後端 + 真 Azure：「capital of France?」→「Paris」→「its population?」→ **現在解析「it」→Paris（~2.1M），非「what is 'it'」**；逐控件 AP-4 walk + 截圖 + 實際-vs-預期 → progress.md。
- **US-9** (closeout): CHANGE-094 + design note 38（spike，8-pt gate）+ 收尾（retro + calibration + navigators + **CLOSE the AD**）。

## 3. Technical Specifications

### 3.0 Architecture (new ABC + impl + loop self-load/append + wiring; NO run()-signature / frontend / CSS / wire / codegen change)

```
# NEW
backend/src/agent_harness/state_mgmt/message_store.py   (NEW): MessageStore ABC + DBMessageStore (load/append, bound to db+session+tenant)
# EDIT
backend/src/agent_harness/state_mgmt/_abc.py            (EDIT, OR co-locate ABC in message_store.py — Day-0 picks per existing convention)
backend/src/agent_harness/orchestrator_loop/loop.py     (EDIT): ctor +message_store; run() self-load prior + seed; new_this_run side-list; append at completion
backend/src/api/v1/chat/handler.py                      (EDIT): build_handler constructs + injects DBMessageStore (mirror DBCheckpointer site)
# tests
backend/tests/unit/agent_harness/state_mgmt/test_message_store.py   (NEW): load/append round-trip + seq-from-MAX + cross-tenant [] + db-None
backend/tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py (NEW): inject fake store → seed prior + append new_this_run
backend/tests/integration/api/test_chat_multiturn_context.py        (NEW): 2-send → 2nd run's ChatClient receives prior messages
# migration (CONDITIONAL — only if Day-0 Prong-3 finds the cliff)
backend/src/infrastructure/db/migrations/versions/00XX_messages_forward_partitions.py (NEW, conditional): forward monthly partitions for messages + message_events
# docs
claudedocs/4-changes/feature-changes/CHANGE-094-chatv2-live-multiturn-context.md (NEW)
docs/03-implementation/agent-harness-planning/38-chatv2-multiturn-rehydration-spike.md (NEW design note)
# UNTOUCHED: loop _abc.py run() signature · router.py loop.run() call · frontend/** · styles-mockup.css · events.py/sse.py/codegen (wire 24)
```

### 3.1 `MessageStore` ABC + `DBMessageStore` (US-1/2) — `message_store.py`

- **`MessageStore(ABC)`**: `async def load(self) -> list[Message]`; `async def append(self, messages: list[Message], *, turn_num: int) -> None`. Bound to `(session_id, tenant_id)` at construction (the impl ctor takes `db, session_id, tenant_id`) — mirrors `DBCheckpointer`. Provider-neutral (imports only Cat-3 `Message` + the ORM via the impl; the ABC imports neither DB nor a provider).
- **`DBMessageStore(db, session_id, tenant_id)`**:
  - `load()`: `select(Message).where(Message.session_id == sid, Message.tenant_id == tid).order_by(Message.sequence_num)` → `[_message_from_dict(row.content) for row in rows]`. `db is None` → `[]`. (Cross-tenant/unknown → `[]` naturally — the tenant filter.)
  - `append(messages, *, turn_num)`: if `db is None or not messages` → return. `start = await _max_seq(...) + 1` (`SELECT COALESCE(MAX(sequence_num),0)` for the session, tenant-scoped); for `i, m in enumerate(messages)`: `db.add(Message(id=uuid4(), session_id, tenant_id, sequence_num=start+i, turn_num, role=m.role, content_type=_content_type(m), content=_message_to_dict(m)))`. Best-effort `async with db.begin_nested():` (mirror `_persist_main_event`; swallow + `logger.exception`). `model`/`tokens_*` left null this slice (optional metadata; populate later if a need appears — YAGNI).
  - `_content_type(m)`: `"text"` when `content` is a str else `"blocks"` (a coarse marker; the full payload lives in `content` JSONB via `_message_to_dict` — `role` column is for filtering/indexing).
- Reuse `_message_to_dict`/`_message_from_dict` from `loop.py` (Day-0 confirms they round-trip `tool_calls`/`tool_call_id`/`name`/`metadata`); if they're private to `loop.py`, expose via a small shared module OR import (Day-0 picks the least-ripple path per the existing import graph).

### 3.2 Loop self-load + append + side-list (US-3/4) — `loop.py`

- **ctor**: add `message_store: MessageStore | None = None` (optional, beside `checkpointer`). Store on `self._message_store`.
- **`run()` start** (`~1983`): `prior = (await self._message_store.load()) if self._message_store is not None else []`; `messages = list(prior)`; `if self._system_prompt: messages.insert(0, Message(role="system", content=self._system_prompt))`; `messages.append(Message(role="user", content=user_input))`; `new_this_run: list[Message] = [messages[-1]]`.
- **during the run**: at each site that appends a real `Message` to `messages` (the assistant response + each tool-result message), ALSO `new_this_run.append(msg)`. (Day-0 enumerates the append sites; a small helper `self._record_new(msg, messages, new_this_run)` keeps it DRY + avoids a missed site.)
- **completion** (the LoopCompleted yield site, on end_turn / max_turns / budget — Day-0 confirms the single exit): `if self._message_store is not None: await self._message_store.append(new_this_run, turn_num=state.transient.current_turn)`. NOT on error/cancel (acceptable — a failed turn need not be remembered). System prompt + `prior` are NEVER re-appended.
- **No `run()` signature change** → `orchestrator_loop/_abc.py` + the router call + subagent factories + tests UNCHANGED.

### 3.3 Wiring (US-5) — `handler.py`

- In `build_handler` (the site that constructs the loop + `DBCheckpointer` for the chat path): construct `DBMessageStore(db, session_id, tenant_id)` and pass to the loop ctor (`message_store=...`). Day-0 confirms db/session_id/tenant_id are all in scope here (the feasibility check); if `session_id` is generated later in the router, the construction moves to wherever `DBCheckpointer` is built (they must co-locate). Subagent dispatch (fork/teammate) builds child loops WITHOUT a store → `prior=[]`, no append.

### 3.4 Partition coverage (US-6) — conditional migration

- Day-0 Prong-3: `\d+ messages` / grep migrations for partition coverage. If partitions exist only through `2026_06` (cliff 2026-07-01), add `00XX_messages_forward_partitions.py` creating forward monthly partitions (e.g. `2026_07`..`2027_06`) for BOTH `messages` AND `message_events` (both now load-bearing; mirror `0002_sessions_partitioned.py` DDL). If a later migration already extended them → SKIP (note in progress.md). The systemic fix (pg_partman automation) stays a tracked infra AD.

### 3.5 Tests (US-7)

- **`test_message_store.py`** (unit): append `[user, assistant(+tool_calls), tool]` → load → equal `Message`s (incl. tool_calls round-trip); a 2nd append continues `sequence_num` from MAX (no collision); a load with the WRONG tenant_id → `[]` (multi-tenant 鐵律); `db is None` → `load()==[]` / `append()` no-op. Uses the test DB session fixture (Risk Class C — autouse reset if a singleton is touched).
- **`test_loop_multiturn_rehydration.py`** (loop unit): inject a fake in-memory `MessageStore` (records appends, returns a seeded prior) → `run()` once with prior=[] → assert `append` called with `[user, assistant]` (new_this_run, not system); `run()` again with the fake now returning the prior → assert the LLM client (mock) saw the prior messages prepended.
- **`test_chat_multiturn_context.py`** (integration): drive `_stream_loop_events` (or the chat POST) twice on one session with a mock/echo ChatClient that records the messages it receives → assert send-2's recorded messages CONTAIN send-1's user+assistant; cross-tenant second send → does NOT see tenant-A's history. (Mirrors `test_main_transcript_persist.py` harness.)

### 3.6 Drive-through (US-8) — real UI + real backend + real LLM (MANDATORY)

1. Clean restart (Risk Class E — `loop.py` + `handler.py` changed; `Win32_Process` PID/PPID/StartTime sweep; fresh sole :8000 owner + startup log; `MAIN_TRANSCRIPT_OBSERVER` on). Vite :3007 (node) NOT stopped.
2. A real-LLM chat in chat-v2 (Azure gpt-5.2): turn 1 "What is the capital of France?" → expect "Paris".
3. **The fix**: turn 2 (same session) "What is its population?" → the agent **resolves "it"→Paris and answers ~2.1M** (NOT "what does 'it' refer to"). This is the exact 57.126 failing case, now passing.
4. Optionally verify a tool/`/skill` turn carries forward too (tool_calls fidelity). Verify a NEW session does NOT inherit the prior session's context (isolation).
5. `GET /sessions/{id}/events` + a direct `messages`-table count check (rows accrue per turn). Per-control AP-4 walk; screenshots + observed-vs-intended → progress.md. "drive-through PASS" only if step 3 actually passes on real LLM.

### 3.7 What is explicitly NOT done

Reconstructing history from `message_events` (the rejected Approach B); checkpoint-metadata for normal sessions (the rejected Approach C); a backfill tool for pre-57.127 sessions (graceful degrade to `prior=[]`); persisting messages for error/cancelled runs; the resume path's message persistence (a pre-existing 57.125 gap — separate AD); a `messages`/`message_events` consolidation (dual-ledger is intentional); pg_partman partition automation (systemic infra AD); `model`/`tokens_*` population on message rows (YAGNI); ANY frontend / CSS / Vitest / wire / codegen change.

### 3.8 Validation (US-1..US-9)

Gates: mypy `src` **0/370 + the new files** (re-assert 0) · run_all **10/10** (wire **24** unchanged — no codegen) · full pytest **2712+5skip + backend delta** (store + loop + integration tests) · Vitest **904 UNCHANGED** (no FE change) · mockup **51 UNCHANGED** (`diff styles-mockup.css` empty) · `black`/`isort`/`flake8` clean · LLM-SDK-leak lint clean (the new `message_store.py` imports no provider). Plus the §3.6 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/state_mgmt/message_store.py` | NEW — `MessageStore` ABC + `DBMessageStore` (load/append, bound to db+session+tenant, best-effort SAVEPOINT) |
| 2 | `backend/src/agent_harness/state_mgmt/_abc.py` | EDIT (OR co-locate ABC in #1 per Day-0 convention) — register `MessageStore` if `Checkpointer` lives here |
| 3 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT — ctor `+message_store`; `run()` self-load prior + seed; `new_this_run` side-list; append at completion |
| 4 | `backend/src/api/v1/chat/handler.py` | EDIT — `build_handler` constructs + injects `DBMessageStore` (mirror `DBCheckpointer` site) |
| 5 | `backend/tests/unit/agent_harness/state_mgmt/test_message_store.py` | NEW — load/append round-trip + seq-from-MAX + cross-tenant [] + db-None |
| 6 | `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py` | NEW — fake store: seed prior + append new_this_run |
| 7 | `backend/tests/integration/api/test_chat_multiturn_context.py` | NEW — 2-send → 2nd run sees prior; cross-tenant isolation |
| 8 | `backend/src/infrastructure/db/migrations/versions/00XX_messages_forward_partitions.py` | NEW (CONDITIONAL — only if Day-0 Prong-3 finds the cliff) — forward partitions for messages + message_events |
| 9 | `claudedocs/4-changes/feature-changes/CHANGE-094-chatv2-live-multiturn-context.md` | NEW — change record |
| 10 | `docs/03-implementation/agent-harness-planning/38-chatv2-multiturn-rehydration-spike.md` | NEW — spike design note (8-pt gate) |
| — | loop `_abc.py` `run()` sig · `router.py` loop.run() call · `frontend/**` · `styles-mockup.css` · codegen/wire | **UNTOUCHED** |

## 5. Acceptance Criteria

1. **ABC + impl**: a provider-neutral `MessageStore` ABC + `DBMessageStore` bound to `(db, session_id, tenant_id)`; `load()` returns prior `Message`s ordered by `sequence_num`; `append()` writes new rows with `sequence_num` continuing from the session MAX; both best-effort + `db is None`-safe.
2. **Loop self-load**: `run()` seeds `messages` with `prior` (no store → `[]`), system reconstructed (never persisted), user_input appended; `loop.run()`'s ABC signature UNCHANGED.
3. **Loop append + fidelity**: at clean completion the run's NEW messages (a compaction-immune side-list) are appended verbatim (tool_calls preserved); system + prior are NOT re-persisted; nothing persisted on error/cancel.
4. **Wiring**: the main-chat loop gets a `DBMessageStore`; subagent child loops do NOT (prior=[]; unaffected).
5. **Multi-tenant** (鐵律): `load`/`append` filter by `tenant_id`; a cross-tenant load returns `[]` (test-proven).
6. **Partitions**: writes land in the current month's partition; if Day-0 found a 2026-07 cliff, a forward-partition migration ships (messages + message_events).
7. **Pure backend**: `diff styles-mockup.css` empty; Vitest 904 + mockup 51 UNCHANGED; wire 24; no codegen/table-migration (beyond the conditional partition one).
8. Gates: mypy 0 · run_all 10/10 (24) · pytest 2712+5 + backend delta · black/isort/flake8 clean · LLM-SDK-leak clean.
9. **Drive-through PASS (MANDATORY, real UI + backend + LLM)**: turn 1 "capital of France?"→"Paris"; turn 2 "its population?" → resolves "it"→Paris (~2.1M), NOT "what is 'it'"; a new session does NOT inherit context; screenshots + observed-vs-intended in progress.md. (NOT gate-only.)
10. `AD-ChatV2-Live-MultiTurn-Context` CLOSED; CHANGE-094 + design note 38; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `MessageStore` ABC (load/append, bound) (`message_store.py` / `_abc.py`)
- [ ] US-2 `DBMessageStore` (load ORDER BY seq + `_message_from_dict`; append seq-from-MAX + `_message_to_dict` + SAVEPOINT; db-None safe) (`message_store.py`)
- [ ] US-3 loop self-load prior + seed (`loop.py run()`)
- [ ] US-4 loop `new_this_run` side-list + append at completion (compaction-immune; no re-persist) (`loop.py`)
- [ ] US-5 `build_handler` constructs + injects `DBMessageStore`; child loops none (`handler.py`)
- [ ] US-6 partition coverage verified; conditional forward-partition migration
- [ ] US-7 tests: store unit (round-trip / seq / cross-tenant [] / db-None) + loop unit (fake store) + integration (2-send sees prior; isolation)
- [ ] US-8 drive-through (multi-turn real chat: "it"→Paris resolves; new-session isolation; screenshots; MANDATORY)
- [ ] US-9 CHANGE-094 + design note 38 + closeout (retro + calibration + navigators + CLOSE the AD)

## 7. Workload Calibration

- Scope class **`chatv2-multiturn-rehydration-spike` 0.60** (NEW — a new-domain backend spike: a new provider-neutral ABC + a `DBMessageStore` impl + a loop message-lifecycle touch (self-load at `run()` start + a compaction-immune side-list + append at completion) + `build_handler` wiring + tests + a mandatory drive-through. Closest classes: `subagent-child-loop-spike` 0.60 + `verification-into-loop-spike` 0.60 (both new-domain loop.py-core touches reusing proven injected-ABC patterns). The new ABC + the dedup/seq/side-list precision put it at 0.60, NOT a pure-wiring 0.55. **Ceremony-floor note** (57.120/122/123): a full-ceremony parent-direct sprint WITH a mandatory drive-through + a design note does NOT drop below ~0.55 even for bounded code.)
- **Agent-delegated: no** (parent-direct — the message-lifecycle dedup (don't re-persist prior/system), the compaction-immune side-list, the seq-from-MAX ordering, the self-load-vs-param seam, and the tenant-scoped best-effort writer are precise correctness-critical logic best hand-authored + self-verified). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~11 hr (Day-0 三-prong + wiring-site + partition + helper-roundtrip verify ~1.5 · `MessageStore` ABC + `DBMessageStore` ~1.5 · loop self-load + side-list + append + ctor ~2.0 · `build_handler` wiring ~0.5 · conditional partition migration ~0.5 · store unit + loop unit + integration tests ~2.5 · drive-through + clean restart ~1.5 · CHANGE-094 + design note 38 + closeout ~1.5) → class-calibrated commit ~6.6 hr (mult 0.60). Day-4 retro Q2 verifies (`chatv2-multiturn-rehydration-spike` 1st data point; flag if the loop append-site enumeration or the integration test over-runs).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **`build_handler` lacks session_id/tenant_id/db at the loop-construction site** (self-load seam infeasible) | **Day-0 D-messagestore-wiring-site** confirms FIRST; `DBCheckpointer` is already built bound to (db, session, tenant) → the same site builds `DBMessageStore`; if `session_id` is router-generated, co-locate the construction where `DBCheckpointer` is built |
| **Double-persisting prior/system on each send** (history grows quadratically, duplicate rows) | persist ONLY `new_this_run` (the user_input + this run's assistant/tool messages); system NEVER persisted (reconstructed); prior NEVER re-appended; a store test asserts a 2nd send adds only the new rows |
| **Compaction clobbers ledger fidelity** (persisting the summarized `messages`) | a compaction-immune `new_this_run` side-list captures each new message at creation (before compaction edits `messages`); a loop test with compaction on asserts verbatim rows |
| **Missed message-append site** (a tool-result message not recorded → ledger gap) | a single `_record_new(msg, messages, new_this_run)` helper at every append site; Day-0 enumerates the sites; the integration test asserts the full prior (user+assistant+tool) reloads |
| **`sequence_num` collision across sends** | `append` seeds from `MAX(sequence_num)` for the session (mirrors the 57.126 main_seq fix); the UNIQUE `(session_id, sequence_num, created_at)` would surface a collision → a test drives 2 sends and asserts monotonic seq |
| **Partition cliff 2026-07-01** (writes fail) | Day-0 Prong-3 verifies coverage; conditional forward-partition migration (messages + message_events); the systemic pg_partman fix is a tracked infra AD |
| **Multi-tenant leak** (cross-tenant rehydration) | `load`/`append` filter by `tenant_id`; bound at construction; a cross-tenant load test asserts `[]` (鐵律) |
| **`run()` signature ripple** (touching the ABC breaks subagent/test callers) | AVOIDED by the self-load seam — `run()` signature UNCHANGED; only the ctor gains an optional `message_store` |
| **Token cost of replaying a long history** | expected + bounded by Cat 4 compaction (75% threshold self-compacts a long rehydrated history); no special handling (the alternative — losing context — is the bug) |
| **`_message_to_dict` private to loop.py** | Day-0 D-message-helpers-roundtrip picks the least-ripple exposure (import vs a small shared module); they already round-trip full Messages for HITL resume |
| **Risk Class E** — stale `--reload` backend serves pre-edit `loop.py`/`handler.py` during the drive-through | clean restart (`Win32_Process` PID/PPID/StartTime sweep; orphan spawn-workers on :8000); confirm fresh sole owner + startup log + a `messages`-row count climbing before trusting the UI |
| **Risk Class C** — test DB session/singleton across event loops | the new tests use the integration `get_db_session` override / autouse reset; the store binds to the passed `db` (no module singleton) |
| **Test counts move** | document exact deltas in the retro; the gate asserts the finals |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Approach B / C** (reconstruct from `message_events` / checkpoint-metadata) — rejected by the user decision.
- **Backfill for pre-57.127 sessions** — graceful degrade (`prior=[]`); a backfill-from-`message_events` tool is a follow-on if old-session continuity is needed.
- **Persisting error/cancelled runs** — only clean completions append (a failed turn need not be remembered).
- **The resume path persisting messages** — a pre-existing 57.125 gap (`AD-ChatV2-Resume-Transcript-Persistence`); separate.
- **`messages`/`message_events` consolidation** — the dual-ledger is intentional (different consumers); a future canonical-ledger AD.
- **pg_partman partition automation** — the systemic fix for all partitioned tables; an infra AD (this sprint only adds forward partitions if cliffing).
- **`model`/`tokens_*` on message rows** — YAGNI (null this slice).
- **ANY frontend / CSS / Vitest / wire / codegen change** (pure backend; the frontend already continues the session — 57.126).
