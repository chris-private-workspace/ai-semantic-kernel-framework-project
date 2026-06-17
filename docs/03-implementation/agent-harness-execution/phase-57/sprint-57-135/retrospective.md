# Sprint 57.135 Retrospective — scheduled transcript-retention background job

**Closed** 2026-06-17. Branch `feature/sprint-57-135-scheduled-transcript-retention` (from `main` `c98b6368`). Closes 57.134 follow-on #1. CHANGE-102; NO design note (continuation, not a spike).

## Q1 — What was delivered

A scheduled background job that auto-enforces per-tenant transcript retention: `run_transcript_retention_sweep` (enumerate all tenants → per-tenant apply+audit+commit, fail-open) in `retention.py` + `_transcript_retention_poll_loop` / `_start_transcript_retention_job` + lifespan startup/shutdown wiring in `api/main.py` (mirror of the billing-outbox drainer). DEFAULT OFF (destructive opt-in). +6 tests. Backend-only, NO migration.

## Q2 — Estimate accuracy / calibration

- Scope class **NEW `scheduled-job-mirror-spike`** — committed at **0.55** (bottom-up ~6 hr → ~3.3 hr). Parent-direct, `agent_factor` 1.0.
- Actual landed **notably OVER** the 0.55 commit (~1.4-1.5×): the mirror-code was small + quick (sweep ~40 lines + main.py ~50 lines + 6 tests), but the **drive-through ceremony dominated** — a Risk-Class-E orphan spawn-worker hunt (57.97 trap: dead-parent stale socket attribution), a clean single-proc restart, seed/verify/cleanup scripts, and the timed sweep observation.
- **Re-point 0.55 → 0.85** (1st data point). This is the same **ceremony-not-code-accelerated** insight as 57.120/122/123/126/129/132: a tiny-code + full-ceremony + parent-direct sprint WITH a mandatory drive-through lands ~0.85-1.0, NOT the 0.45-0.55 band — the plan/Day-0/drive-through/CHANGE/retro ceremony is fixed-cost and NOT code-hour-accelerated. If a 2nd `scheduled-job-mirror-spike` lands < 0.7 at 0.85, lower again.

## Q3 — What went well

- **Day-0 三-prong held 100%** — the plan's recon (billing drainer template + apply no-commit/no-audit + append_audit user_id-optional + Tenant fields) was all re-verified GREEN, 0% scope shift. The fix was pure composition (no new primitive, no schema), exactly as planned.
- The drive-through gave a **definitive real-DB proof** (MESSAGES 2→1, the sweep log `tenants=5000 failed=0 messages_deleted=1`, SCHEDULED_AUDITS=1) — not a paper claim.
- DEFAULT OFF (vs billing default-ON) was the right safety call for a destructive periodic job; re-confirmed live (`retention job disabled (env; default off)`).

## Q4 — What to improve

- The Risk-Class-E orphan-worker hunt cost real time (the `Listen` socket attributed to the dead reloader parent; the live worker was a `multiprocessing.spawn` child). The fix (Win32_Process PID/PPID sweep) is codified — but starting the drive-through backend as a single non-`--reload` process from the start (as I did) avoids the reloader+worker split next time.
- `scheduled-job-mirror-spike` 0.55 under-priced the drive-through ceremony — re-pointed to 0.85 (Q2). The lesson recurs: tiny-code + full-ceremony parent-direct → 0.85, not 0.55.

## Q5 — Anti-pattern self-check

- AP-2 (no orphan): the sweep + job are reachable from the lifespan startup (real flow); the drive-through proves the job runs end-to-end. ✅
- AP-3 (no scatter): sweep in `platform_layer/transcripts/retention.py` (data-lifecycle); the background job in `api/main.py` (the established home for background pollers, alongside the billing drainer). ✅
- AP-4 (no Potemkin): the job is drive-through proven (real deletion + audit). DEFAULT OFF is a deliberate opt-in safety default (tested + driven), NOT a dead stub. ✅
- AP-6 (no premature abstraction): reuses `apply_transcript_retention` + the billing drainer pattern; per-tenant interval / `Tenant.state` filter deliberately deferred (YAGNI). ✅
- AP-8 (PromptBuilder): N/A. AP-11 (no version suffix): none. ✅
- v2 lints **10/10**.

## Q6 — Drive-through honesty (約束)

The scheduled job has NO UI surface → the Day-3 verification is a REAL RUNTIME drive-through (real backend uvicorn PID 43144 + real DB + real lifespan + real poll loop), NOT a UI drive-through and NOT gate-only. Labeled as such in progress.md + CHANGE-102. The deletion + audit were observed in the real DB (not inferred from the gate).

## Q7 — Carryover

- 57.134 follow-on #1 (scheduled retention) **CLOSED**. Remaining 57.134 follow-ons: **#2 partition lifecycle** (pg_partman + default partition; Ops slice) · **#3 FE Tenant Settings retention tab** (frontend slice).
- **Observation (non-blocker)**: one sweep over 5000 dev tenants took ~44s (per-tenant session + commit). Fine for the daily (86400s) cadence; a future optimization could batch the enumeration/delete, but the per-tenant txn + fail-open isolation is the correct trade-off. If a tenant count grows much larger, revisit.
- **Possible refinement**: `Tenant.state`-aware skipping (e.g. skip suspended/provisioning) — deferred; v1 runs all tenants (correct: retention is state-independent).
- Separate (subagent diagnostic 2026-06-17): TEAMMATE/HANDOFF-mode Tree relay verification — only `fork` was driven.

## Design Note Extract

N/A — not a spike sprint (continuation of the 57.134 transcript-retention domain + an established drainer pattern; no new contract / ABC / wire event). NO design note.
