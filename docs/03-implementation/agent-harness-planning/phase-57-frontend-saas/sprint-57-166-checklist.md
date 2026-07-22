# Sprint 57.166 — Checklist (cross-burst turn/token aggregate in the final loop_end)

[Plan](./sprint-57-166-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `3395b4a1`)
- [x] **Prong 1 — path verify**: `router.py` + `sse.py` + `test_scheduler_router.py` + `test_audit_log_observer.py` exist; NEW `test_scheduler_burst_stats.py` free; `CHANGE-135` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-billing-per-burst-ungated** — grep `router.py:1024` billing enqueue is NOT under `if not _swallow` (confirms mutate-event would double-bill)
  - [x] **D-loopend-payload-fields** — grep `sse.py:247` loop_end carries `total_turns` (not total_tokens) → 1 payload field to patch
  - [x] **D-audit-fields** — grep `router.py:1157-1161` audit reads `event.total_turns/total_tokens/input_tokens/output_tokens`
  - [x] **D-audit-observer-pre-existing-fails** — run `test_audit_log_observer.py` on `main`; confirmed the 2 async-mock fails pre-date this sprint (don't fix)
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM change)
- [x] **D-baselines** — run_all 12/12 · mypy `src` 400 · scheduler tests 18 pass
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — ~0% scope shift → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-166-burst-stats-aggregate` (from `main` `3395b4a1`)

---

## Day 1 — Aggregation + tests (US-1/US-2)

### 1.1 Accumulators + accumulate
- [x] **4 accumulators before the `async for` + accumulate on each LoopCompleted**
  - DoD: `agg_turns/agg_total_tokens/agg_input_tokens/agg_output_tokens` init 0; `+= event.*` on every LoopCompleted (swallowed + final), before serialize
  - Verify: `grep -n "agg_turns" backend/src/api/v1/chat/router.py`

### 1.2 Patch the 2 read-sites (payload + audit)
- [x] **FE payload `total_turns` = agg on final loop_end; audit `operation_data` 4 fields = agg**
  - DoD: `payload["data"]["total_turns"] = agg_turns` only when `isinstance(event, LoopCompleted) and not _swallow`; audit block uses `agg_*`; billing enqueue UNCHANGED (still `event.*`)
  - Verify: `grep -n "agg_turns\|agg_total_tokens" backend/src/api/v1/chat/router.py`

### 1.3 Tests (T1-T4)
- [x] **`test_scheduler_burst_stats.py` — T1 audit aggregate / T2 wire aggregate / T3 OFF byte-identical / T4 no double-bill**
  - DoD: 2-burst (8+7 turns, 100+70 tokens) → audit + payload == 15 turns / 170 tokens; OFF → 8; billing per-burst 80/20 then 55/15
  - Verify: `python -m pytest backend/tests/unit/api/v1/chat/test_scheduler_burst_stats.py -q` → 4 pass

### 1.x Partial gate
- [x] `mypy src` (400) + `black/isort/flake8` on the 2 touched files (1 MHist E501 trimmed)

---

## Day 2 — Full gate (US-1/US-2)

### 2.1 Full gate
- [x] mypy `src` 400 · run_all 12/12 · scheduler suite 18 + test_router + T1-T4 = 47 pass (2 pre-existing audit-observer fails unchanged) · chat integration 27 pass (e2e/cost/quota/transcript byte-identical) · black/isort/flake8 clean · LLM-SDK-leak clean (run_all)

---

## Day 3 — Drive-through (US-3) — real UI + real backend + real LLM
_(MANDATORY — the ChatHeader turn-count badge is user-facing.)_

### 3.1 Clean restart (Risk Class E)
- [x] Kill all stale uvicorn reloader + spawn-workers on :8000 (verify sole live worker via `Win32_Process` PID/PPID/StartTime); restart backend with `CHAT_SCHEDULER_AUTO_CONTINUE=true` (+ low `CHAT_SCHEDULER_MAX_BURSTS`); confirm startup + `get_settings().chat_scheduler_auto_continue` true
  - Sole live `python.exe` verified before each leg; no-`--reload` single process; scheduler confirmed by the 2nd/3rd `loop_start` + new `agent_loop.run` span in the live stream

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] In chat-v2, send a multi-step `write_todos` plan that forces > 8 turns → the scheduler auto-continues into a 2nd burst
  - **Test lever** (user-approved, NOT committed): `handler.py` `max_turns` 8 → 2 to hit the ceiling deterministically; **reverted** (`git diff` empty). Leg 3 = 3 bursts.
- [x] **THE fix (real UI)**: after the run completes, the ChatHeader **"N turns"** badge shows the AGGREGATE (e.g. 15), not the last burst (7); cross-check the `conversation_completed` audit_log row's `total_turns`
  - Badge **"· 7 turns"** == audit `total_turns` **7**; per-burst ceiling 2 → 7 is impossible for a single burst; exactly ONE terminal `loop_end` (2 swallowed)
- [x] Screenshot + observed-vs-intended → progress.md Day 3
  - `artifacts/sprint-57-166-drivethrough-aggregate-7-turns.png` + Day 3 leg table (incl. 2 inconclusive legs: HITL gate / model self-loop refusal)

---

## Day 4 — CHANGE-135 + closeout

### 4.1 CHANGE-135
- [x] **`CHANGE-135-scheduler-burst-stats-aggregate.md`** (gap + fix + drive-through PASS + AD closed)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`scheduler-cross-burst-spike` 0.60, 2nd data point; flag if ratio out of band → re-point 0.70)
  - Ratio **~1.9-2.1** (committed ~2.6 hr, actual ~5.0-5.5 hr) → OUT of band → **RE-POINTED 0.70**. Code+tests landed on estimate; the whole overrun is Day-3 drive-through (6 legs).
- [x] calibration-matrix.md row — fill skeleton, ≤ 1 line ~250 chars (narration → calibration-log §1): `| \`scheduler-cross-burst-spike\` | 0.60 | <mean> | KEEP (57.166 2nd pt ratio ~<Y> IN band; smaller slice than 57.157; if 3rd >1.20 → 0.70; → calibration-log §1) |`
  - Landed as **RE-POINT 0.70** (not KEEP — the skeleton assumed in-band); full narration → calibration-log §1; `check_rules_hygiene` green (row within cap)
- [x] Final gate sweep: mypy · run_all · pytest · black/isort/flake8 · LLM-SDK-leak
  - mypy `src` **400/0** · run_all **12/12** · scheduler+router+new **47 pass** (4+6+12+25 — corrected from the 48 first recorded) · chat integration **27 pass** · black/isort/flake8 clean
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Scheduler-Burst-Stats-Aggregate-Phase58` + add `AD-Scheduler-Burst-CacheRate-Aggregate`) · calibration-matrix.md row
  - Also: shipped-archive full block + pointer-index row; MEMORY.md compacted 19.7 → 17.4 KB (hook limit) by folding 57.162-166 into the 1-line style
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; v2 lints 12/12
  - 0 violations (AP-1/AP-8 N/A — no loop control-flow or LLM call added)
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION → post-merge status flip after gh-verified MERGED
