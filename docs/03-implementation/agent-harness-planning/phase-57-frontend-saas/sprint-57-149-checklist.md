# Sprint 57.149 — Checklist (memory Option-B deterministic post-send fact extraction)

[Plan](./sprint-57-149-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `694e0062`)
- [x] **Prong 1 — path verify**: edit targets exist — `_category_factories.py`, `extraction.py`, `user_layer.py`, `handler.py`, `router.py`, `core/config/__init__.py`, the 3 test files; `CHANGE-116` + `53-memory-auto-extract-design.md` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-msgstore-load** — `DBMessageStore.load() -> list[Message]` no params → FULL ledger; whole-ledger MVP (no cap Day-1), rely on prompt-level dedup
  - [x] **D-write-source** — `MemoryUser.source: Mapped[str \| None]` column ALREADY exists (`memory.py:230`) → `write(source=)` real column, NO migration
  - [x] **D-extractor-msg-type** — ledger + extractor both use `agent_harness._contracts.Message`, no adapter
  - [x] **D-handler-return** — return-tuple breaks ~12 callers → RESOLVED: self-contained `build_chat_memory_extractor(model_policy, db)` in `handler.py`, router calls separately (0 caller breakage)
  - [x] **D-cheap-tier** — `profile.cheap` + `memory_layers["user"]` both in `build_real_llm_handler` scope (`handler.py:352`/`:360`)
