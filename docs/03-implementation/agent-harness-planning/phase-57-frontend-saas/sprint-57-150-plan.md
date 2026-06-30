# Sprint 57.150 Plan — memory user-layer write-side dedup (upsert-by-key)

**Summary**: Closes `AD-Memory-User-Upsert-By-Key` — `UserLayer.write()` today always `INSERT`s a fresh row, so the same durable fact accumulates duplicate rows; 57.149 made this worse by running an auto-extractor after EVERY send, and the dup rows dilute the 57.148 `profile()` top-k (the always-on identity inject). This sprint makes the write side idempotent: a normalized `dedup_key = md5(normalize(content))` column + a `(tenant_id, user_id, dedup_key)` unique constraint + a `pg_insert … on_conflict_do_update` so a repeat of the same fact UPDATEs (greatest confidence / bump `updated_at`) instead of inserting a second row. ALL three writers (the 57.148 nudge `memory_write` tool, the 57.149 `auto_extract` BackgroundTask, and any agent `memory_write`) route through `UserLayer.write`, so they all dedup at one chokepoint. Backend-only; needs migration **0032** (add column + backfill + dedup existing rows + unique constraint). Dedup is EXACT-normalized (case / whitespace), NOT semantic — cross-send exact re-emits are the target (semantic near-dup is CARRY-026). **Drive-through MANDATORY** (the effect is on the chat memory-formation path). NOT a spike design-note sprint (a focused correctness fix on an existing path, no new cross-category contract).

**Status**: Approved-to-execute (user picked "Upsert-By-Key (推薦)" via AskUserQuestion 2026-06-30, from the memory-arc carryover list)
**Branch**: `feature/sprint-57-150-memory-upsert-dedup`
**Base**: `main` HEAD `7460f23b` (Sprint 57.149 flip PR #353 merged — docs-only over feature `02ca23ba`)
**Slice**: closes `AD-Memory-User-Upsert-By-Key`; memory-formation arc follow-on (Slice 1 = 57.148 identity inject, Slice 2 = 57.149 auto-extract, this = the dedup that keeps both clean)
**Scope decisions**: (a) DB-level atomic upsert (unique constraint + ON CONFLICT) over an app-level SELECT-then-INSERT — atomic, race-free, mirrors 4 existing `on_conflict_do_update` sites; (b) key = `md5(normalize(content))` in a real `dedup_key` column (bounded 32 chars, indexable) over a unique index on the raw `content` Text (btree size limit) or an expression index (awkward ON CONFLICT target); (c) on conflict KEEP the first writer's `source` + `metadata` (don't relabel a manual fact as auto_extract), UPDATE only `content` (latest phrasing) / `confidence` (greatest) / `expires_at` (latest) / `updated_at`; (d) dedup is exact-normalized only — semantic near-dup stays CARRY-026.

---

## 0. Background

### The gap (`AD-Memory-User-Upsert-By-Key`)

`UserLayer.write()` (`user_layer.py:144-157`) always builds a fresh `uuid4()` row and `session.add`s it — there is NO dedup. Every call INSERTs. The 57.149 design note explicitly deferred this as `AD-Memory-User-Upsert-By-Key` ("MVP tolerates dup rows; `profile()` top-k by confidence").

### Why it matters (the missing capability)

