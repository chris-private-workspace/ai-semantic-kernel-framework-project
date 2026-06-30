# Sprint 57.150 — Checklist (memory user-layer write-side dedup / upsert-by-key)

[Plan](./sprint-57-150-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `7460f23b`)
- [x] **Prong 1 — path verify**: EDIT targets exist — `memory.py`, `user_layer.py`, `test_user_layer.py`; NEW free — `0032_memory_user_dedup_key.py`, `test_user_layer_dedup.py`, `CHANGE-117-*.md`; migration 0031 is the latest (→ 0032 next)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-rowcount-tests** — `test_extraction_worker.py:100` writes 2 DIFFERENT facts via a MOCK layer (unaffected); `test_memory_ops_rls.py:142` real write of a SINGLE fact → still 1 row (needs 0032 in test DB) → both compatible
  - [x] **D-write-unit-tests** — confirmed `test_write_*` assert `session.add(MemoryUser)` + mock lacks `scalar_one` → adapt to `session.execute(pg_insert…returning).scalar_one()`; relocate expires coverage to integration (NOT delete)
  - [x] **D-greatest-numeric** — `func.greatest(Numeric, Numeric)` valid PG + ignores NULL; mock needs `scalar_one`
  - [x] **D-migration-backfill-regex** — Python `re.sub(r"\s+"," ",c).strip().lower()` ↔ SQL `lower(btrim(regexp_replace(c,'\s+',' ','g')))` same bytes → same md5 (ASCII); integration verifies collide
  - [x] **D-all-writers** — `extraction.py:75-77` + `memory_tools.py:352` both route `UserLayer.write` (one chokepoint) confirmed
