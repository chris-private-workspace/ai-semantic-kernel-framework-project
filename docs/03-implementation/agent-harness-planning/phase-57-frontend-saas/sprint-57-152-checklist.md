# Sprint 57.152 — Checklist (combine post-send extract + summarize into one LLM call)

[Plan](./sprint-57-152-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `a6e8d586`)
- [x] **Prong 1 — path verify**: `formation.py` + `test_formation.py` free (NEW); all EDIT targets present; `CHANGE-119` + design note `55` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-write-facts-session-id** — `session_id` unused in the extract write loop (so `write_facts` need not take it)
  - [x] **D-ctx-field-rename** — `ctx.extractor`/`ctx.summarizer`/`ChatMemoryExtractContext(` sites mapped (router.py + 2 test files)
  - [x] **D-allowlist-formation** — `extraction.py` + `session_summarizer.py` in ALLOWLIST_PATTERNS (add `formation.py`)
  - [x] **D-profile-gate** — `_maybe_auto_extract` profile() gated on `extractor is not None and user_id is not None` (→ `former.wants_user_facts`)
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column change)
- [x] **D-baselines** — pytest 3042 · wire 26 · Vitest 922 · mockup 51 · mypy 0/396 · run_all 11/11
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — scope-shift ~0% → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-152-memory-combined-formation` (from `main` `a6e8d586`)

---

## Day 1 — Worker + dispatch extraction (US-1/US-2/US-3)

### 1.1 Extract dispatch halves (behavior-preserving)
- [x] **`MemoryExtractor.write_facts(...)`** — write loop verbatim; `extract_session_to_user` refactored to call it (test_extraction green untouched)
- [x] **`SessionSummarizer.store_summary(...)`** — guard + upsert verbatim; `summarize_and_store` refactored to call it (test_session_summarizer green untouched)

### 1.2 MemoryFormationWorker
- [x] **`agent_harness/memory/formation.py`** — worker + `wants_user_facts` + `form` + `_form_combined` (1 call) + `_form_separate` (fallback) + own combined parse/render helpers
- [x] **`memory/__init__.py`** — export `MemoryFormationWorker`

### 1.3 Config flag + AP-8 allowlist
- [x] **`chat_memory_combined_formation: bool = True`** (env `CHAT_MEMORY_COMBINED_FORMATION`)
- [x] **allowlist `agent_harness/memory/formation.py`** (rationale comment) → AP-8 0 violations

### 1.4 Worker unit tests
- [x] **`test_formation.py`** (10): combined 1-call writes both · `combined=False` → 2 delegate calls · only-extract · only-summary · no-user-skips-facts · empty/no-collaborator no-op · `_build_prompt` · `_parse_combined`

### 1.x partial gate
- [x] `black . && isort . && flake8 . && mypy src` clean

---

## Day 2 — Rewiring + test updates (US-4)

### 2.1 handler.py rewiring
- [x] **`ChatMemoryExtractContext`** → `{former}`; `build_chat_memory_extractor` builds the worker (`combined=settings.chat_memory_combined_formation`), None when both feature flags off

### 2.2 router.py rewiring
- [x] **`_maybe_auto_extract`** → load ledger once; profile() gated on `former.wants_user_facts`; ONE `await former.form(...)`

### 2.3 test updates
- [x] **`test_memory_auto_extract.py`** — `_StubFormer` (records `form()` + `wants_user_facts`); assertions → former.form
- [x] **`test_handler.py`** — cheap-tier assertion → `ctx.former._chat_client`

### 2.x Full gate
- [x] mypy `src` 0/397 · run_all 11/11 (AP-8 formation.py allowlisted) · backend pytest 3053/6skip (+11) · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-5) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale 57.151 PID 61048; fresh 57.152 backend PID 47908 sole :8000 owner; frontend vite :3007 untouched; DB head 0033

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] Real chat-v2 + real Azure (dan@acme.com): one send with a durable fact + substantive conversation
- [x] **THE fix (DB inspector)**: ONE combined call wrote BOTH a `memory_session_summary` row AND `memory_user [auto_extract]` rows at the SAME `15:20:30` timestamp = one call (unit test call-count==1); 57.150 dedup coexists. Leg-2 recall: both halves trace-injected into the new session; final-answer hit 2 pre-existing carryovers (NOT 57.152 regressions)
- [x] Screenshots + DB evidence → progress.md Day 3 + artifacts/

---

## Day 4 — CHANGE-119 + closeout

### 4.1 CHANGE-119 + design note 55
- [x] **`CHANGE-119-memory-combined-formation.md`**
- [x] **`55-memory-combined-formation-design.md`** (8-point gate; amends 53+54)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (NEW `memory-formation-combine-spike` 0.60, 1st pt ~1.0 IN band)
- [x] Final gate sweep: mypy 0/397 · run_all 11/11 · pytest 3053/6skip · LLM-SDK-leak clean (no Vitest/mockup delta — backend-only)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE the AD + add `AD-Memory-Combined-Formation-AB-Quality`) · sprint-workflow matrix
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11
- [ ] **Commit (local done)** → ⏳ PR push + open → CI → merge: **PENDING USER CONFIRMATION** (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