57.149 wired an `auto_extract` MemoryExtractor to run after EVERY real_llm send. When a conversation hasn't changed, the extractor re-emits the SAME fact (the prompt-level "only NEW facts" dedup relies on the LLM choosing not to repeat — not guaranteed). Each repeat = a new row. `profile()` (`retrieval.py:127-163`) returns the user's durable facts confidence-ordered, capped at `top_k=5`; if "Chris is handling Project Aurora" sits in 5 near-identical rows it fills all 5 slots and crowds out the user's other facts. The always-on identity inject (57.148) then surfaces a degraded, repetitive profile. The dup count grows every send → the problem compounds.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `7460f23b`) | Anchor |
|-------|--------------------------------------|--------|
| write path | always `uuid4()` + `session.add(MemoryUser(...))` → pure INSERT | `user_layer.py:144-157` |
| table | 3 indexes, **NO unique constraint** on any (tenant,user,content) combo | `memory.py:256-264` |
| `updated_at` | `server_default=func.now()` but **no `onupdate`** → never bumped today | `memory.py:252-254` |
| profile dilution | top_k=5 confidence-desc over user long_term rows → dups fill slots | `retrieval.py:127-163` |
| all writers route here | `memory_write` tool → `layer.write(...)` (one chokepoint) | `memory_tools.py:352` |
| upsert precedent | 4 `pg_insert(...).on_conflict_do_update(constraint=...)` sites | `todo_store.py:118-130` (cleanest, 57.140) |

→ The fix adds a normalized dedup key + a unique constraint so `write()` becomes an idempotent upsert; one chokepoint means all three writers benefit; a migration must dedup EXISTING rows before the constraint can be added.

### The design (backend-only: 1 ORM column + 1 constraint + 1 migration + write() ON CONFLICT + helper + tests)

```
# user_layer.py
def _dedup_key(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content).strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()   # 32 hex chars

async def write(...):
    key = _dedup_key(content)
    stmt = (pg_insert(MemoryUser).values(id=uuid4(), ..., dedup_key=key, ...)
        .on_conflict_do_update(
            constraint="uq_memory_user_dedup",
            set_={"content": excluded.content,
                  "confidence": func.greatest(MemoryUser.confidence, excluded.confidence),
                  "expires_at": excluded.expires_at,
                  "updated_at": func.now()})       # source / metadata NOT updated → first writer wins
        .returning(MemoryUser.id))
    row_id = (await session.execute(stmt)).scalar_one()   # new id on insert, existing id on conflict
    _record_memory_op(session, ...)                        # still emit WRITE op (append-only history)
    await session.commit()
    return row_id

# memory.py: + dedup_key column + UniqueConstraint("tenant_id","user_id","dedup_key", name="uq_memory_user_dedup")
# migration 0032: add col → backfill md5(lower(btrim(regexp_replace(content,'\s+',' ','g')))) → dedup existing → add constraint
```

WHY DB-upsert over app-level SELECT-then-INSERT: atomic (no SELECT→INSERT race), single statement, and the codebase already has 4 `on_conflict_do_update` sites to mirror. WHY a `dedup_key` column over a unique index on raw `content`: a btree index entry must be < ~2704 bytes; a long extracted fact could exceed it — a 32-char md5 is bounded and indexable.

### Ground truth (recon head-start — code read on `main` HEAD `7460f23b`; ALL re-verified §checklist 0.1)

- `user_layer.py:107-172` — `write()` signature already has `source` (57.149); only the body INSERT changes.
- `memory.py:230` — `MemoryUser.source` exists; `:252` `updated_at` no `onupdate`; `:256-264` `__table_args__` = 3 Index, no UniqueConstraint.
- `todo_store.py:118-130` — `pg_insert(...).values(...).on_conflict_do_update(constraint="uq_...", set_={...})` pattern.
- `0031_session_todos.py` — latest migration; next = **0032**. RLS already on `memory_user` (0009) — migration adds NO RLS.
- `memory_tools.py:352` — the `memory_write` tool calls `layer.write(...)` → covered.
- `func.greatest` in PG ignores NULLs (NULL confidence handled gracefully).

