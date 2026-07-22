# Sprint 57.166 Progress — cross-burst turn/token aggregate

## Day 0 — 2026-07-16 — Plan-vs-Repo Verify

### Baselines (re-verified on `main` HEAD `3395b4a1`)
- run_all: **12/12 green**
- mypy `src`: **400 files, no issues**
- scheduler tests: `test_scheduler_router.py` 6 pass · `test_scheduler.py` 12 pass

### Drift findings

| ID | Finding | Implication |
|----|---------|-------------|
| **D-billing-per-burst-ungated** | `router.py:1024` billing `enqueue` is a standalone `if (billing_outbox... and event.input_tokens > 0...)` — NOT under `if not _swallow` (runs per burst) | ✅ Confirms mutating the event to the aggregate would double-bill → design keeps aggregate in separate locals (plan §0 design) |
| **D-loopend-payload-fields** | `sse.py:247` loop_end payload carries `total_turns` (+ `cached_input_tokens`, `cache_hit_rate`), NOT `total_tokens` | ✅ FE-visible aggregate = 1 field (`total_turns`); tokens aggregate lives only in audit |
| **D-audit-fields** | `router.py:1158-1161` audit `operation_data` reads `event.total_turns/total_tokens/input_tokens/output_tokens` | ✅ 4 fields to swap to `agg_*` |
| **D-audit-observer-pre-existing-fails** | `test_audit_log_observer.py` — 2 tests FAIL on `main` (`..._appends_on_loop_completed`, `..._failure_does_not_break_stream`): `router.py:678` `_max_main_seq` does `int((await db.execute(stmt)).scalar_one())` and `_make_mock_db()`'s AsyncMock returns a coroutine → `TypeError` (MAIN_TRANSCRIPT_OBSERVER defaults "true") | Pre-existing (confirmed earlier via git stash); **out of scope**. NEW test file sets `MAIN_TRANSCRIPT_OBSERVER=false` to avoid the same pitfall |

### Go/no-go
Scope shift ~0% (all plan assumptions confirmed) → **proceed to Day 1**.

## Day 1-2 — 2026-07-16 — Aggregation + tests + gate

### Implemented (`router.py` `_stream_loop_events`, 4 edits)
1. 4 accumulators (`agg_turns/agg_total_tokens/agg_input_tokens/agg_output_tokens`) before the `async for`.
2. Accumulate `+= event.*` on each `LoopCompleted` (swallowed + final), before serialize.
3. Patch final loop_end FE payload `total_turns = agg_turns` (only `not _swallow`).
4. Audit `operation_data` 4 counters → `agg_*` (billing enqueue UNCHANGED — still per-burst `event.*`).

### Tests — `test_scheduler_burst_stats.py` (NEW, 4 pass)
- T1 audit aggregate: 2-burst (8+7 / 100+70 / 80+55 / 20+15) → audit `operation_data` == 15 / 170 / 135 / 35.
- T2 wire aggregate: REAL serialize + captured `format_sse_message` → single loop_end frame `total_turns == 15`.
- T3 OFF byte-identical: scheduler OFF single burst → audit `total_turns == 8` (agg == the one burst).
- T4 no double-bill: `billing_outbox.enqueue` per-burst tokens 80/20 then 55/15 (NOT the aggregate).

### Gate
- black/isort/flake8 clean (1 MHist E501 trimmed) · mypy `src` 400 · run_all 12/12.
- Regression: scheduler suite (18) + test_router + my 4 = 47 pass; the 2 `test_audit_log_observer` fails are the Day-0 pre-existing ones (unchanged — fail at `_max_main_seq` before my code; single-burst agg == event so compatible).
- Chat integration (e2e / cost_ledger / quota_reconcile / main_transcript_persist): 27 pass → scheduler-OFF main path byte-identical.

## Day 3 — 2026-07-22 — Drive-through (real UI + real backend + real LLM) — **PASS**

### Setup (Risk Class E clean restart)
- Killed every stale uvicorn / spawn-worker; `Win32_Process` confirmed a **sole** live `python.exe` before each leg.
- Backend started WITHOUT `--reload` (deterministic startup log), `CHAT_SCHEDULER_AUTO_CONTINUE=true` + `CHAT_SCHEDULER_MAX_BURSTS=3`; frontend Vite :3007; real Azure `gpt-5.2`.
- **Test lever** (user-approved, NOT committed): `handler.py` `max_turns=8 → 2` so a burst hits the ceiling with pending todos deterministically. **Reverted after leg 3** — `git diff backend/src/api/v1/chat/handler.py` empty.

### Legs

| Leg | Setup | Observed | Verdict |
|-----|-------|----------|---------|
| **1** | scheduler ON, HITL default ON; `write_todos` + `python_sandbox` plan | Burst 1 hit `max_turns` with 4 pending todos → **2nd `loop_start` + new `agent_loop.run` span** (scheduler fired). Burst 2 stopped at the `python_sandbox` HITL gate → `stop=awaiting_approval`, 0 completed turns → agg 2+0 = **2** | Cross-burst continuation proven, but the sum is indistinguishable from last-burst-only → **inconclusive** |
| **2** | `write_todos`-only prompt (avoid the HITL gate) | Model refused to self-loop: *"I can't keep calling write_todos turn after turn on my own"* → `stop=end_turn`, single burst | Scheduler correctly did NOT continue (predicate needs the ceiling hit) → **no signal** |
| **3** | `HITL_ENABLED=false` (env only) so burst 2+ actually run turns | **3 bursts** (3 × `loop_start`), exactly **ONE terminal `loop_end`** reaching the FE with `stop=end_turn turns=7`; the 2 intermediate loop_ends correctly swallowed | ✅ **PASS** |

### Leg 3 — observed vs intended

| | Intended | Observed |
|---|---|---|
| ChatHeader badge | cross-burst SUM | **"· 7 turns"** |
| `conversation_completed` audit `total_turns` | same SUM | **7** (`total_tokens` 36898) |
| Per-burst ceiling | `max_turns=2` → no single burst can report > 2 | 7 is arithmetically impossible for one burst → the badge is the AGGREGATE, not the last burst |
| Terminal frames | exactly 1 `loop_end` | 1 (2 swallowed) |

Pre-fix behaviour would have shown **≤ 2** in both places. Screenshot: `artifacts/sprint-57-166-drivethrough-aggregate-7-turns.png`.

### Post-run restore
- `handler.py` reverted to `max_turns=8` (git diff empty); backend restarted with **no** test flags (scheduler default OFF, HITL default ON).
