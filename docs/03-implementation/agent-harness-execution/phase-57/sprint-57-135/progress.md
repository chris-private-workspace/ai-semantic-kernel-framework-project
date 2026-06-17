# Sprint 57.135 Progress — scheduled transcript-retention background job

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-135-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-135-checklist.md)

---

## Day 0 — 2026-06-17 — Plan-vs-Repo Verify (三-prong) + Branch

**Base**: `main` HEAD `c98b6368` (post-#316 Leg-2-closure merge). Branch `feature/sprint-57-135-scheduled-transcript-retention` (commit 1 = subagent-AD-closure docs `c629b8d3`).

### Drift findings (三-prong)

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-tenant-enum | 2 | `Tenant` (identity.py:112,156,119) has `id` + `retention_days` (NOT NULL ≥1) + `state` (TenantState enum); **no soft-delete column** (no `deleted_at`) | Enumerate ALL tenants via `select(Tenant.id, Tenant.retention_days)`; `state` is a lifecycle enum, NOT a soft-delete → no filter v1 (per plan §3.1) |
| D-lifespan-test | 2 | `test_main_lifespan.py` drives lifespan via `TestClient(app)` ctx-manager (`load_dotenv` / pricing / sla wiring tests) | Test `_start_transcript_retention_job` **directly** (NOT via full lifespan) — driving lifespan with the job ENABLED would run a real sweep against the test DB. Default-OFF + mocked-loop unit tests. |
| D-billing-loop-first-run | 2 | `_billing_outbox_poll_loop` runs `drain_once()` at `main.py:280` BEFORE the first `wait_for(stop_event.wait(), timeout)` at `:291` | The retention sweep also runs ONCE at startup, then every interval — drive-through with a short interval sees the immediate first sweep |
| D-append-audit-sig | 2 | `append_audit(session, *, tenant_id, operation, resource_type, operation_data, user_id=None, …)` — `user_id` OPTIONAL (`audit_helper.py:90-102`) | System sweep audits with `user_id=None` (no admin user) ✅ |
| D-apply-no-commit | 2 | `apply_transcript_retention` (retention.py:66-111) is pure delete/count — does NOT commit or audit (docstring + body confirm caller owns the txn) | The sweep owns the per-tenant txn: apply → audit → commit ✅ |
| Prong 3 (schema) | 3 | N/A — no new table / migration / ORM column (reuses `Tenant.retention_days` + `Message`/`MessageEvent` + `audit_log`) | — |

### Baselines (57.134 closeout; backend unchanged on main since — only docs PRs #316 + the AD-closure docs commit)

pytest **2741 + 5 skip** · mypy `src` **0/374** · run_all **10/10**. (Vitest / mockup / wire = N/A — pure backend.) Re-verify at the full gate (Day 2).

### Go/no-go

All prongs **GREEN**; no scope-shift drift (0% shift — the plan's recon held). **PROCEED to Day 1.** The fix composes two existing things (57.134 `apply_transcript_retention` + the billing drainer lifecycle); no new primitive, no schema.

### Note

The subagent-AD-closure (`AD-Subagent-Child-Event-SSE-Relay`, found stale/YAGNI by a 2026-06-17 diagnostic) rides as commit 1 on this branch (`chore(docs)` scope, separate concern) — will be noted in the PR body.

---

## Day 1 — 2026-06-17 — Sweep + background job (US-1/2/3)

- **`retention.py`**: added `SweepStats` + `run_transcript_retention_sweep(session_factory, *, now=None)` — enumerate `select(Tenant.id, Tenant.retention_days)` (all tenants); per tenant a fresh txn `apply_transcript_retention → append_audit("tenant_transcript_retention_scheduled", user_id=None) → commit`; per-tenant `except` → log + `tenants_failed += 1` + continue (fail-open).
- **`api/main.py`**: `_transcript_retention_poll_loop` (sweep once → log if any deleted/failed → `wait_for(stop_event, interval)`) + `_start_transcript_retention_job` (env `TRANSCRIPT_RETENTION_JOB_ENABLED` default `"false"`; interval env default 86400; `create_task` + `app.state.transcript_retention_{task,stop}`) + lifespan startup call (after billing drainer) + shutdown cancel (mirror billing, before OTel/engine teardown).
- Partial gate: mypy `src` 0/374 · black/isort/flake8 clean (2 E501 in MHist/Key-Components docstrings trimmed).

## Day 2 — 2026-06-17 — Tests + full gate (US-1/3)

- **`test_retention_sweep.py`** (NEW, +4): processes-all-tenants (apply+audit+commit per tenant, aggregate) · fail-open-per-tenant (one raises → `tenants_failed=1`, rest processed) · no-tenants (all-zero) · passes-`now`-to-apply. Fake async-CM session factory + monkeypatched `apply_transcript_retention` / `append_audit`.
- **`test_main_lifespan.py`** (EDIT, +2): job default-off (env unset → no task) · starts-enabled (env true → task + stop event on `app.state`; poll loop patched to a no-op that blocks on stop_event so NO real sweep hits the DB; cleaned up).
- **Full gate ALL GREEN**: mypy `src` **0/374** · run_all **10/10** · backend pytest **2747 passed / 5 skipped** (baseline 2741 +6) · black/isort/flake8 clean · LLM-SDK-leak clean · frontend UNTOUCHED.
- Note: test-file standalone `mypy <file>` shows import-untyped artifacts (wrong invocation); the authoritative gate `mypy src` is clean (tests not in the mypy-src scope; 57.134 added tests + still reported `mypy src 0/374`).

## Day 3 — 2026-06-17 — Drive-through (US-4) — real backend + real DB (NO UI; runtime verification)

**Observed vs intended**: the scheduled job's startup sweep auto-deleted an expired transcript on a throwaway tenant, kept the recent one, audited it — exactly as intended; no UI (background job), so this is a real RUNTIME verification (NOT gate-only, NOT a UI drive-through).

- **Clean restart (Risk Class E)**: killed the stale dev uvicorn (PID 55768 reloader) + an **orphan spawn-worker** (PID 54788, PPID=dead-55768, cmdline `python -c "from multiprocessing..."` — the 57.97 trap; the `Listen` socket was stale-attributed to the dead parent, found via `Get-CimInstance Win32_Process` PID/PPID); confirmed PORT 8000 FREE; started a fresh single-process uvicorn (PID 43144) with `TRANSCRIPT_RETENTION_JOB_ENABLED=true` + `TRANSCRIPT_RETENTION_JOB_INTERVAL_S=10` set BEFORE start.
- **Seed**: throwaway tenant `656968f4-…` (retention 30) + an OLD message+event (now-60d) + a RECENT one (now-5d). BEFORE: `MESSAGES=2 SCHEDULED_AUDITS=0`.
- **THE job (real backend + real DB)**: startup log `transcript retention job started (interval=10s)`; the startup sweep ran → log `transcript retention sweep — tenants=5000 failed=0 messages_deleted=1 events_deleted=1` (enumerated all 5000 dev tenants, fail-open clean, deleted exactly the expired row). AFTER: **`MESSAGES=1`** (recent now-5d survived) **`SCHEDULED_AUDITS=1`** (the system audit row). Default-OFF re-confirmed on the normal restart (log `transcript retention job disabled (env; default off)`).
- **Cleanup**: deleted the throwaway tenant (CASCADE + audit_log WORM-trigger toggle) → `MESSAGES=0 SCHEDULED_AUDITS=0`; restored the normal dev backend (PID 56292, job OFF).
- Evidence: `artifacts/{seed_drivethrough,verify_sweep,cleanup_drivethrough}.py` + the log lines above.
- Observation (non-blocker): one sweep over 5000 dev tenants took ~44s (per-tenant session+commit). Fine for the daily (86400s) cadence; a future optimization could batch, but the per-tenant txn + fail-open isolation is the correct trade-off. Logged for the retro.

---
