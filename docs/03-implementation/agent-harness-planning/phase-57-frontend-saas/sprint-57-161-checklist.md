# Sprint 57.161 — Checklist (structural compactor real token re-count)

[Plan](./sprint-57-161-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `204c4499`)
- [x] **Prong 1 — path verify**: 4 EDIT targets exist; `CHANGE-128` free; design note `63` free
- [x] **Prong 2 — content verify** (drift → progress.md; all GREEN, 0 drift):
  - [x] **D-structural-ctor-shape** — `structural.py:107-124` keyword-only ctor, `masker` last (additive `token_counter` safe)
  - [x] **D-preclear-realcount-pattern** — `preclear.py:178-181` real-count shape + `count(*, messages, tools)` keyword-only (`_abc.py:43-49`)
  - [x] **D-loop-consumes-tokens-after** — `loop.py:2282` `tokens_used = tokens_after` (no re-count → fix reaches loop budget; `structural.py:192` comment STALE)
  - [x] **D-factory-counter-available** — `TiktokenCounter` imported (`_category_factories.py:65`) + used (244/295) → injection is one line
  - [x] **D-structural-test-counter-absent** — 6 existing tests all `StructuralCompactor()` w/o counter (60/79/97/115/139/157) → legacy path byte-identical
- [x] **Prong 3 — schema verify**: N/A (no DB tables / migrations / ORM columns)
- [x] **D-baselines** — pytest 3202+6skip · wire 26 · Vitest 927 · mockup 51 · mypy `src` 400 · run_all 11/11 (carried from 57.160; branch = 57.160-merged main)
- [x] **Catalog drift** — progress.md Day-0 table (5 D-items, all GREEN)
- [x] **Go/no-go** — PROCEED (0 drift, scope-shift ~0%)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-161-compaction-structural-realcount` (from `main` `204c4499`)

---

## Day 1 — Real re-count branch + default-on wiring + docstring (US-1, US-2, US-3)

### 1.1 `StructuralCompactor` real-count branch
- [x] **`token_counter: TokenCounter | None = None` ctor param** (last keyword-only) + `self.token_counter` + `TokenCounter` import from `token_counter._abc`
  - DoD ✅: injected → real re-count (mirror `preclear.py:178-181`); None → verbatim message-count ratio; `messages_compacted` UNCHANGED
  - Verify: 9 structural tests pass

### 1.2 Default-on factory injection
- [x] **`make_chat_compactor` injects `TiktokenCounter(model="gpt-4o")` into `StructuralCompactor`**
  - DoD ✅: applies to bare-hybrid + preclear-chained paths; NO new env lever; MHist added
  - Verify: 33 factory tests pass

### 1.3 Stale-docstring + class-docstring fix
- [x] **Fixed `structural.py:192` comment** (loop trusts `tokens_after`, does NOT re-count) + class docstring point 6 (real-count-when-injected) + MHist
  - DoD ✅: no false "Loop.run() will re-count" claim; Karpathy §3 stale-docstring closed

### 1.4 Tests
- [x] **structural real-count tests** — real-count-on-tombstone reduction / `None` legacy byte-identical no-op / preclear parity (AC-1/2/3) — +3
- [x] **factory test** — `TiktokenCounter` injected into structural (AC-4) — +1

### 1.x Partial gate
- [x] black/isort/flake8/mypy clean on touched files (fixed 1 E501 in factory MHist)

---

## Day 2 — Full gate + evidence

### 2.1 Deterministic evidence
- [x] **Confirmed the fix delta** — `test_realcount_on_tombstone_reflects_reduction` (counter → `tokens_after < tokens_before`) vs `test_no_counter_is_message_count_ratio_blind_to_tombstone` (no counter → `N→N`) on the SAME tombstoned transcript = the 57.160-Leg-1/2-vs-fixed contrast at unit level; `test_realcount_matches_preclear_reduction` proves parity

### 2.x Full gate
- [x] mypy `src` 400 · run_all 11/11 · backend pytest **3206 + 6 skipped** (baseline 3202 +4) · Vitest 927 (FE untouched, 0 FE files) · mockup 51 (unchanged) · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM (MANDATORY)

### 3.1 Clean restart (Risk Class E)
- [ ] Kill stale/orphan backends (`Win32_Process` PID/PPID/StartTime sweep); confirm `:8000` free + sole owner; start single no-`--reload` backend with env-before-start (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING=1` + low `CHAT_COMPACTION_TOKEN_BUDGET`, **NO `CHAT_COMPACTION_PRECLEAR_RATIO`**) + startup-log confirmed

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [ ] Real chat-v2 (`/chat-v2`, real_llm) + Azure gpt-5.2, dev-login jamie@acme.com: reuse 57.160 Leg-3 staging (multi-tool single user turn, e.g. 6× knowledge_search) but **preclear OFF**
- [ ] **THE fix (real UI)**: the 57.159 `CompactionMarker` renders a **REAL `before→after` reduction** WITHOUT preclear — vs 57.160 Leg-1/2's recorded `N→N`; context bounded (loop budget relieved)
- [ ] Context retention: key facts survive compaction (honest note if run ends in unrelated HITL)
- [ ] Screenshot `artifacts/sprint-57-161-structural-realcount-marker.png` + observed-vs-intended (+ compare to 57.160 Leg-1/2) → progress.md Day 3

---

## Day 4 — CHANGE-128 + closeout

### 4.1 CHANGE-128 + design note
- [ ] **`CHANGE-128-structural-compactor-real-token-count.md`** (gap + fix + drive-through PASS + AD closed + loop-budget-tracking consequence)
- [ ] **Design note `63-structural-realcount-design.md`** (spike — 8-point gate all ✅; documents the loop-consumes-`tokens_after` runtime invariant + the message-count-ratio→real-count fix + parity with preclear)

### 4.2 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (`compaction-structural-realcount-spike` 0.60, 1st pt; flag if ratio out of band → re-point)
- [ ] Final gate sweep: mypy · run_all · pytest · Vitest · mockup · lint · LLM-SDK-leak
- [ ] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Compaction-Structural-RealTokenCount`) · sprint-workflow matrix (new `compaction-structural-realcount-spike` 0.60 row)
- [ ] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
