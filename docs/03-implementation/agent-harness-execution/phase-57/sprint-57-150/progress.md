# Sprint 57.150 Progress — memory user-layer write-side dedup (upsert-by-key)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-150-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-150-checklist.md)

---

## Day 0 — 2026-06-30 — Plan-vs-Repo Verify (三-prong) + Branch

### Baselines (57.149 closeout, re-verify Day 2 + Day 4)
pytest 3013 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11.

### Drift findings (三-prong)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-rowcount-tests** | `test_extraction_worker.py:100 assert len(new_ids)==2` writes TWO DIFFERENT facts ("tables over prose" + "in finance") AND uses a MOCK `_RecordingLayer` (never hits real write) → unaffected. `test_memory_ops_rls.py:142 test_user_layer_write_op_same_txn_rollback` uses the REAL UserLayer.write but writes a SINGLE fact → still 1 row. | ✅ both compatible; the real-write rls test needs migration 0032 in the test DB (CI runs `alembic upgrade head`) so the `uq_memory_user_dedup` conflict target exists |
| **D-write-unit-tests** | `test_user_layer.py` `test_write_long_term_no_expires` + `test_write_short_term_sets_24h_expiry` assert `session.add(MemoryUser)`; `_build_factory` configures `scalar_one_or_none` but NOT `scalar_one`. ON CONFLICT shifts write() to `session.execute(pg_insert…returning).scalar_one()` (only the MemoryOp stays `session.add`). | ⚠️ adapt: add `scalar_one` to the mock; assert `session.execute` awaited + MemoryOp recorded + returned id; RELOCATE the long_term/short_term expires assertions to the real-DB integration test (NOT delete — Never Delete Tests) |
| **D-greatest-numeric** | `func.greatest(Numeric, Numeric)` is valid PG and ignores NULLs (NULL confidence handled). | ✅ verified at integration; mock just needs `scalar_one` |
| **D-migration-backfill-regex** | Python `re.sub(r"\s+", " ", content).strip().lower()` (collapse→trim→lower) ↔ SQL `lower(btrim(regexp_replace(content, '\s+', ' ', 'g')))` (collapse→trim→lower) → identical bytes → identical md5 for ASCII whitespace. | ✅ integration test writes a backfilled-style row + a live repeat → asserts they collide to 1 row |
| **D-all-writers** | `extraction.py:50/75-77` holds `UserLayer` + calls `self._user_layer.write(...)` (57.149 auto_extract); nudge → `memory_tools.py:352` → `layer.write(...)`; agent `memory_write` same. | ✅ single chokepoint `UserLayer.write` — all 3 writers dedup for free |

### Prong 1 (path) ✅
EDIT targets present: `memory.py`, `user_layer.py`, `test_user_layer.py`. NEW free: `0032_memory_user_dedup_key.py`, `test_user_layer_dedup.py`, `CHANGE-117-*.md`. Migration 0031 is latest → 0032 next.

### Prong 3 (schema) ✅
`memory_user` (`memory.py:205-264`): `source`/`updated_at` present, `__table_args__` = 3 Index, NO UniqueConstraint. `UniqueConstraint` already imported (`memory.py:65`). `memory_user` RLS in 0009 (0032 adds NO RLS). `dedup_key` additive nullable.

### Go/no-go
Scope-shift ~0% (additive column + write rewrite + bounded test refactor). **Proceed.**

### Branch
`git checkout -b feature/sprint-57-150-memory-upsert-dedup` from `main` `7460f23b` ✅.

---

## Day 1 — 2026-06-30 — ORM + migration 0032 (US-2)

### Done
- `memory.py` — `MemoryUser.dedup_key String(32) nullable` + `UniqueConstraint("tenant_id","user_id","dedup_key", name="uq_memory_user_dedup")` in `__table_args__`; MHist + Last Modified.
- `0032_memory_user_dedup_key.py` — upgrade: add column → backfill `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` → dedup existing (row_number keep highest-confidence/newest) → `create_unique_constraint`; downgrade: drop constraint → drop column. NO RLS change.
- Gate: black/isort clean; flake8 — 2 E501 (MHist 117/107 > 100) → shortened → clean; mypy 3 files Success.
- Migration `alembic upgrade head` → `downgrade -1` → `upgrade head` clean; current = 0032 head (the `�X` in alembic log = console encoding of the em-dash, not an error).

## Day 2 — 2026-06-30 — write() upsert + tests (US-1, US-3) + full gate

