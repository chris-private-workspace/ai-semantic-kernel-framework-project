# Sprint 57.148 — Checklist (memory-formation Slice 1: user-identity write + always-on inject)

[Plan](./sprint-57-148-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `3d5a1360`)
- [x] **Prong 1 — path verify**: edit targets exist — `handler.py`, `memory/retrieval.py`, `prompt_builder/builder.py`, `memory/layers/user_layer.py`, the 3 test files; `CHANGE-115` + `52-memory-formation-identity-design.md` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-empty-query-guard** — `search()` has NO empty-query guard (`retrieval.py:67`); guard is in the builder → `profile()` uses `query=""` directly
  - [x] **D-write-upsert** — confirm `UserLayer.write` INSERTs (no upsert-by-key) → dup-row limitation noted
  - [x] **D-nudge-seam** — handler `system_prompt` → loop prepend (`loop.py:1970`); nudge rides the proven skills-catalog seam
  - [x] **D-tier2-cap** — `_apply_memory_budget` (`builder.py:257`) after inject → merge inserts before the cap
- [x] **Prong 3 — schema verify**: N/A — `memory_user` table + `UserLayer` already exist; NO migration this sprint (confirm no new column needed for identity facts)
- [x] **D-baselines** — pytest 2988 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11 (re-verify full Day 4)
- [x] **Catalog drift** — progress.md Day-0 table (D-IDs + finding + implication)
- [x] **Go/no-go** — scope-shift 0%; Risk A confirmed + Risk B GREEN → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-148-memory-formation-identity` (from `main` `3d5a1360`)

---

## Day 1 — Surfacing core: always-on user-profile (US-2)

### 1.1 `MemoryRetrieval.profile()`
- [x] **NEW `profile(tenant_id, user_id, top_k)` — wildcard user-scope long_term pull** (4 unit tests)
  - DoD: returns user-scope long_term hints regardless of query; tenant+user scoped; returns `[]` when user_id is None; does NOT route through the empty-query guard
  - Verify: `pytest backend/tests/.../test_memory_retrieval.py -k profile`

### 1.2 PromptBuilder always-on merge
- [x] **`DefaultPromptBuilder.build()` injects profile facts unconditionally** (4 unit tests; ctor `profile_top_k`)
  - DoD: profile hints merged into the `user` layer block even when the user message keyword-mismatches; dedup by `hint_id` vs query-gated hints; stays within the ≤2000-tok Tier2 cap; rendered under an "About this user" sub-heading
  - Verify: `pytest backend/tests/.../test_prompt_builder_memory.py -k profile`

### 1.3 Multi-tenant isolation test
- [x] **Profile pull never crosses tenant** (1 integration test; empty query still tenant-filtered)
  - DoD: tenant A profile() returns 0 tenant-B rows (mirrors `.claude/rules/multi-tenant-data.md` Case 1)
  - Verify: `pytest -k "profile and tenant"`

---

## Day 2 — Formation nudge (US-1) + full gate

### 2.1 Formation nudge in chat system prompt
- [x] **Append `MEMORY_FORMATION_NUDGE` at the system-prompt seam, gated on memory tools wired** (2 handler tests)
  - DoD: nudge present when memory tools wired; ABSENT for echo/no-memory path; instructs `memory_write(scope='user', time_scale='long_term')` for durable self-facts
  - Verify: `pytest backend/tests/.../test_chat_handler*.py -k nudge`

### 2.2 Full gate
- [x] mypy `src` 0/392 · run_all 11/11 · 42 affected tests pass (+11 new) · black/isort/flake8 clean (8 files) · LLM-SDK-leak clean · FE untouched (full pytest re-verify Day 4)

---

## Day 3 — Drive-through (US-3) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale python 54568, `:8000` free + no python orphans + node 31616 untouched; fresh reloader 46684 + worker 30056 on branch code; `/api/v1/health` 200; 57.147 test env shell-set not `.env` → clean default

### 3.2 Drive-through (MANDATORY — NOT gate-only) — ALL 3 LEGS PASS (real Azure gpt-5.2)
- [x] **S1 — formation**: jamie@acme.com (baseline 0 rows) → "我是 Chris…知識連接器…" → agent PROACTIVELY `memory_write(scope=user)` ×2 → DB `'User name is Chris.'` (0.90) + `'Chris is responsible for developing the Knowledge Connector feature…'` (0.85), both perm
- [x] **S2 — recall**: NEW session (same user_id) → "你知道我是誰嗎?" (0 keyword overlap) → **"你是 Chris。我也記得你目前負責…開發 Knowledge Connector"**; Inspector Memory 2 user-layer reads (trace `ddc56264…`) → proves always-on inject, NOT query-gated
- [x] **Negative/isolation**: priya@acme.com (different user_id) → same Q → "我不知道你是誰…沒有任何關於你的身份…的資訊"; `mentionsChris=false`
- [x] Screenshots `sprint-57-148-{s1-formation,s2-recall,s3-isolation-priya}.png` + observed-vs-intended → progress.md Day 3

---

## Day 4 — CHANGE-115 + closeout

### 4.1 CHANGE-115 + design note 52
- [x] **`CHANGE-115-memory-formation-identity.md`** (gap + fix + drive-through PASS + AD closed)
- [x] **`52-memory-formation-identity-design.md`** (spike — 8-point gate ALL ✅; §Open Invariants lists upsert-by-key + Option-B + cross-session as deferred)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`memory-formation-identity-spike` 0.60, 1st pt, ratio ~1.0-1.1 IN band → KEEP)
- [x] Final gate sweep: mypy `src` 0/392 · run_all 11/11 · pytest **2999** passed/6skip · black/isort/flake8 clean (9 files) · LLM-SDK-leak clean · FE untouched (Vitest 922 / mockup 51)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Memory-Formation-Identity` Slice 1 + log Option-B/upsert/session-recall/CARRY-026 open) · sprint-workflow matrix (`memory-formation-identity-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 all ✅/N/A; v2 lints 11/11
- [x] **Local commit done** → ⏳ PR push + open → CI → merge: **PENDING USER CONFIRMATION** (push is outward-facing) → post-merge status flip after gh-verified MERGED