**Baselines (57.149 closeout)**: pytest 3013 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-rowcount-tests** — grep `test_extraction_worker.py:100 assert len(new_ids)==2` + `test_memory_ops_rls.py:177` count → confirm they write DIFFERENT content (→ different dedup_key → still N rows, unaffected); if any writes the SAME content N times expecting N rows it tests the OLD behavior and must adapt.
- **D-write-unit-tests** — `test_user_layer.py` `test_write_*` assert `session.add(MemoryUser)`; ON CONFLICT shifts to `session.execute(pg_insert…returning)` → unit mock + assertions must adapt (relocate the long_term/short_term expires coverage to the real-DB integration test, don't delete).
- **D-greatest-numeric** — confirm `func.greatest(Numeric, Numeric)` compiles + the `.returning(MemoryUser.id).scalar_one()` shape against the mock factory (needs `scalar_one` configured).
- **D-migration-backfill-regex** — verify PG `regexp_replace(content,'\s+',' ','g')` + `btrim` + `lower` + `md5` matches the Python `_dedup_key` normalization byte-for-byte (same hash) so live writes hit the backfilled keys.

## 1. Sprint Goal

Make `UserLayer.write()` an idempotent upsert keyed on a normalized fact hash so a repeated durable fact UPDATEs one row instead of accumulating duplicates, keeping the 57.148 `profile()` top-k clean. PROVEN by: gates (mypy/pytest/lint/v2-lints/migration up+down) + a new dedup integration test + a MANDATORY drive-through (real chat-v2 + real Azure LLM: send the same fact across two sends → exactly ONE `memory_user` row, `confidence` = max, `updated_at` bumped; vs. the pre-57.150 2+ rows; `profile()` recall shows the fact once). Produces CHANGE-117. NO design note (focused correctness fix, no new cross-category contract).

## 2. User Stories

- **US-1** (write-side dedup): 作為平台，我希望同一筆 durable user fact 重複寫入時 UPDATE 既有 row 而非新增，以便 `profile()` top-k 不被重複事實稀釋。
- **US-2** (schema): 作為平台，我希望 `memory_user` 有 `(tenant_id, user_id, dedup_key)` unique 約束且既有重複 row 已清理，以便 upsert 有合法的 conflict target。
- **US-3** (provenance + lifetime on conflict): 作為平台，我希望 conflict 時保留首位 writer 的 `source`/`metadata`、取 `confidence` 最大值、刷新 `updated_at`，以便去重不損失 provenance 也反映最新可信度。
- **US-4** (drive-through MANDATORY): 作為開發者，我希望在真 chat-v2 + 真 LLM 上實證跨 send 重複事實只留一 row（非 gate-only），以便確認去重在主流量真的生效。
- **US-5** (closeout): CHANGE-117 + retrospective + navigators + AD 關閉。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; 1 migration; NO frontend / NO wire event / NO new ABC)

```
EDIT  backend/src/infrastructure/db/models/memory.py        — + dedup_key column + UniqueConstraint
NEW   backend/src/infrastructure/db/migrations/versions/0032_memory_user_dedup_key.py
EDIT  backend/src/agent_harness/memory/layers/user_layer.py — _dedup_key() helper + write() → pg_insert ON CONFLICT
EDIT  backend/tests/unit/agent_harness/memory/test_user_layer.py     — adapt write() unit tests to ON CONFLICT shape + _dedup_key tests
NEW   backend/tests/integration/memory/test_user_layer_dedup.py      — real-DB: same fact ×2 → 1 row; diff facts → 2 rows; confidence=max
UNTOUCHED  retrieval.py / extraction.py / handler.py / router.py     — profile()/extractor/chat unchanged (they call write(), benefit for free)
```

### 3.1 ORM (US-2) — `memory.py`

