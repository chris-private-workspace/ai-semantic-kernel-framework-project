# Sprint 57.157 Progress — Scheduler: cross-burst auto-continue

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-157-plan.md`
**Base**: `main` HEAD `aa0dcf13`

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — YYYY-MM-DD

### Prong 1 — path verify ✅
- NEW free: `orchestrator_loop/scheduler.py` (Glob 0), `test_scheduler.py`, `test_chat_router_scheduler.py`.
- EDIT present: `api/v1/chat/router.py`, `core/config/__init__.py`.
- `CHANGE-124` free (highest = CHANGE-123), design note `60` free (highest = 59).

### Prong 2 — content verify (drift findings)

| D | Finding | Implication |
|---|---------|-------------|
| **D-router-loopcompleted-shape** ⚠️ **MAJOR** | The `LoopCompleted` handler is NOT "emit loop_end + break". Reality: (1) the `loop_end` frame is yielded at `router.py:878` — BEFORE the handler block at `router.py:888`; every event including `LoopCompleted` is yielded there. (2) `router.py:888-1158` is a HEAVY closeout block: quota reconcile (`896`), SLA record (`927`), billing enqueue ×3 (llm_call/verification/compaction, `953-1055`), audit "conversation_completed" (`1068`), handoff boot (`1109`), then `break` (`1158`). | A naive outer-loop would re-run the ENTIRE closeout every burst. Must split: **billing enqueue = every burst** (each burst really burns tokens; skipping = regress C-11/C-15 漏帳 fix); **quota reconcile / SLA / audit / handoff = final burst only** (quota reconcile re-uses the SAME reservation → repeated calls = over-release bug risk; audit "completed" per-burst = multiple misleading rows; SLA latency counts from send-start = p99 pollution). Swallow = at `878` skip persist+yield when continuing (NO re-emit needed — D-terminal-reemit resolved). **Shifts plan §3.2 design** (see below). |
| **D-todo-store-factory** ✅ | `make_chat_todo_store(db, session_id, tenant_id) -> TodoStore \| None` at `_category_factories.py:430` (all-three-or-None guard). Router `_stream_loop_events` scope already has `db`/`tenant_id`/`session_id` (used by billing/audit). | 2nd `make_chat_todo_store(...).load()` at the continuation-peek is clean; None-guard mirrors existing (no store → no continuation, single-burst). |
| **D-continuation-persist** ✅ | `loop.py:2005` appends `Message(role="user", content=user_input)`; `loop.py:2009` persists it to the ledger (turn_num=0). The generator-head 57.126 main_transcript persist (`router.py:809-817`) runs ONCE on the inbound prompt, NOT inside the `async for` → the continuation nudge lands in the rehydration ledger but NOT the replay transcript. | Continuation nudge = a real user turn in the rehydration ledger (needed so the next burst sees "continue"). Replay shows the clean original conversation (nudge invisible) — a beneficial asymmetry. Finalize the nudge text (D). |
| **D-settings-pattern** ✅ | `chat_verification_mode:129` / `chat_memory_auto_extract:179` / `chat_session_summary:191` are pydantic Settings fields in `core/config/__init__.py`, read per-request via `get_settings()`. `chat_scheduler*` grep 0 (no conflict). | Add `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3` as sibling fields; per-request `get_settings()` (settings startup-fixed for a chat request). |
| **D-terminal-reemit** ✅ RESOLVED | Since `loop_end` yields at `878` (before the closeout block), a continuing burst simply SKIPS the `878` persist+yield. No re-emit machinery needed — the final burst yields its `878` frame normally. | Simplifies the design: swallow = a guard around `869-878` (skip persist+yield for a continuing LoopCompleted), not a "swallow then re-emit". |

### Prong 3 — schema verify
- **N/A** — no new DB table / migration / ORM column. Reuses `session_todos` via existing `DBTodoStore.load()`.

### D-baselines
- Trusting 57.156 closeout: pytest 3139/6skip · wire 26 · Vitest 925 · mockup 51 · mypy `src` 399/0 · run_all 11/11. Re-verified at Day 2 full gate.

### Go/no-go
- **PROCEED with revised §3.2 design.** The MAJOR drift (D-router-loopcompleted-shape) raises complexity (outer-loop must split billing-every-burst vs closeout-only-final + swallow at 878) but stays confined to `router.py` (one file) + the new predicate — no new files beyond plan, no DB, no wire. Scope shift ~15-20% (complexity up, surface unchanged) → within the ≤20% "continue with risk noted in §Risks" band. Plan §0/§3.2/§8/§9 updated to reflect the split; original naive design preserved in this catalog for audit trail.

---

## Day 1 — Predicate + settings (US-1/2/3) — 2026-07-06

**Done**:
- `orchestrator_loop/scheduler.py` (NEW) — `should_continue_plan()` 4-condition AND predicate (`enabled` · `stop_reason=="max_turns"` · `bursts_used<max_bursts` · `any(!=completed)`) + `CONTINUATION_NUDGE` const. Pure, I/O-free.
- `tests/unit/agent_harness/orchestrator_loop/test_scheduler.py` (NEW) — 12 tests: happy path + every false branch (disabled / end_turn / token_budget / handoff / max_bursts reached+exceeded / all-completed / empty plan / in_progress-counts-unfinished).
- `core/config/__init__.py` (EDIT) — `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3` (sibling chat_* fields, per-request `get_settings()`).

**Partial gate**: pytest **12 passed** · black 3 files unchanged · isort clean · flake8 **CLEAN** (fixed 2 E501 in file-header Purpose lines) · mypy scheduler.py **Success**.

**Next (Day 2)**: router.py `_stream_loop_events` outer-loop — the MAJOR-drift-informed **billing-every-burst / closeout-only-final split** + swallow-at-878. The high-risk main-flow edit.

## Day 2 — Router outer-loop + integration (US-1/2/4) — 2026-07-06

**Done**:
- `api/v1/chat/router.py` (EDIT) — the MAJOR-drift-informed outer-loop. Design choice: a `_scheduled_loop_events` **chaining generator** yielding `(event, swallow)` (avoids indenting the ~400-line main-flow body): the existing `async for` iterates it + unpacks `_swallow`; the body barely changes — 3 `if not _swallow` guards (persist+yield / quota·SLA·audit / break→continue), **billing kept every-burst**, compaction accumulator **reset per-burst**. Imports: `scheduler` + `make_chat_todo_store`.
- `tests/unit/api/v1/chat/test_scheduler_router.py` (NEW) — 6 tests drive the REAL helper (fake loop max_turns→end_turn + fake todo store + patched settings): AC-2 OFF byte-identical / AC-3+7 continue + one-terminal / AC-4 complete-stops / AC-5 end_turn-stops / AC-6 max_bursts bound / empty-plan-stops. (`importlib.import_module` used — `from api.v1.chat import router` yields the __init__-re-exported APIRouter, not the module.)

**Gate**: mypy `src` **400 Success** (+scheduler.py) · run_all **11/11** · router.py black/isort/flake8 clean · scheduler test **6** · **850 regression passed** (all chat unit+integration+orchestrator_loop → default-OFF byte-identical confirmed; quota/SLA/audit/billing/handoff intact). Warnings = pre-existing asyncpg `Connection._cancel` cleanup noise.

**Next (Day 3)**: drive-through (MANDATORY) — real chat-v2 + Azure, env ON, a >8-turn multi-step DAG plan auto-completes in one send; env-OFF control stops at 8.

## Day 3 — Drive-through (US-4) — real chat-v2 + real Azure gpt-5.2 — 2026-07-06

**Setup**: backend started from project root (`--app-dir backend/src` → CWD=root so `env_file=".env"` reads the root `.env` with the scheduler flag; verified via `get_settings()` probe `chat_scheduler_auto_continue=True/False` per leg). Clean single no-`--reload` process (no spawn-worker orphan; Risk Class E). Frontend vite `:3007` (untouched). DB/Redis docker healthy. Real Azure gpt-5.2 + real DB (`ipa_v2`). jamie@acme-prod, real_llm mode. Prompt (both legs): a 12-step sequential DAG plan via `write_todos`, executed one step at a time (one `write_todos` mark per step) → forces >8 LOW-risk tool turns (no HITL pause) so a burst hits the `max_turns=8` ceiling with the plan unfinished.

### Leg 1 — env ON (`CHAT_SCHEDULER_AUTO_CONTINUE=true`, max_bursts=3) — **STRONG PASS**
- **Multi-burst in ONE send**: 1 `POST /api/v1/chat/` → **15 gpt-5.2 completions under ONE trace `43b6032f…`**; UI **LOOP (14 TURNS)** rendered as one continuous stream. A single `loop.run` caps at `max_turns=8` → 15 turns ⇒ the scheduler auto-continued (burst 1 ≈8 + burst 2 ≈7).
- **Airtight burst-boundary (messages ledger)**: `13:37:54` original prompt → burst 1 assistant/tool turns → **`13:38:33` `user` role "Continue executing the plan…" = the scheduler-injected `CONTINUATION_NUDGE`** → burst 2 turns → `13:39:06` final answer (end_turn). Exactly 1 nudge row in the DB (`content LIKE '%Continue executing the plan%'` → count 1).
- **Plan completed**: Todos panel **12/12 `completed`** (each with the 57.156 DAG "⤷ needs" dependency line) — NO manual "continue" clicked. Final answer + summary rendered. **Verification passed (llm_judge 0.98)**.
- **Per-burst billing intact (D-router-loopcompleted-shape split works)**: billing outbox drain `materialized=15 failed=0` (one row per real turn; no per-burst closeout double-run).
- Artifact: `artifacts/leg1-env-on-multiburst.png`.

### Leg 2 — env OFF (`CHAT_SCHEDULER_AUTO_CONTINUE=false`) — **PASS (control, gate proven)**
- Clean restart (killed PID 13432, `:8000` free, 0 orphan python). Settings probe confirmed `False`.
- **Single burst stops at the ceiling**: 1 POST → **8 gpt-5.2 completions, all ONE trace `bc98e6ff…`** (unfiltered total = 8). UI **LOOP (8 TURNS)**; Inspector **TURN 8 · MAX_TURNS · stop_reason=`max_turns`**.
- **Plan UNFINISHED**: last `write_todos` output "Recorded plan: 12 todos (**7 completed, 0 in_progress, 5 pending**)". **NO continuation** — DB nudge count still **1** (leg-1 only; OFF injected none → predicate correctly returns False when disabled).
- billing `materialized=8` (single-burst per-turn billing = byte-identical to pre-57.157).
- The turn-9 UI "awaiting approval" badge = chat-v2's pre-existing render for a `max_turns`-terminated (non-end_turn) loop (this sprint changed **no** frontend); it visually IS the "agent stalled at the ceiling, needs the human to continue" state the scheduler removes. The 3 `hitl` log hits are all startup construction lines (NoopNotifier fallback / DBHITLPolicyStore / HITLManager), NOT a runtime pause.
- Artifact: `artifacts/leg2-env-off-single-burst.png`.

### Observed vs intended
Intended: ON → a >8-turn plan auto-completes in one send via cross-burst continuation; OFF → the same task stalls at `max_turns` with the plan unfinished. **Observed exactly that**, with the burst boundary directly evidenced by the injected `CONTINUATION_NUDGE` ledger row (ON) vs its absence (OFF), and the per-burst-billing / final-only-closeout split confirmed by `materialized=15` (ON, 2 bursts, no double closeout) vs `materialized=8` (OFF).

## Day 4 — <pending>
