# Sprint 57.135 — Checklist (scheduled transcript-retention background job)

[Plan](./sprint-57-135-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `c98b6368`)
- [x] **Prong 1 — path verify**: `platform_layer/transcripts/retention.py` + `__init__.py` present · `api/main.py` present · `infrastructure/db/audit_helper.py` present · `infrastructure/db/models/identity.py` + `sessions.py` present · `tests/unit/platform_layer/transcripts/` + `tests/unit/api/test_main_lifespan.py` present · `CHANGE-102` free
- [x] **Prong 2 — content verify** (drift → progress.md Day-0 table):
  - [x] **D-tenant-enum** — `Tenant` has id + retention_days; NO soft-delete column → ALL-tenants enumeration ✅
  - [x] **D-lifespan-test** — `test_main_lifespan.py` drives lifespan via TestClient → test `_start_transcript_retention_job` DIRECTLY (job-enabled lifespan would run a real sweep on the test DB) ✅
  - [x] **D-billing-loop-first-run** — `drain_once()` runs at `main.py:280` BEFORE `wait_for` `:291` → sweep runs once at startup ✅
  - [x] **D-append-audit-sig** — `append_audit` `user_id` optional → system audit `user_id=None` ✅
  - [x] **D-apply-no-commit** — `apply_transcript_retention` pure delete/count, caller owns txn ✅
- [x] **Prong 3 — schema verify**: N/A (no new table / migration / ORM column — reuses `Tenant.retention_days` + `Message`/`MessageEvent` + `audit_log`)
- [x] **D-baselines** — pytest 2741+5skip · mypy `src` 0/374 · run_all 10/10 (57.134; backend unchanged on main since — re-verify Day 2 full gate)
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — 0% scope-shift, all prongs GREEN → **PROCEED**

### 0.2 Branch
- [x] `feature/sprint-57-135-scheduled-transcript-retention` (from `main` `c98b6368`; commit 1 = subagent-AD-closure `c629b8d3`)

---

## Day 1 — Sweep + background job (US-1 / US-2 / US-3)

### 1.1 Sweep — `platform_layer/transcripts/retention.py`
- [x] **`SweepStats` + `run_transcript_retention_sweep(session_factory, *, now=None) -> SweepStats`** ✅
  - Enumerate `select(Tenant.id, Tenant.retention_days)` (ALL tenants); per tenant fresh txn: `apply_transcript_retention` → `append_audit("tenant_transcript_retention_scheduled", user_id=None)` → `commit`; per-tenant `except` → log + `tenants_failed += 1` + continue (fail-open)

### 1.2 Background job — `api/main.py` (mirror `_billing_outbox_*`)
- [x] **`_transcript_retention_poll_loop(session_factory, interval_s, stop_event)`** — sweep once → log if any deleted/failed → `wait_for` ✅
- [x] **`_start_transcript_retention_job(app)`** — env `TRANSCRIPT_RETENTION_JOB_ENABLED` default `"false"` (DEFAULT OFF); interval default `86400`; `create_task` + `app.state.transcript_retention_{task,stop}` ✅
- [x] **lifespan wiring** — startup call after `_start_billing_outbox_drainer`; shutdown set stop_event + `wait_for(task,10)` + cancel BEFORE OTel/engine teardown ✅

### 1.x Partial gate
- [x] mypy `src` 0 · black/isort/flake8 clean (2 docstring E501 trimmed) ✅

---

## Day 2 — Tests + full gate (US-1 / US-3)

### 2.1 Tests
- [x] **unit `test_retention_sweep.py`** (NEW, +4) — processes-all-tenants + **fail-open** (one raises → `tenants_failed=1`, rest processed) + no-tenants + passes-`now` ✅
- [x] **lifespan `test_main_lifespan.py`** (EDIT, +2) — default-OFF (env unset → no task) + starts-enabled (poll loop patched no-op, no real DB sweep) ✅
- [x] conftest sweep — **N/A** (unit tests mock; the live drive-through tenant used the `TRANSCRIPTRET_%` prefix already covered by the 57.134 conftest sweep + was cleaned up manually)

### 2.x Full gate
- [x] mypy `src` **0/374** · run_all **10/10** · backend pytest **2747+5skip** (+6) · black/isort/flake8 clean · LLM-SDK-leak clean · frontend UNTOUCHED ✅

---

## Day 3 — Drive-through (US-4) — real backend + real DB (NO UI — runtime verification)
_(Background job has NO UI surface → this is a REAL runtime verification, NOT a UI drive-through and NOT gate-only. State that honestly.)_

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale uvicorn (PID 55768) + **orphan spawn-worker (PID 54788, dead-parent stale-attribution; 57.97 trap)** via Win32_Process PID/PPID; PORT 8000 FREE; started fresh single-proc uvicorn PID 43144 with `TRANSCRIPT_RETENTION_JOB_ENABLED=true` + `INTERVAL_S=10` set BEFORE start; startup log `transcript retention job started (interval=10s)` ✅

### 3.2 Drive-through (MANDATORY runtime — NOT gate-only)
- [x] Seeded THROWAWAY tenant `656968f4` retention 30 + OLD (now-60d) + RECENT (now-5d); BEFORE `MESSAGES=2 SCHEDULED_AUDITS=0` ✅
- [x] **THE job (real backend + real DB)**: startup sweep log `transcript retention sweep — tenants=5000 failed=0 messages_deleted=1 events_deleted=1`; AFTER **`MESSAGES=1`** (recent survived) **`SCHEDULED_AUDITS=1`**; default-OFF re-confirmed on normal restart (`retention job disabled (env; default off)`) ✅
- [x] Cleanup throwaway tenant (CASCADE + WORM toggle) → `MESSAGES=0 SCHEDULED_AUDITS=0`; restored normal dev backend PID 56292 (job OFF) ✅
- [x] Evidence → progress.md Day 3 + `artifacts/{seed,verify,cleanup}_drivethrough*.py` ✅

---

## Day 4 — CHANGE-102 + closeout

### 4.1 CHANGE-102
- [x] **`CHANGE-102-scheduled-transcript-retention-job.md`** ✅ (gap manual-only → scheduled; sweep + drainer-mirror; default-OFF; drive-through PASS; follow-on #1 CLOSED). NO design note.

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`scheduled-job-mirror-spike` 0.55→**0.85** re-pointed, 1st data point, ceremony-not-code-accelerated) ✅
- [x] Final gate sweep: mypy src 0/374 · run_all 10/10 · pytest 2747+5skip · black/isort/flake8 clean · LLM-SDK-leak clean ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (follow-on #1 CLOSED + 57.135 block) · sprint-workflow matrix (`scheduled-job-mirror-spike` 0.85 NEW row) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 10/10 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