- [x] **Prong 3 — schema verify**: N/A — no new table / migration; `MemoryUser.source` pre-exists → additive write only, no DDL
- [x] **D-baselines** — pytest 2999 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11 (recorded; re-verify full Day 4)
- [x] **Catalog drift** — progress.md Day-0 table (5 D-IDs + finding + implication)
- [x] **Go/no-go** — scope-shift ~0% (D-handler-return refines factory location, change-set unchanged) → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-149-memory-auto-extract` (from `main` `694e0062`)

---

## Day 1 — Extractor wiring core (US-1)

### 1.1 Extractor factory
- [x] **`build_chat_memory_extractor(model_policy, db, session_id, tenant_id) -> ChatMemoryExtractContext | None`** in `handler.py` (D-handler-return: self-contained, NOT a `build_handler` tuple → 0 caller breakage)
  - DoD: returns a real context (extractor+retrieval+message_store) when env + db/session/tenant present; SOFT `None` otherwise (never raises)
  - Verify: `pytest tests/unit/api/v1/chat/test_handler.py -k memory_extractor` ✅ 3 passed

### 1.2 Build extractor + thread to router
- [x] **router builds the ctx (`profile.cheap` + `memory_layers["user"]`) gated on real_llm + flag; `_stream_loop_events` gains `memory_extract_ctx` param**
  - DoD: ctx reaches `_stream_loop_events`; `None` path = no-op; mypy clean
  - Verify: `mypy src/api/v1/chat/` ✅ clean

### 1.3 Post-completion extraction hook
- [x] **`_maybe_auto_extract` helper called after `natural_completion`: load ledger + profile → `extract_session_to_user(known_facts=...)`, best-effort try/except** (factored out for unit-testability)
  - DoD: runs only when ctx not None AND user_id present; an extractor exception is logged + swallowed (the SSE stream + send never fail); runs AFTER the answer streamed
  - Verify: `pytest tests/unit/api/v1/chat/test_memory_auto_extract.py` ✅ 5 passed (gate / known-facts / swallow)

---

## Day 2 — Dedup + env gate + source tag (US-2, US-3) + full gate

### 2.1 Prompt-level dedup
- [x] **`extract_session_to_user(..., known_facts: list[str] | None = None)` → `_build_known_block` "only NEW facts"** in `extraction.py`
  - DoD: non-empty `known_facts` appends the do-not-repeat block; empty/None/blank-only = 51.2 byte-identical prompt
  - Verify: `pytest tests/.../test_extraction.py -k "known_facts or known_block"` ✅

### 2.2 env gate + cheap tier + source tag
- [x] **`chat_memory_auto_extract: bool = True` (`CHAT_MEMORY_AUTO_EXTRACT`) + `UserLayer.write(..., source: str | None = None)` additive + extractor passes `source="auto_extract"`**
  - DoD: `=false` → router skips ctx → hook no-op (57.148 byte-identical); `write` default `source=None` keeps all callers; extractor rows persist `source="auto_extract"` (real column — D-write-source: pre-existed, no migration)
  - Verify: `pytest tests/.../test_extraction*.py -k source` ✅ + cheap-tier factory test ✅

### 2.3 Multi-tenant isolation test
- [x] **Extracted writes inherit originating tenant_id + user_id (never cross-tenant)**
  - DoD: the `test_extraction_worker` per-write tenant+user asserts + `test_tenant_isolation` extractor-pollution test stay green with the `source` param
  - Verify: `pytest tests/integration/memory/ -q` ✅ 89 passed

### 2.4 Full gate
- [x] mypy `src` **0/392** · v2 lints **25 passed** (incl. LLM-SDK-leak) · backend pytest **3013 passed/6skip** (2999 +14) · Vitest 922 (untouched) · mockup 51 (untouched) · black/isort/flake8 clean (7 src + 5 test) · FE untouched

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale main backend (reloader 46684 + worker 30056); port 8000 free + 0 python orphans; fresh no-reload uvicorn on branch code (`CHAT_MEMORY_AUTO_EXTRACT` default ON); health 200 + clean startup; node frontend (vite 3007) + claude-code UNTOUCHED

### 3.2 Drive-through (MANDATORY — NOT gate-only) — real Azure gpt-5.2 — ALL 3 LEGS PASS
- [x] **Extractor wrote it**: dan (baseline 3 `source=none`) states Project Aurora → DB `[auto_extract]` conf 0.99 'Chris is currently handling Project Aurora…' (cheap-tier extractor ran). NOTE: the 57.148 nudge ALSO fired (agent wrote a `source=none` row) — the `auto_extract` tag proves the extractor ran independently
- [x] **Recall**: NEW session (same dan), 0-keyword-overlap question → agent recalls "Project Aurora…Oracle→PostgreSQL…Q3"; Inspector `profile()` read the extractor row `memory_user:5d487f86`
- [x] **Isolation**: priya (different user) → "我不知道你是誰" (judge 0.99; 0 leak; per-user `WHERE user_id`)
- [x] **BackgroundTask evolution + re-drive**: moved extraction off the SSE generator → Starlette `BackgroundTask` (connection-close no longer blocked; GeneratorExit/OTel noise found PRE-EXISTING `tracer.py:200`); re-drive (priya, baseline 0) → `[auto_extract]` conf 0.78 SOC 2 row written after the response
- [x] Screenshots + observed-vs-intended → progress.md Day 3 + artifacts/

---

## Day 4 — CHANGE-116 + closeout

### 4.1 CHANGE-116 + design note 53
- [x] **`CHANGE-116-memory-auto-extract.md`** (gap + fix + drive-through PASS + AD closed)
- [x] **`53-memory-auto-extract-design.md`** (spike — 8-point gate ALL ✅; §Open Invariants: upsert-by-key + async queue + 缺口 2 + semantic axis + judge-memory-blind deferred)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`memory-formation-extract-spike` 0.60 → **re-pointed 0.85**; ratio ~1.3-1.4 OVER per 57.148 note; drive-through discovery loop = BackgroundTask re-arch + noise investigation + re-drive = variance driver)
- [x] Final gate sweep: mypy `src` 0/392 · v2 lints 25 · pytest 3013/6skip · black/isort/flake8 clean · FE untouched (Vitest 922 / mockup 51)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Memory-Formation-Auto-Extract` + re-list remaining memory-formation carryover) · sprint-workflow matrix (`memory-formation-extract-spike` 0.85 row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 all ✅/N/A; v2 lints 25/25
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