- [x] **Prong 3 — schema verify**: `memory_user` (`memory.py:205-264`) `source`/`updated_at` present, `__table_args__` = 3 Index no UniqueConstraint; `UniqueConstraint` imported (`:65`); 0031 latest → 0032; RLS in 0009 (0032 NO RLS); `dedup_key` additive nullable
- [x] **D-baselines** — pytest 3013 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11 (recorded; re-verify Day 2 + Day 4)
- [x] **Catalog drift** — progress.md Day-0 table (5 D-IDs + finding + implication)
- [x] **Go/no-go** — scope-shift ~0% (additive column + write rewrite + bounded test refactor) → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-150-memory-upsert-dedup` (from `main` `7460f23b`)

---

## Day 1 — ORM + migration 0032 (US-2)

### 1.1 ORM column + constraint
- [x] **`MemoryUser.dedup_key` `String(32)` nullable + `UniqueConstraint("tenant_id","user_id","dedup_key", name="uq_memory_user_dedup")`** in `memory.py`
  - DoD: column additive (nullable); constraint in `__table_args__` alongside the 3 Index; mypy clean ✅
  - Verify: `mypy ... memory.py` ✅ Success

### 1.2 Migration 0032
- [x] **`0032_memory_user_dedup_key.py`**: add column → backfill md5(normalize) → dedup existing rows (row_number keep-best) → `create_unique_constraint`; downgrade drops constraint + column
  - DoD: upgrade order = add → backfill → dedup → constraint (dups deleted BEFORE constraint); backfill `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` matches `_dedup_key`; down reverses; NO RLS change
  - Verify: `alembic upgrade head` → `downgrade -1` → `upgrade head` clean ✅ (current = 0032 head)

### 1.x Partial gate
- [x] mypy clean (3 files) · migration up→down→up clean · black/isort/flake8 clean (2 E501 MHist fixed)

---

## Day 2 — write() upsert + tests (US-1, US-3) + full gate

### 2.1 `_dedup_key` helper + write() ON CONFLICT
- [x] **`_dedup_key(content)` module helper + `write()` → `pg_insert(MemoryUser)...on_conflict_do_update(constraint="uq_memory_user_dedup", set_={content, confidence=greatest, expires_at, updated_at=now()}).returning(MemoryUser.id)`**
  - DoD: same normalized content twice → 1 row (existing id returned); `source`/`metadata` first writer preserved; `confidence`=greatest; `updated_at`=now(); `_record_memory_op` still emits; own-session; signature UNCHANGED ✅
  - Verify: `pytest test_user_layer.py` ✅ 14 passed

### 2.2 Unit-test adaptation + `_dedup_key` tests
- [x] **Adapted `test_write_*` to ON CONFLICT shape (mock `scalar_one`; assert execute + MemoryOp + no MemoryUser-add); added 3 `_dedup_key` tests (whitespace/case → same hash; 32-hex; different → different). Also fixed `test_ops_emit.py::test_user_write_emits_write_op_same_session` (same add→execute shift)**
  - DoD: write() unit tests pass on new shape; expires coverage RELOCATED to §2.3 (not deleted); `_dedup_key` idempotence + discrimination covered
  - Verify: `pytest test_user_layer.py test_ops_emit.py` ✅ 14 + 8 passed

### 2.3 Dedup integration test (real DB)
- [x] **`test_user_layer_dedup.py`** (6 tests): same fact ×2 → 1 row + confidence=max(0.7,0.9)=0.9 + content=latest + 2 op rows; lower-conf repeat keeps greatest; 2 different facts → 2 rows; per-tenant (same content, 2 tenants → 1 each); long_term no-expiry + short_term 24h (relocated from unit)
  - DoD: real Postgres (commit→flush shared-session, Risk Class C); asserts row count / confidence / content / expiry / per-tenant isolation
  - Verify: `pytest tests/integration/memory/test_user_layer_dedup.py` ✅ 6 passed

### 2.4 Full gate
- [x] mypy `src` 0/393 (392 + migration) · run_all 11/11 (incl. LLM-SDK-leak + rls_policies) · backend pytest 3022 passed/6skip (3013 +9) · Vitest 922 (untouched) · mockup 51 (untouched) · black/isort/flake8 clean (6 files) · migration up→down→up clean · FE untouched

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale port-8000 backend (PID 22760, pre-57.150 code) + dead 57.149 bg backend; port 8000 sole owner + 0 orphans; `alembic upgrade head` = 0032 (dedup_key backfilled on all 9 dan rows confirmed); fresh no-reload uvicorn on branch code (PID 43620, `CHAT_MEMORY_AUTO_EXTRACT` default ON); startup clean; node vite 3007 + claude-code UNTOUCHED

### 3.2 Drive-through (MANDATORY — NOT gate-only) — real Azure gpt-5.2 — ALL PASS
- [x] **Repeat-fact dedup (THE fix, real UI)**: send 1 agent `memory_write` "Project Helix DT150…" (conf 0.6, source none) + auto_extract re-extract (conf 0.99) → **1 row** key=dd16b505, conf=greatest=0.99, updated BUMPED (07:08:54→07:09:01), first-writer source preserved. Send 2 same fact → **STILL 1 row**, updated BUMPED again (07:10:14). Pre-57.150 = 2-4 rows. `scratchpad/dt150_db.py` (get_session_factory + set_config FORCE-RLS, dedup_key + created/updated)
- [x] **Distinct facts still kept**: integration test `test_distinct_facts_kept_separate` + per-tenant test cover this deterministically (exact-normalized, not over-collapsing); live drive focused on the dedup-fires path
- [x] **Clean recall**: NEW session → "What do you remember about Project Helix DT150?" → agent recalls ONCE cleanly via `profile()` inject ("built in Rust and ships in November 2027"), no dilution
- [x] Screenshots (`dt150-chat-dedup.png` + `dt150-clean-recall.png`) + observed-vs-intended → progress.md Day 3 + `artifacts/snapshot.md`

---

## Day 4 — CHANGE-117 + closeout

### 4.1 CHANGE-117
- [x] **`CHANGE-117-memory-user-upsert-dedup.md`** (gap: write always INSERTs → 57.149 dup bloat → profile dilution; fix: dedup_key + unique + ON CONFLICT; migration 0032; drive-through PASS; AD closed). NO design note (focused correctness fix, no new contract)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (NEW `memory-upsert-dedup-spike` 0.60, 1st pt ~1.07 IN band → KEEP; landed clean vs 57.149 over-run ∵ dedup fired on send 1)
- [x] Final gate sweep: = Day 2.4 (mypy 0/393 · run_all 11/11 · pytest 3022/6skip · migration up→down→up · black/isort/flake8 clean · FE untouched Vitest 922/mockup 51); Day 3-4 = drive-through + docs only, NO code change since
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Memory-User-Upsert-By-Key` + NEW `AD-Memory-Ops-Emit-Dedup-On-Reaffirm` + re-list memory-arc carryover) · sprint-workflow matrix (NEW `memory-upsert-dedup-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 all ✅/N/A; v2 lints 11/11 (incl. llm_sdk_leak + rls_policies)
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