### Done
- `user_layer.py` — `_dedup_key(content)` module helper (`re.sub(r"\s+"," ",c).strip().lower()` → `hashlib.md5(..., usedforsecurity=False).hexdigest()`); `write()` → `pg_insert(MemoryUser).values(...).on_conflict_do_update(constraint="uq_memory_user_dedup", set_={content, confidence=greatest, expires_at, updated_at=now()}).returning(MemoryUser.id).scalar_one()`. KEEP first writer's source/metadata (NOT in set_); `_record_memory_op` still emits; own-session (no SAVEPOINT). Imports: `hashlib`/`re`/`func`/`pg_insert`.
- `test_user_layer.py` — `_build_factory` += `scalar_one_value`; 2 write tests adapted to upsert shape (assert execute + MemoryOp + NO MemoryUser-add); +3 `_dedup_key` tests; removed now-unused `timedelta` import.
- `test_user_layer_dedup.py` (NEW, 6 tests) — same fact ×2 → 1 row + conf max + content latest + 2 op rows; lower-conf repeat keeps greatest; distinct facts → 2 rows; per-tenant (no cross-tenant collapse); long_term no-expiry + short_term 24h (relocated from unit). commit→flush shared-session trick (mirror `test_memory_ops_rls`).
- `test_ops_emit.py` — `test_user_write_emits_write_op_same_session` adapted (the MemoryUser is now an `execute()` not `session.add` — Risk-C same-session/one-commit preserved).

### Gate (Day 2.4)
mypy `src` 0 errors / 393 files (392 + migration) · run_all **11/11** green (incl. llm_sdk_leak + rls_policies) · pytest **3022 passed / 6 skipped** (3013 +9: +3 _dedup_key unit + 6 dedup integration; the 2 write tests transformed, ops_emit edited) · black/isort/flake8 clean (6 files) · migration up→down→up clean · FE untouched (Vitest 922 / mockup 51).

### Note (run_all count)
`run_all.py` reports **11/11** lint scripts (the "25" in some prior sprint notes was a mis-record; 11 is the actual script count incl. llm_sdk_leak + rls_policies + tool_descriptions).

---

## Day 3 — 2026-06-30 — Drive-through (US-4) — real UI + real backend + real LLM — ALL PASS

### Clean restart (Risk Class E)
Killed the stale port-8000 backend (PID 22760, 1:25PM, pre-57.150 code); confirmed port 8000 free + 0 python orphans; the stale 57.149 background backend (b5sott3hx) was already dead. Started a fresh no-reload uvicorn on branch code (PID 43620) against the migrated dev DB (`alembic upgrade head` = 0032); startup log clean ("startup complete", pricing loader wired); node frontend (vite 3007) + claude-code UNTOUCHED. Confirmed dev DB has `dedup_key` backfilled on all 9 existing dan rows (0032 applied).

### Drive-through (real chat-v2 + real Azure gpt-5.2) — dan@acme.com (tenant acme-prod)

**THE dedup fix — verbatim repeat collapses to one row:**
- **Send 1** ("save this fact verbatim: 'Project Helix DT150 is built in Rust and ships in November 2027.'"): agent called `memory_write` (scope=user, content verbatim, conf 0.6, entry_id b5148920) → confirmed "Saved", verification 0.99. DB after send 1: **exactly 1 row** matching "Helix DT150" — `key=dd16b505…` `conf=0.99` `created=07:08:54.868` `updated=07:09:01.629 (BUMPED)`. **Intra-send dedup proven LIVE**: the agent's `memory_write` (source=none, conf 0.6) + the auto_extract BackgroundTask (~7s later, conf 0.99) BOTH wrote the same verbatim fact → upsert collapsed them to ONE row, `confidence` = greatest(0.6, 0.99) = 0.99, `updated_at` bumped, **first writer's source (none) preserved** (NOT relabelled auto_extract). Pre-57.150 this would have been 2 rows.
- **Send 2** ("save this exact fact to memory again, verbatim: '…'"): agent `memory_write` again. DB after send 2: **STILL exactly 1 row** — same `key=dd16b505…`, `created` unchanged (07:08:54), `updated=07:10:14.740 (BUMPED again)`. **Cross-send dedup proven**: across 2 sends (3-4 same-fact write attempts: 2× memory_write + auto_extract) the row count stayed at **1**, `updated_at` bumping each time.
- **Clean recall** (new session, 07:12): "What do you remember about Project Helix DT150?" → agent recalled **once, cleanly**: "I remember that Project Helix DT150 is built in Rust and ships in November 2027." — surfaced via `profile()` inject (not stated in this session), NO dilution / repetition.

**Net**: pre-57.150 = 2-4 rows for one fact (diluting `profile()` top-k); post-57.150 = **1 row**, greatest confidence, latest content, first-writer provenance, recalled once.

### Evidence
- Screenshots: `artifacts/dt150-chat-dedup.png` (send 1+2 + the 2 `memory_write` tool calls), `artifacts/dt150-clean-recall.png` (new-session single clean recall).
- DB inspector: `scratchpad/dt150_db.py` (backend `get_session_factory` + `set_config('app.tenant_id')` FORCE-RLS; shows dedup_key + created/updated). dan user `cf2b40a1…` tenant `09eb1b62…`.
- Session id (send 1+2): `69b0b5ec-76c4-435f-9867-33c856497295`; trace `7c0a0067…`.

### NOT gate-only
This is a real UI + real backend + real Azure LLM drive-through (per the Drive-Through Hard Constraint), not a curl/probe. The deterministic dedup LOGIC is additionally covered by the 6 real-Postgres integration tests (`test_user_layer_dedup.py`).
