# Sprint 57.166 Plan — cross-burst turn/token aggregate in the final loop_end

**Summary**: Closes `AD-Scheduler-Burst-Stats-Aggregate-Phase58` (Task-primitive range, 57.157 carryover). When the cross-burst scheduler (57.157) runs the loop across N bursts, each burst yields its own `LoopCompleted` carrying only THAT burst's counters, so the final loop_end (the one the FE sees + the audit records) under-reports the run's true totals (e.g. a 8+7 two-burst run reports 7 turns, not 15). This sprint accumulates the per-burst turn/token counters in `_stream_loop_events` and feeds the aggregate to (a) the FE-visible loop_end `total_turns` payload and (b) the `conversation_completed` audit `operation_data`, while leaving per-burst billing untouched (billing reads `event.*` per burst — mutating the event would double-bill). The ChatHeader turn-count badge is user-facing → **drive-through MANDATORY** (scheduler ON, force a multi-burst run, verify the badge shows the aggregate). No design note (not a spike; a scheduler-range carryover fix).

**Status**: Approved-to-execute (user picked ① Burst-Stats-Aggregate via AskUserQuestion 2026-07-16, then "繼續執行 Task primitive pending task")
**Branch**: `feature/sprint-57-166-burst-stats-aggregate`
**Base**: `main` HEAD `3395b4a1` (FIX-034 New-session sidebar fix merged, PR #394)
**Slice**: closes `AD-Scheduler-Burst-Stats-Aggregate-Phase58` — Task-primitive range, standalone (1 of the 4 open 57.157 scheduler carryovers)
**Scope decisions**: (a) accumulate in `_stream_loop_events`, NO event mutation — billing keeps reading per-burst `event.*`; (b) patch only 2 sites — the final loop_end FE payload `total_turns` + the audit `operation_data` (4 counters); (c) scheduler OFF (single burst) → agg == the one burst → byte-identical; (d) `cached_input_tokens` / `cache_hit_rate` (a rate) left as last-burst — out of scope (ambiguous to aggregate a rate).

---

## 0. Background

### The gap (`AD-Scheduler-Burst-Stats-Aggregate-Phase58`)

- The 57.157 scheduler re-runs `loop.run()` for each burst; each burst emits its OWN `LoopCompleted` with only that burst's `total_turns` / `total_tokens` / `input_tokens` / `output_tokens`.
- Only the FINAL (non-swallowed) `LoopCompleted` is yielded to the FE + drives the `conversation_completed` audit row.
- So a multi-burst run under-reports: a 8+7 two-burst run shows **7 turns** in the ChatHeader badge (and 7 in the audit), not 15.

### Why it matters (the missing capability)

The scheduler's whole point (engine-debt kickoff) is long-running agents across bursts. Under-reporting the turn/token totals makes the one visible signal of "this was a long multi-burst run" lie — the header badge and the audit trail both hide the real scope of work. Billing is already correct per-burst (57.157), so the money is right; only the *displayed / recorded* stats are wrong.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `3395b4a1`) | Anchor |
|-------|-------------------------------------|--------|
| burst loop | each burst = a fresh `loop.run()`; its `LoopCompleted` counts only that burst | `router.py:786` |
| FE payload | loop_end SSE data carries `total_turns` straight from `event.total_turns` | `sse.py:247` |
| audit | `conversation_completed` `operation_data` reads `event.total_turns/total_tokens/input_tokens/output_tokens` | `router.py:1157-1161` |
| billing | per-burst enqueue reads `event.input_tokens/output_tokens` (runs for EVERY burst, not gated on `_swallow`) | `router.py:1024-1044` |

→ The fix must aggregate the counters across bursts and feed the aggregate to the FE payload + audit ONLY — never to the billing enqueue (per-burst), so it must NOT mutate the event.

### The design (backend-only: 4 accumulators + 1 payload patch + 4 audit fields + tests)

```
_stream_loop_events (router.py):
  before the async-for:  agg_turns = agg_total_tokens = agg_input_tokens = agg_output_tokens = 0
  on each LoopCompleted (before serialize): agg_* += event.*        # swallowed AND final
  after serialize, final loop_end only:      payload["data"]["total_turns"] = agg_turns
  audit operation_data:                       total_turns=agg_turns, total_tokens=agg_total_tokens,
                                              input_tokens=agg_input_tokens, output_tokens=agg_output_tokens
  billing enqueue:                            UNCHANGED — still reads event.input_tokens/output_tokens (per-burst)
```

Chose "accumulate + patch 2 read-sites" over "mutate the final event via dataclasses.replace" because billing and audit read the SAME `event` fields; mutating the event to the aggregate would make the final burst's billing enqueue bill the cross-burst sum → double-charge. Keeping the aggregate in separate locals feeds only the 2 display/record sites.

### Ground truth (recon head-start — code read on `main` HEAD `3395b4a1`; ALL re-verified §checklist 0.1)

- `router.py:784-810` — `_scheduled_loop_events` yields `(event, swallow)`; swallowed intermediate `LoopCompleted` is neither persisted nor yielded (`router.py:934`).
- `router.py:954-1132` — the `LoopCompleted` block: billing enqueue is NOT gated on `_swallow` (per-burst); quota/SLA/audit ARE `if not _swallow` (final-only).
- `sse.py:242-252` — loop_end payload carries `stop_reason`, `total_turns`, `cached_input_tokens`, `cache_hit_rate` (NOT total_tokens) → FE-visible aggregate target is `total_turns` only.
- FE `chatStore.ts` loop_end case reads `ev.data.total_turns` → `totalTurns`; `ChatHeader.tsx:83` shows `turnCount = totalTurns > 0 ? totalTurns : active?.turns` (both pre-existing, UNCHANGED).
- `test_audit_log_observer.py::_drive_stream` drives `_stream_loop_events` with a fake loop + capturable `append_audit`; `test_scheduler_router.py::_patch` shows the scheduler-ON `get_settings` + `make_chat_todo_store` monkeypatch — combine them for the multi-burst aggregate test.

**Baselines (57.165 closeout)**: pytest 3255 · run_all 12/12 · mypy `src` 400. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-audit-observer-pre-existing-fails** — summary notes 2 pre-existing `test_audit_log_observer` async-mock never-awaited failures; run the file on `main` first to confirm they pre-date this sprint (don't fix — out of scope) and that my new tests are additive.
- **D-billing-per-burst-ungated** — re-grep `router.py:1024` billing enqueue is NOT under `if not _swallow` (per-burst); confirms mutating the event would double-bill.
- **D-loopend-payload-fields** — re-grep `sse.py:247` loop_end carries `total_turns` (not total_tokens) → payload patch is 1 field.

## 1. Sprint Goal

Make the final loop_end honestly report the cross-burst aggregate turn/token totals (FE badge + audit row) without disturbing per-burst billing. Proven by: (1) unit tests — a scheduler-ON 2-burst drive of `_stream_loop_events` yields a final loop_end payload `total_turns` == sum and an `append_audit` `operation_data` == sum; a scheduler-OFF single burst stays byte-identical; (2) **MANDATORY drive-through** — scheduler ON, a plan forcing >8 turns, the ChatHeader badge shows the aggregate (e.g. 15) not the last burst (7). Produces CHANGE-135; no design note.

## 2. User Stories

- **US-1** (aggregate): 作為 operator，我希望多-burst run 的 turn/token 統計反映整個 run 的總和，以便 header 與 audit 不會少報真實工作量。
- **US-2** (no double-bill): 作為 platform owner，我希望這個修正**不影響** per-burst billing，以便計費維持正確(57.157 已驗)。
- **US-3** (drive-through, MANDATORY): 作為使用者，我希望在真實多-burst 對話中 ChatHeader 的「N turns」顯示總和，以便我看到的數字是誠實的。
- **US-4** (closeout): CHANGE-135 + AD closed + calibration + navigators.

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO wire codegen / NO frontend / NO new file)

```
EDIT  backend/src/api/v1/chat/router.py       — 4 accumulators + accumulate-on-LoopCompleted + payload patch + audit 4 fields
NEW   backend/tests/unit/api/v1/chat/test_scheduler_burst_stats.py  — multi-burst aggregate (payload + audit) + OFF byte-identical
UNTOUCHED  agent_harness/orchestrator_loop/scheduler.py  — pure predicate, no counter logic
UNTOUCHED  sse.py                              — payload built from event; the router patches the dict post-serialize
UNTOUCHED  frontend/**                          — chatStore + ChatHeader already render loop_end.total_turns
UNTOUCHED  billing / quota / SLA paths          — read event.* per burst
```

### 3.1 Aggregation (US-1/US-2) — `router.py` `_stream_loop_events`

- Before the `async for` (near the `compaction_in/out` locals ~L880): init `agg_turns = agg_total_tokens = agg_input_tokens = agg_output_tokens = 0`.
- After the subagent-frame drain, before `serialize_loop_event` (~L908): on `isinstance(event, LoopCompleted)`, `agg_turns += event.total_turns` (+ 3 token fields). Runs for swallowed AND final bursts.
- After the `active_skill` payload patch (~L927), before persist/yield (`if not _swallow`): add `if isinstance(event, LoopCompleted) and not _swallow: payload["data"]["total_turns"] = agg_turns`.
- Audit block (L1157-1161): replace `event.total_turns/total_tokens/input_tokens/output_tokens` → `agg_turns/agg_total_tokens/agg_input_tokens/agg_output_tokens`. `model`/`provider` stay `event.*` (last burst — same across bursts).
- Billing enqueue (L1024-1044): **UNCHANGED** — keeps `event.input_tokens/output_tokens` per burst.

### 3.2 Tests (US-1/US-2) — `test_scheduler_burst_stats.py`

- `_drive_stream` variant that patches `get_settings` (scheduler ON, max_bursts≥2) + `make_chat_todo_store` (pending todo) + a 2-burst `_FakeLoop` (burst1 `LoopCompleted(stop_reason="max_turns", total_turns=8, total_tokens=100, input_tokens=80, output_tokens=20)`, burst2 `LoopCompleted(stop_reason="end_turn", total_turns=7, total_tokens=70, input_tokens=55, output_tokens=15)`).
- **T1 audit aggregate**: capture `append_audit` → called ONCE, `operation_data.total_turns==15`, `total_tokens==170`, `input_tokens==135`, `output_tokens==35`.
- **T2 wire aggregate**: real `serialize_loop_event` + `format_sse_message`; parse the single loop_end frame → `total_turns==15`.
- **T3 OFF byte-identical**: scheduler OFF single burst → audit `total_turns==8` (== the one burst; no double count).
- **T4 no double-bill**: assert `billing_outbox.enqueue` was called per-burst with each burst's OWN input/output tokens (80/20 then 55/15), NOT the aggregate.

### 3.x What is explicitly NOT done

- `cached_input_tokens` / `cache_hit_rate` aggregate (a rate — ambiguous; last-burst kept) → `AD-Scheduler-Burst-CacheRate-Aggregate` (new carryover).
- A per-burst wire event / FE burst counter → that's the separate `AD-Scheduler-Burst-Boundary-Wire-Phase58` (② slice, deferred).
- Any `dataclasses.replace` on the event (rejected — would double-bill).

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 400 · run_all 12/12 · pytest 3255+new · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.1/3.2 unit proofs + the US-3 MANDATORY drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/chat/router.py` | EDIT (4 accumulators + accumulate + payload patch + audit 4 fields) |
| 2 | `backend/tests/unit/api/v1/chat/test_scheduler_burst_stats.py` | NEW (T1-T4) |
| — | `agent_harness/orchestrator_loop/scheduler.py` | **UNTOUCHED** (pure predicate) |
| — | `backend/src/api/v1/chat/sse.py` | **UNTOUCHED** (router patches the dict) |
| — | `frontend/**` | **UNTOUCHED** (renders loop_end.total_turns already) |

## 5. Acceptance Criteria

1. A scheduler-ON 2-burst drive of `_stream_loop_events`: final loop_end payload `total_turns` == sum of both bursts; `append_audit` `operation_data` 4 counters == sums.
2. Per-burst billing enqueue still receives each burst's OWN input/output tokens (no double-charge) — T4.
3. Scheduler OFF (single burst) → byte-identical audit + payload (agg == the one burst) — T3.
4. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — scheduler ON, a plan forcing >8 turns → ChatHeader badge shows the aggregate turn count (not the last burst); screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
5. `AD-Scheduler-Burst-Stats-Aggregate-Phase58` CLOSED; CHANGE-135; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 aggregate accumulators + payload/audit patch in `_stream_loop_events`
- [ ] US-2 billing untouched (T4 proves per-burst)
- [ ] US-3 drive-through PASS (real multi-burst run, badge = aggregate)
- [ ] US-4 CHANGE-135 + closeout

## 7. Workload Calibration

- Scope class **`scheduler-cross-burst-spike` 0.60** (2nd data point; **Read + cite `docs/03-implementation/agent-harness-execution/calibration-matrix.md`**; 57.157 was the 1st @ 0.60 — this is a SMALLER slice of the same range, so ratio likely IN band; if 2nd > 1.20 → re-point 0.70 per the class note).
- **Agent-delegated: no** (parent-direct — small surgical backend change requiring precise billing/audit-interplay understanding; not a mechanical delegation). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~4.25 hr (impl ~0.75 · tests ~1.0 · drive-through ~1.5 · closeout ~1.0) → class-calibrated commit ~2.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Mutating the event to aggregate → double-bill | Design keeps aggregate in separate locals; billing reads `event.*` untouched; T4 asserts per-burst billing tokens |
| Stale `--reload` backend masks the wiring for drive-through (Risk Class E) | Clean restart with `CHAT_SCHEDULER_AUTO_CONTINUE=true`; confirm sole live worker via `Win32_Process` PID/PPID/StartTime; capture startup log |
| Multi-burst drive-through env detective work (57.157 variance driver) | Reuse 57.157's known-good env (same machine/session); probe `get_settings().database_url` before psql |
| Pre-existing `test_audit_log_observer` async-mock fails (Risk Class C-adjacent) | Confirm they pre-date this sprint on `main` (Day-0); write the new test file independently so it isn't coupled to the flaky ones |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- `cached_input_tokens` / `cache_hit_rate` cross-burst aggregate — `AD-Scheduler-Burst-CacheRate-Aggregate` (new).
- Burst-boundary wire event + FE burst counter — `AD-Scheduler-Burst-Boundary-Wire-Phase58` (② slice).
- `token_budget` also continuing — `AD-Scheduler-TokenBudget-Continue-Phase58` (③ slice).
- Per-tenant scheduler policy — `AD-Scheduler-PerTenant-Phase58` (deliberate anti-AP-6).
