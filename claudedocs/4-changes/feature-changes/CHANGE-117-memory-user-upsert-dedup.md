# CHANGE-117: memory_user write-side dedup (upsert-by-key)

**Date**: 2026-06-30
**Sprint**: 57.150
**Scope**: 範疇 3 (Memory) — `UserLayer.write` + `MemoryUser` schema (backend-only)

## Problem
`UserLayer.write()` always INSERTed a fresh `uuid4()` row, so the same durable user fact accumulated duplicate rows. Sprint 57.149 made this worse by running an `auto_extract` MemoryExtractor as a BackgroundTask after EVERY chat send — when the conversation re-surfaces a fact (or the agent's `memory_write` nudge and the auto_extract both capture it verbatim), each writes a separate row. The duplicates dilute the always-on 57.148 `profile()` top-k (`top_k=5`, confidence-ordered): one fact repeated 5× fills all five identity slots and crowds out the user's other facts. The dup count grew every send → the problem compounded. Deferred from 57.149 as `AD-Memory-User-Upsert-By-Key`.

## Root Cause
No uniqueness on `memory_user` — `__table_args__` had three indexes but no `(tenant, user, content)` constraint, and `write()` had no dedup path. Every write was an unconditional INSERT (`user_layer.py:144-157`).

## Solution
Make `UserLayer.write()` an idempotent upsert keyed on a normalized fact hash. One chokepoint covers all three writers (57.148 nudge `memory_write` tool, 57.149 `auto_extract`, any agent `memory_write` — all route `memory_tools.py:352 → UserLayer.write`).

- **Schema** (`memory.py`): `MemoryUser.dedup_key VARCHAR(32)` (nullable) + `UniqueConstraint("tenant_id","user_id","dedup_key", name="uq_memory_user_dedup")`.
- **Migration 0032**: add column → backfill `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` → delete pre-existing dups (row_number keep highest-confidence/newest per group) → add the unique constraint (dups deleted BEFORE the constraint).
- **write()** (`user_layer.py`): `_dedup_key(content) = md5(re.sub(r"\s+"," ",content).strip().lower())` (matches the backfill byte-for-byte) → `pg_insert(MemoryUser).values(..., dedup_key=key, ...).on_conflict_do_update(constraint="uq_memory_user_dedup", set_={content, confidence=greatest, expires_at, updated_at=now()}).returning(MemoryUser.id).scalar_one()`. On conflict: KEEP the first writer's `source` + `metadata` (a later auto_extract does not relabel a manual fact), take the GREATEST confidence, refresh content/expires_at, bump updated_at. `_record_memory_op` still emits (append-only history). Own-session, atomic statement — no SAVEPOINT.
- Dedup is **exact-normalized** (case/whitespace) only; semantic near-dup stays CARRY-026.

PR: feature/sprint-57-150-memory-upsert-dedup (base `main` 7460f23b).

## Verification
- 6 real-Postgres integration tests (`test_user_layer_dedup.py`): same fact ×2 → 1 row + conf=max + content=latest + 2 op rows; lower-conf repeat keeps greatest; distinct facts → 2 rows; per-tenant (same content, 2 tenants → 1 each); long_term no-expiry + short_term 24h.
- Adapted unit tests (`test_user_layer.py` write tests → upsert shape; +3 `_dedup_key` tests; `test_ops_emit.py` add→execute).
- Migration `up → down → up` clean.
- **Drive-through PASS** (real chat-v2 + real Azure gpt-5.2, dan@acme.com): send 1 `memory_write` (conf 0.6, source none) + auto_extract (conf 0.99) of the SAME verbatim fact → **1 row** (key dd16b505, conf=greatest=0.99, updated bumped 07:08:54→07:09:01, source kept = first writer); send 2 same fact → **STILL 1 row** (updated bumped again 07:10:14); new-session recall surfaces it ONCE cleanly. Pre-57.150 = 2-4 rows. Screenshots in `sprint-57-150/artifacts/`.
- Gates: mypy `src` 0/393 · run_all 11/11 · pytest 3022 passed/6skip (3013 +9) · black/isort/flake8 clean · FE untouched.

## Impact
Backend-only. NO new wire event (stays 26), NO frontend, NO new cross-category contract. Migration 0032 (additive column + backfill + dedup existing + unique constraint; downgrade drops constraint + column). Per-request rollback: none needed (the upsert is byte-compatible — a single distinct write still inserts one row). Full revert: revert the 6 src/test edits + the migration. Closes `AD-Memory-User-Upsert-By-Key`.
