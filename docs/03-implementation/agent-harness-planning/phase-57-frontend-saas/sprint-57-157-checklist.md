# Sprint 57.157 — Checklist (Scheduler: cross-burst auto-continue)

[Plan](./sprint-57-157-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `aa0dcf13`)
- [x] **Prong 1 — path verify**: `scheduler.py` + `test_scheduler.py` free (Glob 0); `router.py` + `core/config/__init__.py` present; `CHANGE-124` + design note `60` free (highest 123 / 59)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-router-loopcompleted-shape** ⚠️ MAJOR — loop_end yields @878 (BEFORE closeout @888); closeout = billing×3 + quota + SLA + audit + handoff → must SPLIT (billing every burst / quota-SLA-audit-handoff final only); plan §0/§3.2/§8/§9 updated
  - [x] **D-todo-store-factory** — `make_chat_todo_store(db, session_id, tenant_id)` @`_category_factories.py:430`; router scope has the args
  - [x] **D-continuation-persist** — `loop.py:2005` append + `:2009` persist user turn; nudge enters rehydration ledger NOT replay transcript (beneficial asymmetry); nudge text finalized
  - [x] **D-settings-pattern** — `chat_*` are config pydantic fields (129/179/191) via `get_settings()`; `chat_scheduler` grep 0
  - [x] **D-terminal-reemit** — RESOLVED: loop_end @878 → continuing burst just skips :878 (no re-emit machinery)
