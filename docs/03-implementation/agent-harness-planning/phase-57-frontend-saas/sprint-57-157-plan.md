# Sprint 57.157 Plan — Scheduler: cross-burst auto-continue for unfinished plans

**Summary**: Delivers **cross-burst auto-continue** — when a chat send's loop burst ends at the per-send `max_turns=8` ceiling (`stop_reason="max_turns"`) but the durable task plan (`write_todos`) still has unfinished todos, the SSE generator automatically re-runs the loop for the next burst instead of closing the stream and forcing the user to type "continue". This directly attacks the reality-audit §9 "long-lived personal agent 5% — per-session `max_turns=8`" short-life ceiling. Closes `AD-TaskPrimitive-Scheduler-Phase58` (the 57.140 task-primitive carryover; prerequisites — durable spine 57.140 + DAG 57.156 + cross-burst rehydration 57.127 — all shipped). Key scope decision: an **inline bounded outer-`while`** in the `_stream_loop_events` SSE generator (NOT a background job), **default OFF** env-gated (byte-identical when off), bounded by a NEW **max-bursts counter** (default 3). Drive-through is **MANDATORY** (chat-v2 user-facing). A design note (60) is **required** (spike sprint).

**Status**: Approved-to-execute (user AskUserQuestion pick "Task Scheduler (推薦)" 2026-07-06, under the engine-debt program kickoff — clear 7 engine-internal ranges first, kickoff = Scheduler)
**Branch**: `feature/sprint-57-157-scheduler-cross-burst`
**Base**: `main` HEAD `aa0dcf13` (#369 chore branch-protection doc fix merged)
**Slice**: closes `AD-TaskPrimitive-Scheduler-Phase58` (standalone; the Task-primitive range's flagship item in the engine-debt program)
**Scope decisions**: (a) **inline** outer-`while` in `_stream_loop_events`, NOT a `main.py`-style background job — the SSE connection is already open streaming this session's events, so continuation stays on the same stream (Agent-2 recon: a background poller would orphan it); (b) **default OFF** env `CHAT_SCHEDULER_AUTO_CONTINUE` → byte-identical single-burst behavior when off (spike discipline, mirrors 57.136-139/146/155); (c) bounded by NEW `CHAT_SCHEDULER_MAX_BURSTS` **default 3** (3×8 = ≤24 turns/send); (d) continue-condition = `stop_reason=="max_turns"` AND `any(todo.status != "completed")` via a 2nd `make_chat_todo_store` in router scope — **NO** `LoopCompleted` contract change / **NO** wire schema change; (e) re-invoke `loop.run(session_id, user_input=<continuation nudge>)` — reuses the FREE ledger (57.127) + `## Active Plan` (57.156) rehydration; **loop.py UNTOUCHED**.

---

## 0. Background

### The gap (`AD-TaskPrimitive-Scheduler-Phase58`)

- Sprint 57.140 shipped a durable task plan (`write_todos` + `session_todos`) and 57.156 added DAG dependencies, but a multi-step plan that needs **more than 8 turns** stalls at the per-send `max_turns=8` ceiling.
- On that ceiling the burst ends with `LoopCompleted(stop_reason="max_turns")` → the SSE stream closes → the user must **manually** send "continue" to get the next burst.
- Nothing in the repo auto-continues (grep-confirmed): the router only post-drives `handoff` / `awaiting_approval`, never `max_turns`.

### Why it matters (the missing capability)

- The agent cannot autonomously finish a task that needs multiple bursts; every 8 turns a human must intervene and type "continue", breaking the "Autonomous — self-organize, plan, execute, retry" agent-team design principle (#4).
- This is the direct code source of the reality-audit §9 "long-lived personal agent ~5% — per-session `max_turns=8`" finding.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `aa0dcf13`) | Anchor |
|-------|-------------------------------------|--------|
| max_turns ceiling | chat burst cap = **8** (loop ctor default is 50) | `api/v1/chat/handler.py:771` |
| burst termination | ceiling → `LoopCompleted(stop_reason="max_turns")` then `return` | `orchestrator_loop/loop.py:2138-2145` |
| distinguishable | `"max_turns"` vs `"end_turn"` are distinct stop_reasons | `orchestrator_loop/termination.py:55-56` |
| no auto-continue | router `_stream_loop_events` has NO `max_turns` branch (only handoff/awaiting_approval) | `api/v1/chat/router.py:888-1158` |
| one send = one burst | one POST → one `loop.run()` generator | `api/v1/chat/router.py:825-829` |
| plan completeness | NO boolean helper; `any(t.status != "completed")` is the signal | `_contracts/todo.py:51,138` |
| todo load | `DBTodoStore.load()` bound to (session_id, tenant_id) | `state_mgmt/todo_store.py:94` |
| free rehydration | `run()` reloads ledger + re-injects `## Active Plan` on EVERY call | `loop.py:1990-2003` |
| max-bursts guard | **NONE exists** — must be added | (grep 0 hits) |

→ The fix = an inline bounded outer-loop in the SSE generator: on `max_turns` + unfinished plan, re-invoke `loop.run()` up to N bursts; reuse the existing free rehydration; add the one missing piece (a max-bursts bound). `loop.py` stays untouched.

### The design (backend-only: 1 pure predicate + router outer-loop + 2 settings + tests)

```
# api/v1/chat/router.py :: _stream_loop_events (outer-loop wrap of the single loop.run)
# KEY (Day-0 D-router-loopcompleted-shape): loop_end yields at :878 (BEFORE the closeout
# block :888). The block does billing (EVERY burst — real token spend) + quota/SLA/audit/
# handoff (FINAL burst only — reused reservation / "completed" audit are once-per-send).
bursts = 0
user_input = req.message
while True:
    continue_after = False
    async for event in loop.run(session_id, user_input, trace_context):
        ... subagent flush / serialize (skip None) / active_skill inject ...
        cont = False
        if isinstance(event, LoopCompleted) and settings.chat_scheduler_auto_continue:
            todos = (await make_chat_todo_store(db, session_id, tenant_id).load()) or []
            cont = should_continue_plan(enabled=True, stop_reason=event.stop_reason,
                                        todos=todos, bursts_used=bursts,
                                        max_bursts=settings.chat_scheduler_max_bursts)
        if not cont:                                 # normal path (incl. the FINAL burst)
            if main_transcript_on: persist(:869-877)
            yield sse(event)                         # :878 — the terminal loop_end streams here
        if isinstance(event, LoopCompleted):
            enqueue_burst_billing(event, compaction_*)   # EVERY burst (llm/verification/compaction)
            if cont:
                continue_after = True; break         # swallow: skip :878 + quota/SLA/audit/handoff
            ... quota reconcile / SLA / audit / handoff ...   # FINAL burst only
            break
        ... per-event tool_call billing ...
    if not continue_after: break
    bursts += 1
    user_input = CONTINUATION_NUDGE                  # a real user turn; ledger-persisted (57.127)
    # next burst: loop.run() self-rehydrates ledger + Active Plan (57.127 + 57.156) for free

# orchestrator_loop/scheduler.py (NEW) :: pure, unit-testable
def should_continue_plan(*, enabled, stop_reason, todos, bursts_used, max_bursts) -> bool:
    return (enabled and stop_reason == TerminationReason.MAX_TURNS.value
            and bursts_used < max_bursts
            and any(t.status != "completed" for t in todos))
```

**Why inline over a background job**: the SSE connection is already open and streaming this session's events; an inline outer-loop keeps the continuation on the same stream (the user sees one continuous turn-stream + one final `loop_end`), whereas a `main.py`-style poller would orphan the continuation off the live connection and lose the "finished within one send" UX. **Why swallow the intermediate `loop_end`**: keeps the frontend transparent — it renders a continuous stream and one terminal frame, so **no FE change and no wire-schema change** are needed.

### Ground truth (recon head-start — code read on `main` HEAD `aa0dcf13`; ALL re-verified §checklist 0.1)

- `api/v1/chat/router.py:825-829` — the single `async for event in loop.run(...)` that becomes the outer-loop body.
- `api/v1/chat/router.py:888-1158` — the `LoopCompleted` handling block + `break`; the swallow/continue decision hooks here.
- `api/v1/chat/router.py:263-330` — router already has `session_id` / `tenant_id` / `db` in scope → can call `make_chat_todo_store` a 2nd time (recon Agent-2).
- `api/v1/chat/_category_factories.py` — `make_chat_todo_store(db, session_id, tenant_id)` factory (per `todo_store.py:41` header).
- `orchestrator_loop/termination.py:56` — `TerminationReason.MAX_TURNS.value == "max_turns"`.
- `_contracts/todo.py:51` — `TodoStatus = Literal["pending","in_progress","completed"]`.
- `loop.py:1990-2003` — free ledger + Active-Plan rehydration on every `run()`.
- Sibling background-job pattern (NOT used, documented as rejected alternative): `main.py:342-400`.

**Baselines (57.156 closeout)**: pytest 3139/6skip · wire 26 · Vitest 925 · mockup 51 · mypy `src` 399/0 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-router-loopcompleted-shape** — re-read `router.py:888-1158` to confirm the exact `LoopCompleted` handler + `break` structure the outer-loop wraps (the recon summarized it; verify the real control flow + any `awaiting_approval` / `handoff` early-returns that must be preserved inside the outer-loop).
- **D-todo-store-factory** — grep `make_chat_todo_store` signature in `_category_factories.py` + confirm router scope has the args (`db`/`session_id`/`tenant_id`) at the seam.
- **D-continuation-persist** — confirm `loop.run()` appends + persists the `user_input` as a user turn (`loop.py:2005` + 57.127 MessageStore) → the continuation nudge WILL land in the ledger; decide the nudge text so rehydration stays coherent.
- **D-settings-pattern** — confirm the `chat_*` settings live in `core/config/__init__.py` read via `get_settings()` per-request (NOT the raw-env 57.135 background-job pattern — per-request `get_settings()` is correct here since settings are startup-fixed).
- **D-terminal-reemit** — verify swallowing the intermediate `loop_end` and re-emitting the real terminal frame at the end does not double-emit or drop the final `stop_reason` the FE store consumes.

## 1. Sprint Goal

Deliver env-gated cross-burst auto-continue so a multi-step plan that needs >8 turns finishes within a single chat send (bounded by a max-bursts counter), **PROVEN** by: all gates green (pytest / mypy `src` / run_all / Vitest / mockup / build / lint / LLM-SDK-leak) **AND** a MANDATORY drive-through (real chat-v2 + real Azure gpt-5.2: with the env enabled, a task requiring >8 turns runs multiple bursts automatically — no manual "continue" — and the DAG plan reaches all-completed on one send; with the env off, behavior is byte-identical single-burst). Produces **CHANGE-124** + **design note 60** (spike).

## 2. User Stories

- **US-1** (auto-continue core): 作為 operator，我希望一個多步任務在 8 turns 用完但 plan 還沒完成時 agent 自動繼續下一 burst，以便我不用每 8 turns 手動敲一次「continue」。
- **US-2** (bounded safety): 作為 platform owner，我希望自動續跑有明確 max-bursts 上限、且每 burst 的 `max_turns`/`token_budget` cap 不變，以便不會無限迴圈或失控燒 token。
- **US-3** (opt-in default-off): 作為 platform owner，我希望此功能預設關閉、由 env 開啟，以便不悄悄改變所有租戶的成本 / 延遲。
- **US-4** (drive-through, MANDATORY): 作為 user，我希望在真 chat-v2 開啟 env 後，一個 >8-turn 的多步 DAG plan 在單次 send 內自動跑完，無需手動 continue。
- **US-5** (closeout): design note 60 + CHANGE-124 + calibration + navigators + AD closed.

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO wire / NO codegen / NO frontend)

```
NEW   orchestrator_loop/scheduler.py            — pure should_continue_plan() predicate (Cat 1)
NEW   tests/unit/agent_harness/orchestrator_loop/test_scheduler.py — predicate coverage
EDIT  api/v1/chat/router.py                      — _stream_loop_events outer-loop + swallow/continue + 2nd todo-store load
EDIT  core/config/__init__.py                    — chat_scheduler_auto_continue=False + chat_scheduler_max_bursts=3
EDIT  tests/…/chat/test_chat_router*.py (or new) — outer-loop integration (fake loop yields max_turns→end_turn; fake todo store)
UNTOUCHED  orchestrator_loop/loop.py             — core loop unchanged (reuse run() rehydration as-is)
UNTOUCHED  api/v1/chat/sse.py · event_wire_schema · codegen · state_mgmt/todo_store.py · _contracts/todo.py · frontend/**
```

### 3.1 The continuation predicate (US-1, US-2, US-3) — `orchestrator_loop/scheduler.py` (NEW)

- Pure function, no I/O, unit-testable:
  `should_continue_plan(*, enabled: bool, stop_reason: str, todos: Sequence[Todo], bursts_used: int, max_bursts: int) -> bool`
  returns `enabled and stop_reason == TerminationReason.MAX_TURNS.value and bursts_used < max_bursts and any(t.status != "completed" for t in todos)`.
- Import `TerminationReason` from `orchestrator_loop/termination.py`, `Todo` from `_contracts/todo.py` (Cat-1 internal, no cross-category import violation).
- A companion `CONTINUATION_NUDGE: str` constant (e.g. `"Continue executing the plan. Work the next ready step(s)."`) lives here.

### 3.2 Router outer-loop (US-1, US-4) — `api/v1/chat/router.py` `_stream_loop_events`

**Day-0 D-router-loopcompleted-shape (CONFIRMED)**: the `loop_end` frame yields at `router.py:878` (BEFORE the closeout block `:888`); that block does billing enqueue ×3 (`953-1055`) + quota reconcile (`896`) + SLA (`927`) + audit "completed" (`1068`) + handoff (`1109`) + break (`1158`). The outer-loop MUST SPLIT the closeout, not swallow it wholesale.

- Wrap the single `async for event in loop.run(...)` (`router.py:825`) in a bounded `while True`.
- **Continuation peek** — for a `LoopCompleted` when `chat_scheduler_auto_continue` is on: load todos (2nd `make_chat_todo_store(db, session_id, tenant_id).load()`; router scope already has the args, `router.py:263-330`) and evaluate `should_continue_plan`. Decide `cont` BEFORE the `:878` persist+yield.
- **Swallow (continuing burst)**: when `cont`, skip the `:869-878` persist+yield (the intermediate `loop_end` never reaches the FE — D-terminal-reemit: no re-emit needed), run **billing enqueue** (this burst's tokens are real), set `continue_after`, `break`; do NOT run quota/SLA/audit/handoff.
- **Final burst**: normal `:878` yield + billing + the full quota/SLA/audit/handoff closeout + break (existing behavior byte-for-byte).
- **Billing split**: gate the ×3 billing-enqueue blocks (`953-1055`) to run EVERY burst while quota/SLA/audit/handoff run ONLY on the final burst (an inline `is_final = not cont` guard, or a local `_enqueue_burst_billing` helper). A continuing burst that skipped billing would 漏帳 (regress C-11/C-15); one that re-ran quota reconcile against the SAME reservation would over-release.
- **Preserve** `handoff` (`stop_reason=="handoff"`) / `awaiting_approval` exits exactly as today — a continuing burst is `max_turns` only, so these never intersect the new path.
- After the `async for`: if `continue_after`, `bursts += 1`, `user_input = CONTINUATION_NUDGE`, loop again.

### 3.3 Settings (US-3) — `core/config/__init__.py`

- `chat_scheduler_auto_continue: bool = False` (default OFF → byte-identical).
- `chat_scheduler_max_bursts: int = 3`.
- Read per-request via `get_settings()` alongside sibling `chat_*` settings (NOT the raw-env background-job pattern — settings are startup-fixed for a chat request).

### 3.x What is explicitly NOT done

- **Per-burst stats aggregation** on the final `LoopCompleted` (the terminal event reflects only the last burst's turns/tokens; intermediate bursts' counts are not summed) → `AD-Scheduler-Burst-Stats-Aggregate-Phase58`.
- **A visible burst-boundary wire event** (FE burst counter / "continuing…" indicator) — intermediate `loop_end` is swallowed for FE-transparency; a visible signal is a future slice → `AD-Scheduler-Burst-Boundary-Wire-Phase58`.
- **Per-tenant scheduler policy** (enable + max_bursts override in `harness_policy`) → `AD-Scheduler-PerTenant-Phase58` (C3 seam).
- **DAG topological execution enforcement** (block the agent from starting a blocked todo) → `AD-TaskPrimitive-DAG-Enforce-Phase58` (separate range item).
- **Background-job variant** — rejected in favor of inline (rationale recorded in design note 60).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 399 · run_all 11/11 · pytest 3139+new · Vitest 925 (unchanged — no FE) · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.2/US-4 drive-through (MANDATORY, user-facing).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/orchestrator_loop/scheduler.py` | NEW (predicate + CONTINUATION_NUDGE) |
| 2 | `backend/src/api/v1/chat/router.py` | EDIT (`_stream_loop_events` outer-loop) |
| 3 | `backend/src/core/config/__init__.py` | EDIT (2 settings) |
| 4 | `backend/tests/unit/agent_harness/orchestrator_loop/test_scheduler.py` | NEW (predicate unit tests) |
| 5 | `backend/tests/…/chat/test_chat_router_scheduler.py` (or extend existing router test) | NEW/EDIT (outer-loop integration) |
| — | `backend/src/agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** |
| — | `backend/src/api/v1/chat/sse.py` · `event_wire_schema.py` · codegen | **UNTOUCHED** (no new/changed event) |
| — | `backend/src/agent_harness/_contracts/todo.py` · `state_mgmt/todo_store.py` | **UNTOUCHED** |
| — | `frontend/**` | **UNTOUCHED** (continuation is FE-transparent) |

## 5. Acceptance Criteria

1. `should_continue_plan` pure-function correctness: all four AND-conditions (enabled · `stop_reason=="max_turns"` · `bursts_used<max_bursts` · any-unfinished) covered by unit tests incl. each false branch.
2. **env OFF → byte-identical**: with `chat_scheduler_auto_continue=False`, `_stream_loop_events` yields exactly the pre-57.157 single-burst stream (integration test asserts one `loop_end`, no extra `loop.run`).
3. env ON + `max_turns` + unfinished plan → auto-continues (integration test: fake loop yields `max_turns` then `end_turn`; asserts 2 `loop.run` invocations, one final `loop_end`).
4. env ON + plan complete (all todos completed) after a `max_turns` burst → does NOT continue (stops).
5. env ON + `end_turn` terminal → does NOT continue (normal single burst).
6. `max_bursts` bound enforced: after N continuations the outer-loop stops even if plan still unfinished (test with `max_bursts=2`).
7. Intermediate `max_turns` `loop_end` swallowed; the FE-facing stream carries exactly ONE terminal `loop_end` (integration asserts).
8. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — real chat-v2 + Azure gpt-5.2, env enabled: a >8-turn multi-step DAG task runs multiple bursts within ONE send (no manual "continue"), Todos panel reaches all-completed; env-off re-check = single burst stops at 8 with plan unfinished. Screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
9. `AD-TaskPrimitive-Scheduler-Phase58` CLOSED; CHANGE-124 + design note 60; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `should_continue_plan` predicate + router outer-loop auto-continue
- [ ] US-2 `max_bursts` bound + per-burst caps preserved
- [ ] US-3 `chat_scheduler_auto_continue` (default OFF) + `chat_scheduler_max_bursts` (default 3) settings
- [ ] US-4 drive-through PASS (real chat-v2 + Azure, >8-turn plan auto-completes in one send)
- [ ] US-5 design note 60 + CHANGE-124 + calibration + navigators + AD closed

## 7. Workload Calibration

- Scope class **NEW `scheduler-cross-burst-spike` 0.60** (Cat 1 new-mechanism spike: pure predicate + router SSE outer-loop + 2 settings + drive-through. Anchored to `loop-injection-primitive-spike` 0.55 (57.101) / `verification-in-loop-spike` 0.60 (57.98) / `task-primitive-spike` 0.60 (57.140) — same loop-core-adjacent new-mechanism + main-flow-wiring shape. Set 0.60 not the 0.55 pure-wiring because the swallow/re-emit control-flow + the >8-turn drive-through staging is real design content; set 0.60 not a tiny-code 0.85 because the real-code core (predicate + outer-loop + swallow logic + integration tests ≥~3.5 hr) holds the spike multiplier per the 57.137 lesson. If a 2nd `scheduler-*-spike` lands >1.20 (drive-through-dominated), re-point 0.70.)
- **Agent-delegated: no** (parent-direct — loop-core-adjacent control-flow + a drive-through sensitive to real multi-burst behavior; the parent executes directly). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6 hr (predicate + unit tests ~1.5 · router outer-loop + swallow/re-emit + integration test ~2.5 · settings + wiring ~0.5 · drive-through (build a >8-turn task + clean restart + 2 legs) ~1.5) → class-calibrated commit ~3.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Infinite continuation / token burn | `max_bursts` bound (default 3) in `bursts_used < max_bursts`; each burst keeps `token_budget=100k` + `max_turns=8` unchanged; predicate is the single gate. |
| **Per-burst closeout double-execution** (Day-0 D-router-loopcompleted-shape MAJOR) — naive outer-loop re-runs quota reconcile (over-release, same reservation) / SLA (p99 pollution) / audit "completed" (duplicate rows) every burst | Split the closeout: billing enqueue runs EVERY burst (correct — real token spend); quota/SLA/audit/handoff gated to the FINAL burst only. Integration test asserts a 2-burst run → exactly one audit "completed" + one quota reconcile + per-burst billing. |
| Plan all-blocked-but-unfinished (DAG cycle / stuck agent) → continues but agent can't progress | `any(!=completed)` still continues (lets the agent complete a dependency to unblock next ready), but `max_bursts` bounds a truly-stuck plan; documented in design note 60. |
| Swallowing intermediate `loop_end` breaks the FE stream contract | Integration test asserts exactly one terminal `loop_end`; drive-through confirms chat-v2 renders continuously with no duplicate/missing end frame (Day-0 D-terminal-reemit). |
| Stale `--reload` masks the env change (Risk Class E) | Clean restart before drive-through; kill orphan spawn-workers; confirm sole PID + startup log; set env BEFORE restart (settings startup-fixed). |
| Continuation nudge pollutes the ledger | The nudge is a deliberate continuation user turn (rehydration-coherent); Day-0 D-continuation-persist fixes the exact text so a resumed transcript reads sensibly; noted in design note 60. |
| `handoff` / `awaiting_approval` terminal accidentally caught by the new `max_turns` path | Outer-loop only continues on `stop_reason=="max_turns"`; handoff/approval branches preserved exactly (Day-0 D-router-loopcompleted-shape re-reads the real control flow). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Per-burst stats aggregation on the terminal event → `AD-Scheduler-Burst-Stats-Aggregate-Phase58`.
- Visible burst-boundary wire event / FE burst counter → `AD-Scheduler-Burst-Boundary-Wire-Phase58`.
- Per-tenant scheduler enable + max_bursts override → `AD-Scheduler-PerTenant-Phase58` (C3 seam).
- DAG topological execution enforcement → `AD-TaskPrimitive-DAG-Enforce-Phase58`.
- `token_budget`-terminated bursts do NOT auto-continue (only `max_turns` does) — conservative, avoids the main token-runaway path → `AD-Scheduler-TokenBudget-Continue-Phase58` (revisit only if a real plan legitimately needs it).
- Background-job continuation variant → rejected (inline chosen; rationale in design note 60).
