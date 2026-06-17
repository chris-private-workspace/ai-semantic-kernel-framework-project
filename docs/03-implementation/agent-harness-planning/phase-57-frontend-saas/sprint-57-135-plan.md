# Sprint 57.135 Plan — scheduled transcript-retention background job

**Summary**: Ships a scheduled background job that AUTO-enforces per-tenant transcript retention — periodically sweeps every tenant and deletes `messages` + `message_events` older than that tenant's canonical `tenants.retention_days`, reusing the Sprint 57.134 `apply_transcript_retention`. Closes 57.134 follow-on #1 (the scheduled-job leg). Key scope decision: the job **defaults OFF** (destructive opt-in via env, unlike the billing drainer's default-ON) and mirrors the billing-outbox drainer lifecycle (poll loop + `app.state` task/stop_event + lifespan shutdown-cancel). Drive-through is a REAL runtime verification (background job has NO UI — start the real job with a short interval + seeded old transcripts on a throwaway tenant, observe auto-deletion in logs + DB); honest that there is no UI surface. NO design note (continuation of the 57.134 retention domain + an established drainer pattern, not a new-domain spike).

**Status**: Approved-to-execute (user AskUserQuestion 2026-06-17 picked "Scheduled transcript-retention job" as the next direction, after the `AD-Subagent-Child-Event-SSE-Relay` was closed as stale/YAGNI via diagnostic)
**Branch**: `feature/sprint-57-135-scheduled-transcript-retention` (already created; commit 1 = the subagent-AD-closure docs `c629b8d3`)
**Base**: `main` HEAD `c98b6368` (post-#316 Leg-2-closure merge)
**Slice**: closes 57.134 follow-on #1 (scheduled retention enforcement); standalone (FE retention tab + partition lifecycle are separate follow-ons)
**Scope decisions**: (a) job **DEFAULTS OFF** — destructive opt-in via `TRANSCRIPT_RETENTION_JOB_ENABLED` (vs billing drainer default-ON; deletion is irreversible); (b) reuse 57.134 `apply_transcript_retention` (real delete, NOT dry_run) per tenant; (c) per-tenant **fail-open + commit-per-tenant + audit** (`tenant_transcript_retention_scheduled`, system `user_id=None`); (d) **plain-env** config (enable + interval default 86400s) — NO `core.config` Settings schema change (dodges the lru_cache trap, mirrors billing's enable flag); (e) mirror the billing-outbox drainer lifecycle exactly.

---

## 0. Background

### The gap (57.134 follow-on #1 — scheduled retention)

Sprint 57.134 shipped **manual** transcript retention: an admin POST `/{id}/transcript-retention/apply` deletes one tenant's expired transcripts, and a preview GET counts them. There is **no automatic enforcement** — retention windows are only applied when an operator manually triggers each tenant, one at a time.

### Why it matters (the missing capability)

Compliance-grade retention requires transcripts past the tenant's window to be purged **automatically + periodically**, across all tenants, without manual intervention. Without a scheduler, `tenants.retention_days` is an advisory number that nothing enforces on its own.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `c98b6368`) | Anchor |
|-------|-------------------------------------|--------|
| Apply primitive | `apply_transcript_retention(db, tid, retention_days, *, now, dry_run)` exists; pure delete/count, does NOT commit or audit (caller does) | `platform_layer/transcripts/retention.py:66-111` |
| Only caller | the admin apply POST (commits + audits after) — no scheduler anywhere | `api/v1/admin/tenants.py:~1922` |
| Background-job template | billing-outbox drainer: poll loop + `_start_*` (env flag + `create_task` + `app.state`) + lifespan startup call + shutdown cancel | `api/main.py:267-336` (loop+start) · `:353` (startup) · `:358-368` (shutdown) |
| Tenant enumeration | `Tenant.id` (PK) + `Tenant.retention_days` (NOT NULL ≥1) + `Tenant.state` (enum) | `infrastructure/db/models/identity.py:112,156,119` |
| Audit | `append_audit(session, *, tenant_id, operation, resource_type, operation_data, user_id=None, …)` — `user_id` OPTIONAL → system job audits with `user_id=None` | `infrastructure/db/audit_helper.py:90-102` |

→ The fix composes two EXISTING things: a per-tenant **sweep** over `run`→`apply`→`audit`→`commit`, driven by a background **poll loop** that mirrors the billing drainer's lifecycle. No new primitive, no schema.

### The design (backend-only: 1 sweep fn in retention.py + 1 poll-loop/start/lifespan-wire in main.py + tests)

```
platform_layer/transcripts/retention.py  (EDIT)
  + @dataclass SweepStats(tenants_processed, tenants_failed, total_messages, total_events, cutoff_now)
  + async run_transcript_retention_sweep(session_factory, *, now=None) -> SweepStats
      for (tid, retention_days) in SELECT id, retention_days FROM tenants:
          try: async with session_factory() as db:
                   stats = await apply_transcript_retention(db, tid, retention_days, now=now)
                   await append_audit(db, tenant_id=tid, operation="tenant_transcript_retention_scheduled",
                                      resource_type="tenant", resource_id=str(tid),
                                      operation_data={retention_days, cutoff, deleted_messages, deleted_events},
                                      user_id=None)
                   await db.commit()
          except Exception: log.exception(...) ; tenants_failed += 1 ; continue   # fail-open per tenant

api/main.py  (EDIT — mirror billing drainer)
  + async _transcript_retention_poll_loop(session_factory, interval_s, stop_event)  # run sweep, log, wait_for(stop, interval)
  + async _start_transcript_retention_job(app)   # env TRANSCRIPT_RETENTION_JOB_ENABLED default "false"; interval env default 86400; create_task; app.state.transcript_retention_{task,stop}
  + _lifespan startup:  await _start_transcript_retention_job(app)          # after _start_billing_outbox_drainer
  + _lifespan shutdown:  stop_event.set() + wait_for(task,10) + cancel       # before OTel/engine teardown (mirror billing)
```

WHY default OFF (vs billing's default-ON): the billing drainer MATERIALIZES cost rows (non-destructive); this DELETES transcripts (irreversible). A destructive periodic job must be explicit opt-in so it never deletes data on an unconfigured environment.

### Ground truth (recon head-start — code read on `main` HEAD `c98b6368`; ALL re-verified §checklist 0.1)

- `retention.py:66-111` — `apply_transcript_retention` signature + no-commit/no-audit (caller owns the txn).
- `main.py:267-293` — `_billing_outbox_poll_loop` (while-not-stop + fail-open + `wait_for(stop_event.wait(), timeout=interval_s)`); `:296-336` `_start_billing_outbox_drainer` (env flag default true + `create_task` + `app.state`); `:353` startup call; `:358-368` shutdown cancel.
- `audit_helper.py:90-102` — `append_audit` `user_id` optional.
- `identity.py:112,156` — `Tenant.id` + `Tenant.retention_days`.

**Baselines (57.134 closeout)**: pytest **2741 + 5 skip** · mypy `src` **0/374** · run_all **10/10**. (Vitest / mockup / wire = N/A — pure backend.) Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-tenant-enum** — confirm `select(Tenant.id, Tenant.retention_days)` (no soft-delete column forces a filter) → decide ALL-tenants enumeration.
- **D-lifespan-test** — read `tests/unit/api/test_main_lifespan.py` to confirm it tests the billing drainer startup/env-flag (mirror for the retention job test).
- **D-billing-loop-first-run** — confirm the billing loop runs `drain_once()` BEFORE the first `wait_for` (so the retention sweep also runs once at startup, not after one full interval).
- **D-settings-vs-env** — confirm reading interval as plain env (not a new `core.config` field) avoids the lru_cache trap.

## 1. Sprint Goal

Ship a scheduled background job that auto-enforces per-tenant transcript retention. PROVEN by: gates (mypy `src` 0 · run_all 10/10 · pytest green + new sweep/loop tests · black/isort/flake8 · LLM-SDK-leak) AND a real runtime drive-through — start the real backend with the job ENABLED + a short interval + a seeded old transcript on a throwaway tenant, and observe the job auto-delete it (startup log + DB row count before/after). Background job has NO UI surface → runtime-verified (real backend + real DB), explicitly stated (not a gate-only claim; not a UI drive-through). Produces CHANGE-102; NO design note (continuation, not a spike).

## 2. User Stories

- **US-1** (sweep): 作為平台運營者，我希望一個 sweep 函式遍歷所有 tenant 並依各自 `retention_days` 刪除過期 transcript，以便無需手動逐 tenant apply。
- **US-2** (background job): 作為平台運營者，我希望此 sweep 以背景排程定期執行（env 開關 + 可設間隔，mirror billing drainer），以便 retention 持續自動 enforce。
- **US-3** (safety + audit): 作為合規負責人，我希望排程刪除**預設關閉**（destructive opt-in）、每 tenant **fail-open**、每次刪除寫 **audit**（system user），以便安全可控且可審計。
- **US-4** (drive-through, MANDATORY runtime): 作為開發者，我希望以真實後端 + 短間隔 + seeded 過期資料實際觀察 job 自動刪除（log + DB），以便證明它真的運作（非僅 gate / 非 curl）。
- **US-5** (closeout): CHANGE-102 + retrospective + navigators + next-phase-candidates。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / model / config-schema / frontend / wire change)

```
EDIT      platform_layer/transcripts/retention.py   — + SweepStats + run_transcript_retention_sweep
EDIT      api/main.py                                — + poll loop + _start_* + lifespan startup call + shutdown cancel
NEW       tests/unit/platform_layer/transcripts/test_retention_sweep.py  — sweep enumerate/delete/audit/fail-open
EDIT      tests/unit/api/test_main_lifespan.py       — job env-flag default-OFF + start-when-enabled (mirror billing)
UNTOUCHED migrations · models · core/config.py · frontend · event wire schema · the 57.134 apply fn body
```

### 3.1 Sweep (US-1) — `platform_layer/transcripts/retention.py`

- `@dataclass(frozen=True) SweepStats(tenants_processed: int, tenants_failed: int, total_messages: int, total_events: int)`.
- `async def run_transcript_retention_sweep(session_factory: async_sessionmaker, *, now: datetime | None = None) -> SweepStats`.
- Enumerate tenants in a short read session: `select(Tenant.id, Tenant.retention_days)` (ALL tenants — retention is data-lifecycle, independent of `Tenant.state`; provisioning tenants no-op, suspended still enforce).
- Per tenant, a FRESH `session_factory()` txn: `apply_transcript_retention(db, tid, rd, now=now)` → `append_audit(db, tenant_id=tid, operation="tenant_transcript_retention_scheduled", resource_type="tenant", resource_id=str(tid), operation_data={"retention_days": rd, "cutoff": stats.cutoff.isoformat(), "deleted_messages": stats.messages, "deleted_events": stats.events}, user_id=None)` → `await db.commit()`.
- Fail-open per tenant: a per-tenant exception → `logger.exception` + `tenants_failed += 1` + continue (a flake on one tenant must not abort the rest). Mirrors the drainer's fail-open philosophy.
- Aggregate + return `SweepStats`.

### 3.2 Background job (US-2 / US-3) — `api/main.py` (mirror `_billing_outbox_*`)

- `_transcript_retention_poll_loop(session_factory, interval_s, stop_event)`: `while not stop_event.is_set()`: `try: stats = await run_transcript_retention_sweep(session_factory)` (fail-open log on exception); `if stats.total_messages or stats.total_events or stats.tenants_failed: logger.info(...)`; then `await asyncio.wait_for(stop_event.wait(), timeout=interval_s)` (prompt shutdown). Runs the sweep ONCE at start, then every interval (same shape as billing).
- `_start_transcript_retention_job(app)`: `if os.environ.get("TRANSCRIPT_RETENTION_JOB_ENABLED", "false").lower() != "true": return` (DEFAULT OFF); `interval_s = int(os.environ.get("TRANSCRIPT_RETENTION_JOB_INTERVAL_S", "86400"))`; `stop_event = asyncio.Event()`; `task = asyncio.create_task(_transcript_retention_poll_loop(get_session_factory(), interval_s, stop_event))`; store `app.state.transcript_retention_stop` + `app.state.transcript_retention_task`; fail-open try/except around startup.
- `_lifespan` startup: `await _start_transcript_retention_job(app)` immediately after `await _start_billing_outbox_drainer(app)` (line 353).
- `_lifespan` shutdown: mirror billing (lines 358-368) — set stop_event, `await asyncio.wait_for(task, timeout=10)` else cancel, BEFORE OTel/engine teardown.

### 3.x What is explicitly NOT done

- FE Tenant Settings retention tab (separate 57.134 follow-on #3).
- Partition lifecycle / pg_partman / default partition (57.134 follow-on #2; Ops slice).
- Per-tenant interval / per-tenant enable override (YAGNI — one global interval v1).
- `Tenant.state`-based filtering (run ALL tenants v1; state-aware skipping deferred).
- audit_log retention (audit is WORM; out of scope).
- `core.config` Settings fields (plain env keeps the change localized + dodges the lru_cache trap).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0 · run_all 10/10 · pytest (2741 + new) · black/isort/flake8 clean · LLM-SDK-leak clean. (Vitest / mockup / build = N/A — pure backend, frontend UNTOUCHED.) Plus the §3.2 drive-through (US-4, MANDATORY runtime verification).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/platform_layer/transcripts/retention.py` | EDIT (+ SweepStats + run_transcript_retention_sweep) |
| 2 | `backend/src/api/main.py` | EDIT (+ poll loop + _start_* + lifespan startup/shutdown wiring) |
| 3 | `backend/tests/unit/platform_layer/transcripts/test_retention_sweep.py` | NEW |
| 4 | `backend/tests/unit/api/test_main_lifespan.py` | EDIT (job env-flag default-OFF + start-when-enabled) |
| — | `backend/src/infrastructure/db/migrations/**` | **UNTOUCHED** (no schema) |
| — | `backend/src/core/config.py` | **UNTOUCHED** (plain env) |
| — | `frontend/**` · event wire schema | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `run_transcript_retention_sweep` enumerates ALL tenants, deletes each tenant's transcripts past its `retention_days`, audits (`tenant_transcript_retention_scheduled`, `user_id=None`), commits per tenant, and is fail-open (one tenant raising does NOT abort the others — `tenants_failed` increments, the rest still processed).
2. The job starts ONLY when `TRANSCRIPT_RETENTION_JOB_ENABLED=true`; the poll loop runs the sweep once at startup then every `TRANSCRIPT_RETENTION_JOB_INTERVAL_S`; shutdown cancels promptly.
3. **Default OFF** — env unset → `_start_transcript_retention_job` returns early, no task created (test-asserted).
4. **Drive-through PASS (MANDATORY runtime, real backend + real DB)** — backend started with the job ENABLED + a short interval + a seeded old transcript on a THROWAWAY tenant → the job auto-deletes it within one interval; startup log + DB row-count before/after captured in progress.md. Background job has NO UI → runtime-verified (NOT a UI drive-through, NOT gate-only).
5. 57.134 follow-on #1 CLOSED; CHANGE-102; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `run_transcript_retention_sweep` + `SweepStats` (per-tenant apply+audit+commit, fail-open)
- [ ] US-2 `_transcript_retention_poll_loop` + `_start_transcript_retention_job` + lifespan startup/shutdown wiring
- [ ] US-3 default-OFF env gate + per-tenant audit + fail-open (tests)
- [ ] US-4 runtime drive-through (real backend + short interval + seeded throwaway tenant → auto-delete)
- [ ] US-5 CHANGE-102 + retro + navigators + next-phase-candidates

## 7. Workload Calibration

- Scope class **NEW `scheduled-job-mirror-spike` 0.55** (1st data point). Mirrors the proven billing-outbox drainer lifecycle (`main.py:267-336`) + reuses 57.134 `apply_transcript_retention` → mostly composition/wiring; the per-tenant sweep + fail-open + audit + the timed runtime drive-through (short-interval + seed + observe) add a bit over a pure-wiring spike. Kin to `transcript-retention-apply-spike` 0.60 (57.134) but lighter on novel logic (the delete primitive already exists) → 0.55. If the 1st data point diverges > 30%, re-point.
- **Agent-delegated: no** (parent-direct — small focused backend change + a timed runtime drive-through that needs careful real-server observation). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6 hr (sweep ~1.5 · job+lifespan ~1.5 · tests ~1.5 · drive-through ~1 · docs ~0.5) → class-calibrated commit ~3.3 hr (mult 0.55). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Destructive job deletes REAL data in dev | Default OFF (opt-in env); drive-through deletes only on a THROWAWAY tenant (mirror 57.134 Leg-2); never enable on acme-prod beyond the test window |
| **Risk Class E** — stale `--reload` / orphan spawn-worker masks the job startup (env read at startup) | Clean restart for the drive-through: kill stale uvicorn + verify sole live worker (Win32_Process PID/PPID/StartTime); set the env BEFORE restart |
| **Risk Class C** — module singletons across test event loops (lifespan test) | Mirror `test_main_lifespan.py` existing patterns; don't introduce a module-level singleton; inject `session_factory` |
| `get_settings()` lru_cache timing trap | Read enable + interval as plain `os.environ` (mirror the billing enable flag) — NO `core.config` field |
| Sweep holds one long txn across many tenants | Per-tenant fresh session + commit-per-tenant (no cross-tenant txn); fail-open isolates a bad tenant |
| First sweep runs immediately at startup (could delete on a mis-set interval) | Intended (mirror billing loop runs once before waiting); guarded by default-OFF + throwaway-tenant drive-through |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- FE Tenant Settings retention tab — 57.134 follow-on #3 (frontend slice).
- Partition lifecycle / pg_partman / default partition — 57.134 follow-on #2 (Ops slice).
- Per-tenant interval / enable override — YAGNI (one global config v1).
- `Tenant.state`-aware skipping (e.g. skip suspended) — deferred; v1 runs all tenants.
- TEAMMATE/HANDOFF subagent Tree relay verification — separate (surfaced by the 2026-06-17 subagent diagnostic).