- [x] **Prong 3 — schema verify**: **N/A** (reuses `session_todos` via existing `DBTodoStore`)
- [x] **D-baselines** — 57.156 closeout: pytest 3139/6skip · wire 26 · Vitest 925 · mockup 51 · mypy `src` 399/0 · run_all 11/11 (re-verify Day 2 gate)
- [x] **Catalog drift** — progress.md Day-0 table written (5 D-* + implication)
- [x] **Go/no-go** — ~15-20% ≤20% band → PROCEED with revised split design

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-157-scheduler-cross-burst` (from `main` `aa0dcf13`) ✅

---

## Day 1 — Predicate + settings (US-1, US-2, US-3)

### 1.1 Continuation predicate
- [x] **`orchestrator_loop/scheduler.py` (NEW)** — `should_continue_plan(*, enabled, stop_reason, todos, bursts_used, max_bursts) -> bool` (4-condition AND) + `CONTINUATION_NUDGE` const ✅
  - DoD: pure, no I/O; imports `TerminationReason` (termination.py) + `Todo` (_contracts/todo.py); file header per convention ✅

### 1.2 Predicate unit tests
- [x] **`tests/unit/agent_harness/orchestrator_loop/test_scheduler.py` (NEW)** — 12 tests: happy + every false branch (disabled / end_turn / token_budget / handoff / max_bursts reached+exceeded / all-completed / empty / in_progress) ✅
  - DoD: every AND-branch's false path covered ✅ · pytest **12 passed**

### 1.3 Settings
- [x] **`core/config/__init__.py` (EDIT)** — `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3` ✅
  - DoD: default OFF (sibling chat_* fields, per-request `get_settings()`) ✅

### 1.x Partial gate
- [x] black 3 files unchanged · isort clean · flake8 **CLEAN** (fixed 2 E501 header Purpose lines) · mypy scheduler.py **Success** ✅

---

## Day 2 — Router outer-loop + integration (US-1, US-2, US-4-scaffold)

### 2.1 Router outer-loop
- [x] **`api/v1/chat/router.py` (EDIT)** — chaining generator `_scheduled_loop_events` yielding `(event, swallow)`; existing `async for` iterates it + unpacks `_swallow`; 3 `if not _swallow` guards (persist+yield / quota·SLA·audit / break→continue), billing every-burst, compaction reset per-burst ✅
  - DoD: `handoff` (`stop_reason=="handoff"`) + `awaiting_approval` preserved (swallow only on `max_turns`); 2nd `make_chat_todo_store(...).load()` supplies todos; predicate the only gate ✅ · mypy router.py clean

### 2.2 Router integration tests
- [x] **`tests/unit/api/v1/chat/test_scheduler_router.py` (NEW)** — 6 tests drive the REAL helper (fake loop max_turns→end_turn + fake todo store + patched settings) ✅
  - [x] env OFF → 1 burst, byte-identical (AC-2) · env ON + max_turns + unfinished → 2 bursts, 1 terminal (AC-3, AC-7) · plan-complete stops (AC-4) · end_turn stops (AC-5) · `max_bursts=2` bound (AC-6) · empty-plan stops

### 2.x Full gate
- [x] mypy `src` **400** Success (+scheduler.py) · run_all **11/11** · **850 regression passed** (chat unit+integration+orchestrator_loop) · router black/isort/flake8 clean · LLM-SDK-leak clean ✅ (Vitest 925 / mockup 51 / build unchanged — no FE; full pytest count re-verified Day 4)

---

## Day 3 — Drive-through (US-4) — real chat-v2 + real backend + real Azure LLM

### 3.1 Clean restart (Risk Class E)
- [x] Set `CHAT_SCHEDULER_AUTO_CONTINUE=true` (+ `CHAT_SCHEDULER_MAX_BURSTS=3`) in root `.env` BEFORE restart; started single no-`--reload` process from root (`--app-dir backend/src` so CWD=root reads root `.env`); 0 orphan python (single-proc, no spawn worker); `get_settings()` probe confirmed `True`/`False` per leg + startup-complete log ✅

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] **Leg 1 (env ON)**: real chat-v2 + Azure gpt-5.2 — 12-step DAG `write_todos` plan → **15 gpt-5.2 turns / 2 bursts under ONE trace in ONE POST** (LOOP 14 TURNS); Todos panel **12/12 completed**, no manual "continue" ✅
- [x] **Leg 2 (env OFF re-check)**: clean restart env off; same prompt → **single burst, 8 completions, stop_reason=max_turns, plan 7/12 (unfinished)**; DB nudge count still 1 (leg-1 only) ✅
- [x] **THE fix (real UI)**: continuous stream = one terminal frame (Verification passed 0.98); Todos live-updated across bursts; **airtight** burst boundary = injected `CONTINUATION_NUDGE` user turn in the messages ledger (`13:38:33`, between bursts); billing `materialized=15` (ON) vs `8` (OFF) proves per-burst-billing / final-only-closeout split ✅
- [x] Screenshots both legs (`artifacts/leg1-env-on-multiburst.png` + `leg2-env-off-single-burst.png`) + observed-vs-intended → progress.md Day 3 ✅

---

## Day 4 — CHANGE-124 + closeout

### 4.1 CHANGE-124 + design note 60
- [x] **`CHANGE-124-scheduler-cross-burst-auto-continue.md`** (gap + fix + drive-through PASS + AD closed) ✅
- [x] **`60-scheduler-cross-burst-design.md`** (spike — 8-point gate; inline-vs-background matrix + continuation-nudge semantics + billing/closeout split + max-bursts safety) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`scheduler-cross-burst-spike` 0.60, 1st pt ~1.15-1.3 near/slightly-over; KEEP single-data-point, re-point 0.70 if 2nd >1.20) ✅
- [x] Final gate sweep: mypy `src` 400/0 · run_all 11/11 · scheduler pytest 18 · 850 chat regression OFF byte-identical · black/isort/flake8 clean · LLM-SDK-leak clean (Vitest/mockup/build N/A — no FE) ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated + capability list · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED `AD-TaskPrimitive-Scheduler-Phase58` + registered 5 new ADs) · sprint-workflow matrix (`scheduler-cross-burst-spike` 0.60 row) ✅
- [x] Anti-pattern self-check (retro Q5): AP-1/2/3/4/6/8/11 → 0 violations; v2 lints 11/11 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
