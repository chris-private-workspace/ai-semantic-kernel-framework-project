# CHANGE-102: scheduled transcript-retention background job

**Date**: 2026-06-17
**Sprint**: 57.135
**Scope**: platform_layer.transcripts (data lifecycle) + api (lifespan) — backend-only, NO migration

## Problem

Sprint 57.134 shipped MANUAL transcript retention (an admin POST `/{id}/transcript-retention/apply` deletes one tenant's expired transcripts; a preview GET counts them). There was no AUTOMATIC enforcement — `tenants.retention_days` was an advisory number that nothing enforced unless an operator manually triggered each tenant. (57.134 carryover follow-on #1.)

## Root Cause

The delete primitive `apply_transcript_retention` existed but its only caller was the admin POST. No scheduler/background job enumerated tenants and applied retention periodically.

## Solution

Composed two EXISTING things — the 57.134 `apply_transcript_retention` + the billing-outbox drainer lifecycle — into a scheduled sweep:

- **`platform_layer/transcripts/retention.py`**: `SweepStats` + `run_transcript_retention_sweep(session_factory, *, now=None)` — enumerate `select(Tenant.id, Tenant.retention_days)` (ALL tenants); per tenant a FRESH txn `apply_transcript_retention → append_audit("tenant_transcript_retention_scheduled", user_id=None) → commit`; **fail-open per tenant** (a per-tenant exception → log + `tenants_failed += 1` + continue). Returns aggregate `SweepStats`.
- **`api/main.py`** (mirror `_billing_outbox_*`): `_transcript_retention_poll_loop` (sweep once at start, then every interval; `wait_for(stop_event, interval)` for prompt shutdown; fail-open) + `_start_transcript_retention_job` (env `TRANSCRIPT_RETENTION_JOB_ENABLED` **default `"false"`** — destructive opt-in; interval env `TRANSCRIPT_RETENTION_JOB_INTERVAL_S` default 86400; `create_task` + `app.state.transcript_retention_{task,stop}`) + lifespan startup call (after the billing drainer) + shutdown cancel (set stop_event + `wait_for(task,10)` + cancel, before OTel/engine teardown).

**Key decision**: DEFAULT OFF (vs the billing drainer's default-ON) — the job DELETES transcripts (irreversible), so it must be explicit opt-in so an unconfigured environment never deletes data. Plain-env config (no `core.config` Settings schema change — dodges the lru_cache trap, mirrors the billing enable flag).

PR: feature/sprint-57-135-scheduled-transcript-retention.

## Verification

- Gates: mypy `src` **0/374** · run_all **10/10** · backend pytest **2747 passed / 5 skipped** (baseline 2741 +6: 4 sweep unit + 2 lifespan-job) · black/isort/flake8 clean · LLM-SDK-leak clean · frontend UNTOUCHED.
- Tests: `tests/unit/platform_layer/transcripts/test_retention_sweep.py` (processes-all-tenants + fail-open-per-tenant + no-tenants + passes-`now`) · `tests/unit/api/test_main_lifespan.py` (job default-OFF + starts-when-enabled with the poll loop patched to a no-op).
- **Drive-through PASS (real backend + real DB; background job has NO UI → runtime verification, NOT gate-only)**: clean restart (killed a stale reloader + an orphan spawn-worker — 57.97 trap) → fresh uvicorn PID 43144 with the job ENABLED + interval 10s. Seeded a throwaway tenant (retention 30) with an OLD (now-60d) + RECENT (now-5d) transcript (BEFORE `MESSAGES=2`). The startup sweep logged `transcript retention sweep — tenants=5000 failed=0 messages_deleted=1 events_deleted=1`; AFTER `MESSAGES=1` (recent survived) `SCHEDULED_AUDITS=1`. Default-OFF re-confirmed on the normal restart. Cleaned up (`MESSAGES=0`). Evidence: `docs/.../sprint-57-135/artifacts/{seed,verify,cleanup}_drivethrough*.py` + progress.md Day 3.

## Impact

Backend-only; NO migration, NO new table/ORM column/event/frontend (reuses `Tenant.retention_days` + `Message`/`MessageEvent` + `audit_log`). Closes 57.134 follow-on #1. Opt-in (default OFF) → zero behavior change until an operator sets `TRANSCRIPT_RETENTION_JOB_ENABLED=true`. Out of scope (separate follow-ons): FE retention tab (#3), partition lifecycle / pg_partman (#2), per-tenant interval, `Tenant.state`-aware skipping.