- Add `dedup_key: Mapped[str | None] = mapped_column(String(32), nullable=True, doc="md5(normalize(content)) for write-side dedup")` after `source` fields.
- Add `UniqueConstraint("tenant_id", "user_id", "dedup_key", name="uq_memory_user_dedup")` to `__table_args__` (alongside the 3 existing Index). Nullable key → PG allows multiple NULLs (rows that never set it don't conflict); `write()` always sets it.

### 3.2 Migration 0032 (US-2) — `0032_memory_user_dedup_key.py`

- `revises = "0031_session_todos"`.
- upgrade: (1) `op.add_column("memory_user", sa.Column("dedup_key", sa.String(32), nullable=True))`; (2) backfill `UPDATE memory_user SET dedup_key = md5(lower(btrim(regexp_replace(content, '\s+', ' ', 'g'))))`; (3) dedup existing rows — keep best per group:
  ```sql
  DELETE FROM memory_user WHERE id IN (
    SELECT id FROM (
      SELECT id, row_number() OVER (
        PARTITION BY tenant_id, user_id, dedup_key
        ORDER BY confidence DESC NULLS LAST, created_at DESC
      ) rn FROM memory_user WHERE dedup_key IS NOT NULL
    ) s WHERE rn > 1)
  ```
  (4) `op.create_unique_constraint("uq_memory_user_dedup", "memory_user", ["tenant_id","user_id","dedup_key"])`.
- downgrade: drop constraint → drop column. NO RLS change (memory_user RLS from 0009).
- Backfill regex MUST match `_dedup_key` Python normalization byte-for-byte (D-migration-backfill-regex).

### 3.3 write() upsert + helper (US-1, US-3) — `user_layer.py`

- `_dedup_key(content)` module helper: `re.sub(r"\s+", " ", content).strip().lower()` → `hashlib.md5(...).hexdigest()`.
- `write()` body: replace `session.add(MemoryUser(...))` with `pg_insert(MemoryUser).values(..., dedup_key=key, ...).on_conflict_do_update(constraint="uq_memory_user_dedup", set_={content, confidence=greatest, expires_at, updated_at=now()}).returning(MemoryUser.id)`; `row_id = (await session.execute(stmt)).scalar_one()`.
- KEEP `_record_memory_op(...)` emit (append-only history; a re-affirm is still a WRITE op). KEEP own-session (no SAVEPOINT — write() owns its session, atomic statement). Signature + return type UNCHANGED.

### 3.4 What is explicitly NOT done

- Semantic / near-dup dedup ("Chris works on Aurora" vs "Chris is handling Project Aurora") — needs embeddings → CARRY-026.
- `memory_ops` op-emit dedup on a no-change re-affirm — the ops log is append-only history by design and `profile()` reads `memory_user` not `memory_ops`, so it doesn't affect the dilution this sprint fixes → §9 / future.
- `tenant`/`role`/`session` layer dedup — this sprint is user layer only (where auto_extract writes); other layers keep INSERT.

### 3.5 Validation (US-1..US-5)

Gates: mypy `src` 0/392 · run_all 11/11 · pytest 3013 + new · Vitest 922 (untouched) · mockup 51 (untouched) · `npm run lint && npm run build` N/A (FE untouched) · black/isort/flake8 clean · LLM-SDK-leak clean · migration up→down→up clean. Plus the §US-4 drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/infrastructure/db/models/memory.py` | EDIT (dedup_key column + UniqueConstraint) |
| 2 | `backend/src/infrastructure/db/migrations/versions/0032_memory_user_dedup_key.py` | NEW |
| 3 | `backend/src/agent_harness/memory/layers/user_layer.py` | EDIT (_dedup_key + write() ON CONFLICT) |
| 4 | `backend/tests/unit/agent_harness/memory/test_user_layer.py` | EDIT (adapt write() tests + _dedup_key tests) |
| 5 | `backend/tests/integration/memory/test_user_layer_dedup.py` | NEW |
| 6 | `claudedocs/4-changes/feature-changes/CHANGE-117-memory-user-upsert-dedup.md` | NEW |
| — | `retrieval.py` / `extraction.py` / `api/v1/chat/*` / frontend | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `UserLayer.write()` of the same normalized content twice → ONE `memory_user` row (existing id returned), `confidence` = max(old,new), `updated_at` bumped; two DIFFERENT facts → 2 rows.
2. Migration 0032 up: backfills `dedup_key`, deletes pre-existing dup rows (keeping highest-confidence/newest), adds `uq_memory_user_dedup`; down: drops constraint + column; up→down→up clean.
3. All 3 writers (57.148 nudge tool / 57.149 auto_extract / agent `memory_write`) dedup through the one chokepoint; `source`/`metadata` of the first writer preserved on conflict.
4. `profile()` returns each distinct fact once (no dup-filled top-k). Existing memory/extraction tests green (row-count tests confirmed write DIFFERENT content).
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — dan repeats a fact across two sends → DB shows exactly ONE `auto_extract` row for it (not 2+), `confidence` max + `updated_at` bumped; `profile()` recall surfaces it once; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Memory-User-Upsert-By-Key` CLOSED; CHANGE-117; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `_dedup_key` helper + `write()` ON CONFLICT upsert
- [ ] US-2 `dedup_key` column + unique constraint + migration 0032 (backfill + dedup existing)
- [ ] US-3 conflict resolution (greatest confidence / keep first source / bump updated_at)
- [ ] US-4 drive-through PASS (real chat-v2 + Azure; DB row-count evidence)
- [ ] US-5 CHANGE-117 + retrospective + navigators + AD closed

## 7. Workload Calibration

- Scope class **NEW `memory-upsert-dedup-spike` 0.60** (a focused Cat-3 write-path correctness fix WITH a real migration — add column + backfill + dedup-existing SQL + unique constraint + ON CONFLICT rewrite + a normalization helper + a unit-test refactor + a real-DB integration test + drive-through. A real-code core ≥ ~3 hr holds the 0.60 spike multiplier per the 57.137 lesson — NOT a tiny-code-wrapped-in-ceremony 0.85 sprint. Kin: `transcript-retention-apply-spike` 0.60 (a bounded backend spike with a destructive DB op) + the memory-formation-* spikes 0.60. KEEP pending 2-3 sprint validation).
- **Agent-delegated: no** (parent-direct — a correctness fix touching a migration + a load-bearing write path + a test refactor; the migration dedup SQL + the ON CONFLICT shape want direct authorship). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~7.3 hr (migration ~1.5 + ORM ~0.3 + write()+helper ~1 + test refactor ~1.5 + drive-through ~1.5 + docs/closeout ~1.5) → class-calibrated commit ~4.4 hr (mult 0.60). Day-4 retro Q2 verifies (1st `memory-upsert-dedup-spike` data point).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Existing dup rows block adding the unique constraint | migration deletes dups (row_number keep-best) BEFORE `create_unique_constraint` (step ordering in §3.2) |
| Migration backfill regex ≠ Python `_dedup_key` → live writes miss backfilled keys | D-migration-backfill-regex: align `md5(lower(btrim(regexp_replace(content,'\s+',' ','g'))))` to `re.sub(r"\s+"," ",content).strip().lower()`; integration test writes a backfilled-style fact then a live repeat → asserts 1 row |
| `test_user_layer.py` write() unit tests assert `session.add(MemoryUser)` | D-write-unit-tests: adapt to `session.execute(pg_insert…returning)` shape; RELOCATE long_term/short_term expires coverage to the real-DB integration test (don't delete — Never Delete Tests) |
| Row-count tests assert N rows after same-content writes | D-rowcount-tests Day-0 Prong 2: confirm they write DIFFERENT content (→ unaffected); adapt only if they tested old INSERT-always behavior |
| Module-level singleton / event-loop test isolation (Risk Class C) | new integration test uses the standard committed-seed + per-tenant RLS fixture (mirror `test_extraction_worker.py`) |
| Stale `--reload` backend masks the migration/write change at drive-through (Risk Class E) | clean restart: kill stale reloader + spawn-workers, confirm sole port owner + `alembic upgrade head` applied, then drive |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Semantic / near-dup dedup → CARRY-026 (Qdrant memory axis).
- `memory_ops` op-emit dedup on no-change re-affirm → future (append-only history, doesn't dilute `profile()`).
- tenant / role / session layer dedup → future (auto_extract writes user layer only).
- Cross-session CONVERSATION recall + session-summary → `AD-Memory-Formation-Session-Recall` (缺口 2).
- In-loop judge memory-blindness → `AD-Verification-Judge-Memory-Inject-Blind`.
