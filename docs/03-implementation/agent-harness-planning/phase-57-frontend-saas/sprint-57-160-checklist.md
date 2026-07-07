# Sprint 57.160 — Checklist (tool-anchored observation masking + reduction/retention A/B)

[Plan](./sprint-57-160-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `29da11e8`)
- [x] **Prong 1 — path verify**: EDIT targets exist; NEW paths free; `CHANGE-127` + design-note `62` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-masker-ctor-absent** — no existing ctor at `observation_masker.py:47` (additive-safe)
  - [x] **D-abc-signature** — `_abc.py:57-80` declares only `mask_old_results` (impl `__init__` = impl-detail, no ABC change)
  - [x] **D-factory-masker-inject** — `structural.py:115` + `preclear.py:90` both accept `masker=` kwarg
  - [x] **D-tool-msg-shape** — tool results `role=="tool"` with `name` + `tool_call_id` (`chat.py:76-93`)
  - [x] **D-harness-import-shadow** — noted; mirror 57.139 guards on Day 2
- [x] **Prong 3 — schema verify**: N/A (no DB tables / migrations / ORM columns)
- [x] **D-baselines** — pytest 3180 · wire 26 · Vitest 927 · mockup 51 · mypy `src` 400 · run_all 11/11
- [x] **Catalog drift** — progress.md Day-0 table (5 D-items, all GREEN)
- [x] **Go/no-go** — PROCEED (0 drift, scope shift ~0%)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-160-compaction-tool-anchored-masking` (from `main` `29da11e8`)
- [ ] 🚧 Restart backend to DEFAULTS — DEFERRED to Day 3 clean-restart (Day 1-2 fully offline; Day 3 sets defaults + only the 57.160 lever)

---

## Day 1 — Tool-anchored masking mode + env lever (US-1, US-2)

### 1.1 Masking mode
- [x] **`DefaultObservationMasker.__init__(*, tool_anchor_keep: int | None = None)`** — keyword-only ctor stores flag
- [x] **tool-anchored branch in `mask_old_results`** — `_mask_tool_anchored` keeps last N `role=="tool"` intact, tombstones older (same format via extracted `_tombstone`); `<=N` + `keep<1` passthrough; `None` → `_mask_user_anchored` byte-identical

### 1.2 Env lever + factory injection
- [x] **`_compaction_tool_anchored_keep() -> int | None`** — reads `CHAT_COMPACTION_TOOL_ANCHORED_MASKING`; `>=1` → N; unset/invalid/0/neg → None; knob docstringed
- [x] **inject masker into Structural + PreClear when set** — `DefaultObservationMasker(tool_anchor_keep=N)` → `StructuralCompactor(masker=)` + `PreClearCompactor(masker=)`; None → `masker=None` (byte-identical); import + MHist added

### 1.3 Tests
- [x] **tool-anchored masker unit tests** — +5 (reduces / default-None no-op regression / `<=N` passthrough / provenance+non-tool / keep=0); existing 6 UNCHANGED → 11 passed
- [x] **factory env-reader + injection tests** — +6 (parametrized env / default-user-anchored / inject-structural / inject-preclear) → 32 passed

### 1.x Partial gate
- [x] black/isort/flake8/mypy clean on touched files (fixed 2 E501 in masker test)

---

## Day 2 — A/B reduction/retention harness (US-3)

### 2.1 Harness + corpus
- [x] **`scripts/benchmark_tool_anchored_masking.py`** — mirror 57.139; deterministic OFF-vs-ON + `_mechanical_retention_ok`; NO Azure arm (behavioural retention → Day 3 drive-through, documented); cp950 + importlib-shadow guards. Verdict: **off 0.00% / on 60.83% / retention 100% / recommend_default_on True**
- [x] **`tool_anchored_masking_cases.yaml`** — 8 single-user-turn cases incl. `keep-covers-all` boundary; `load_cases` parses

### 2.2 Harness CI-safe tests
- [x] **`test_benchmark_tool_anchored_masking.py`** — 13 tests (real TiktokenCounter; OFF-noop/ON-reduces/passthrough/keep-1/fixture-verdict/report-logic) → 13 passed

### 2.x Full gate
- [x] pytest **3202 passed + 6 skipped** (baseline 3180 +28) · mypy `src` 400 · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · FE untouched → Vitest 927 / mockup 51 unchanged (0 FE files → build N/A)

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM (MANDATORY)

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale 57.159 backend (PID 65320); confirmed `:8000` free + `python.exe` count 0 (no orphan); started single no-`--reload` backends with env-before-start + startup-log confirmed sole owner (3 legs)

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] Real chat-v2 (`/chat-v2`, real_llm) + Azure gpt-5.2 + real knowledge_search + real Qdrant, dev-login jamie@acme.com: Leg 3 = 6× knowledge_search in ONE user turn
- [x] **THE fix (real UI)**: 57.159 `CompactionMarker` renders **REAL reductions** on the DEFAULT single-user-turn path — `13,615 → 7,933 (−42%)`, `16,199 → 7,984 (−51%)` — vs 57.159's no-op `N→N`. context bounded ~8-9k vs 4k→35k
- [x] Context retention: `BOREALIS-9` + all 6 topics retained through aggressive compaction; agent completed all 6 searches (final summary blocked by an UNRELATED HITL `awaiting_approval` — honest caveat in progress)
- [x] Screenshot `artifacts/sprint-57-160-leg3-compaction-real-reduction.png` + full observed-vs-intended + KEY FINDING (Structural message-count-ratio blindness → PreClearCompactor needed to surface) → progress.md Day 3

---

## Day 4 — CHANGE-127 + closeout

### 4.1 CHANGE-127 + design note
- [x] **`CHANGE-127-tool-anchored-observation-masking.md`** (gap + fix + drive-through PASS + AD closed + KEY finding)
- [x] **Design note `62-tool-anchored-masking-design.md`** (spike — 8-point gate all ✅; data-gated flip-to-default verdict + Structural-blindness finding)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`compaction-tool-anchored-masking-spike` 0.60, 1st pt ~1.0 IN band)
- [x] Final gate sweep: mypy 400 · run_all 11/11 · pytest 3202+6skip · Vitest 927 / mockup 51 (FE untouched) · lint clean · LLM-SDK-leak clean
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`; annotated `AD-Compaction-ToolAnchored-Preclear-Phase58` mechanism-half closed) · sprint-workflow matrix (new `compaction-tool-anchored-masking-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): 0 violations; v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
