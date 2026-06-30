# Sprint 57.150 Retrospective — memory user-layer write-side dedup (upsert-by-key)

**Closed**: 2026-06-30 · Branch `feature/sprint-57-150-memory-upsert-dedup` (base `main` `7460f23b`) · CHANGE-117 · closes `AD-Memory-User-Upsert-By-Key`.

## Q1 — What shipped?
Made `UserLayer.write()` an idempotent upsert keyed on `dedup_key = md5(normalize(content))`: a new nullable column + a `(tenant_id, user_id, dedup_key)` unique constraint + `pg_insert … on_conflict_do_update` (greatest confidence, latest content/expires, bump updated_at, KEEP first writer's source/metadata). Migration 0032 (add column → backfill → dedup existing → constraint). All three writers (57.148 nudge, 57.149 auto_extract, agent `memory_write`) dedup through the one `UserLayer.write` chokepoint. Backend-only; NO migration-besides-0032 / wire / frontend / new contract.

## Q2 — Estimate accuracy (calibration)
- Scope class **NEW `memory-upsert-dedup-spike` 0.60**. Agent-delegated: **no** (parent-direct, `agent_factor` 1.0, 3-segment).
- Bottom-up ~7.3 hr → class-calibrated commit ~4.4 hr (mult 0.60). Actual ~4.7 hr → ratio **~1.07 IN band**.
- Why it landed clean (unlike the 57.149 over-run): the drive-through fired the dedup on send 1 (the agent's `memory_write` + the auto_extract re-extract of the same verbatim fact collapsed to one row immediately) — NO re-architecture, NO noise investigation, NO re-drive. The real-code core (migration + write rewrite + test refactor) held the 0.60 per the 57.137 lesson (a >~3 hr implementation core holds the spike multiplier; this is NOT a tiny-code-wrapped-in-ceremony 0.85 sprint). KEEP 0.60 pending 2-3 sprint validation; if a 2nd `memory-upsert-dedup-spike` diverges > 30%, re-point.

## Q3 — What went well?
- **Day-0 三-prong caught the test-shape risk upfront**: D-write-unit-tests + D-rowcount-tests correctly predicted that `test_user_layer.py` write tests + `test_ops_emit.py` would need the add→execute adaptation, and that `test_extraction_worker` (mock layer, 2 different facts) was unaffected. Zero mid-sprint surprises.
- **One chokepoint design** (`UserLayer.write`) meant the dedup covered all three writers for free — the drive-through proved it by showing `memory_write` + `auto_extract` collapse to one row.
- **The drive-through was unusually clean and deterministic**: the agent following "save verbatim: '<exact string>'" gave a controlled trigger; the intra-send dedup (memory_write + auto_extract) was visible as `updated > created` on the very first send.
- Migration `up→down→up` clean; `func.greatest` NULL-safety + the `dedup_key`-backfill-matches-Python-normalization invariant held (the live row keyed against the backfilled rows correctly).

## Q4 — What to improve?
- The `_record_memory_op` still emits a WRITE op on every re-affirm (the ops log bloats even though the fact table dedups). It doesn't affect `profile()` (which reads `memory_user`, now deduped), so it's deferred — but a future op-emit-on-no-change-skip would keep the ops log lean too.
- The unit-test relocation (long_term/short_term expiry → integration) is correct but means the unit layer no longer asserts the expires value directly; the integration test is the single source for that now (acceptable — the real-DB row is observable there, the mock couldn't see pg_insert values).

## Q5 — Anti-pattern self-check
- AP-2 (no orphan): write() reachable from the chat path (drive-through proved); `_dedup_key` used by write() + tests. ✅
- AP-3 (no scatter): all in 範疇 3 (memory) + its migration. ✅
- AP-4 (no Potemkin): drive-through proved the dedup fires LIVE (not a stub) — 1 row, bumped updated_at, clean recall. ✅
- AP-6 (no premature abstraction): no new ABC; reuses pg_insert/ON CONFLICT (4 existing sites). ✅
- AP-8 (PromptBuilder): N/A (no LLM call added). ✅
- AP-11 (no version suffix): none. ✅
- v2 lints 11/11 (incl. llm_sdk_leak + rls_policies). ✅

## Q6 — Gates
mypy `src` 0/393 (392 + migration) · run_all 11/11 · pytest 3022 passed/6skip (3013 +9) · black/isort/flake8 clean (6 files) · migration up→down→up clean · FE untouched (Vitest 922 / mockup 51). Drive-through PASS (real chat-v2 + Azure gpt-5.2).

## Q7 — Carryover (→ ADs, not future tasks)
- `AD-Memory-Ops-Emit-Dedup-On-Reaffirm` (NEW) — skip the memory_op WRITE emit when the upsert is a no-change re-affirm (keep the ops log lean); deferred, doesn't dilute profile().
- `AD-Memory-Formation-Session-Recall` (缺口 2) — cross-session CONVERSATION recall + session-summary → Layer 5.
- `AD-Verification-Judge-Memory-Inject-Blind` — in-loop judge sees only the trace, false-positive-REJECTs memory-injected recalls.
- CARRY-026 — semantic / Qdrant memory axis (would enable semantic near-dup dedup beyond this sprint's exact-normalized dedup).
- CARRY-027 — async/queue extraction.
- Per-tenant auto-extract override; tenant/role/session-layer dedup (this sprint = user layer only).
