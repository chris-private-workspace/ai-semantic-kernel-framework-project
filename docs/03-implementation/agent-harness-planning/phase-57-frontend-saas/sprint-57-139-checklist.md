# Sprint 57.139 — Checklist (layered compaction: tool-result preclear yield + ACON-band measurement spike)

[Plan](./sprint-57-139-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `3bf4a727`)
- [x] **Prong 1 — path verify**: ✅ 7 NEW free; `_category_factories.py` present; CHANGE max 105 → 106; design note max 42 → 43; compactor test dir to create
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-compaction-strategy-wire** — ✅ `CompactionStrategy` on wire (`event_wire_schema.py`/`sse.py`/`router.py`) → **reuse `STRUCTURAL`** for preclear (no wire/codegen touch, count 25)
  - [x] **D-factory-location** — ✅ all in `_category_factories.py` (`make_chat_compactor:143` + `_compaction_token_budget:116` + `_compaction_keep_recent_turns:126`); no separate `factory.py` (recon misattribution)
  - [x] **D-tokencounter-default** — ✅ `TiktokenCounter(model="gpt-4o")` → harness uses same
  - [x] **D-loop-call-site** — ✅ single `loop.py:2221`; `_compactor` injected `:405` → ChainedCompactor transparent, loop UNTOUCHED
  - [x] **🔴 D-masker-user-anchored** (KEY) — `mask_old_results` USER-anchored (`observation_masker.py:62-66`); chat single-user-turn (`_category_factories.py:129-134`) → masking NO-OPs single-send, fires only rehydrated/injected multi-turn → corpus MUST be multi-user-turn + drive-through rehydrated + KEY finding → `AD-Compaction-ToolAnchored-Preclear-Phase58`
- [x] **Prong 3 — schema verify**: N/A (no new DB table / migration / ORM column)
- [x] **D-baselines** — pytest 2797+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10 (from 57.138; re-verify at gate)
- [x] **Catalog drift** — ✅ progress.md Day-0 table (5 D-rows)
- [x] **Go/no-go** — ✅ scope-shift < 20% (sharpen, not redirect) → PROCEED

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-139-layered-compaction-spike` (from `main` `3bf4a727`)

---

## Day 1 — PreClearCompactor + ChainedCompactor (US-1)

> Test-path drift (Day-0/Day-1): existing compactor tests are FLAT `tests/unit/agent_harness/context_mgmt/test_compactor_<name>.py` (not a `compactor/` subdir). Tests placed at the existing convention (AP-3). Preclear `tokens_after` uses a real token-reduction RATIO (masked/original) applied to loop-tracked tokens_before — fixes structural's message-count-ratio blindness to masking + keeps scale consistent for the chain.

### 1.1 `PreClearCompactor` (`compactor/preclear.py`)
- [x] **standalone LLM-free tool-result clearing layer at a lower trigger**
  - ✅ `should_compact` at `token_usage_so_far > preclear_ratio*token_budget` (ratio 0.50); runs ONLY `mask_old_results` (reuses `DefaultObservationMasker`), preserves system+HITL, honest passthrough when nothing masked; `strategy_used=STRUCTURAL`; tokens_after via real reduction ratio
  - Verify: `pytest tests/unit/agent_harness/context_mgmt/test_compactor_preclear.py` → 8 passed

### 1.2 `ChainedCompactor` (`compactor/chained.py`)
- [x] **sequential compactor composition threading state**
  - ✅ ordered `list[Compactor]`; threads compacted_state forward (preclear→hybrid), merges `messages_compacted`, carries last-stage tokens + C2 LLM-usage attribution; `should_compact` = any child; empty → ValueError
  - Verify: `pytest tests/unit/agent_harness/context_mgmt/test_compactor_chained.py` → 7 passed

### 1.3 Compactor unit tests
- [x] **preclear + chained tests** (FLAT path per convention)
  - ✅ preclear: masks only / triggers earlier / NO-OP too-few-user-turns / preserves system+HITL / real reduction ratio / STRUCTURAL strategy; chained: threads state / merges / passthrough / usage carry / empty-raises
  - Verify: 15 passed

### 1.4 Factory preclear branch + env knob (US-3, pulled into Day 1)
- [x] **selectable, default-OFF, byte-identical default**
  - ✅ `_compaction_preclear_ratio()` (`CHAT_COMPACTION_PRECLEAR_RATIO`, valid (0,1) else 0=OFF); `make_chat_compactor`: ratio>0 → `ChainedCompactor([PreClearCompactor(TiktokenCounter), hybrid])`; unset → bare `HybridCompactor` (byte-identical); `test_category_factories.py` 22 still pass

### 1.x Partial gate
- [x] ✅ mypy src 376 (0 issues) · black/isort/flake8 clean · v2 lints (run_all from repo root) 10/10 (incl. check_llm_sdk_leak) · 15 new + 34 existing compactor/factory tests pass

---

## Day 2 — Measurement harness + corpus + real-Azure run (US-2)

### 2.1 `benchmark_layered_compaction.py` + corpus fixture
- [x] **per-layer token reduction harness (mirror benchmark_sandbox_escape.py)**
  - ✅ `load_cases / build_transcript (spec→Messages) / measure_case (L0 / L1 tool-clear-only / L2 structural / L3 hybrid-semantic) / build_report (tool_clear_reduction, in_acon_band [0.26,0.54], structural_reduction, semantic_reduction, semantic_deferred_rate, preclear_recommended) / report_to_markdown / _amain (RUN_AZURE_INTEGRATION-gated L3) / main()`; REAL `TiktokenCounter(gpt-4o)` (NOT the internal approx); corpus = 6 specs tool-heavy→text-heavy + 1 single-turn NO-OP demo
  - Verify: `python scripts/benchmark_layered_compaction.py` → LLM-free core ran

### 2.2 CI-safe unit test
- [x] **harness load/measure/report test (no Azure)**
  - ✅ `test_benchmark_layered_compaction.py` (importlib) — load_cases (schema/dup/empty) · build_transcript · measure L0/L1/L2 real counter · L1==L2 non-redundant invariant · single-turn NO-OP · build_report band/deferral/recommended · no-L3 invariant → 13 passed

### 2.3 Real-Azure full run
- [x] **per-layer report incl. semantic deferral**
  - ✅ `RUN_AZURE_INTEGRATION=1` → mean tool_clear **33.72% IN band** · mean semantic 40.65% (LLM layer adds ~6.9pp over free tool-clear) · semantic_deferred_rate 66.67% · preclear_recommended True. Verdict: tool-clear captures ~83% of total yield free + defers 2/3; keep default OFF (composition-dependent + user-anchored NO-OP single-send) → env opt-in. Report → `artifacts/layered_compaction_report.{md,json}`

### 2.4 Factory preclear branch + env knob (US-3) — done Day 1.4
- [x] ✅ `_compaction_preclear_ratio()` + `make_chat_compactor` branch; default bare hybrid byte-identical (test_category_factories 22 pass)

### 2.x Full gate
- [x] ✅ mypy src 376 (0) · run_all 10/10 · backend pytest **2825 +5skip** (+28) · black/isort/flake8 clean (src/scripts/tests) · LLM-SDK-leak clean · Vitest 915 / mockup 51 untouched sentinels (backend-only)

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] ✅ no python pre-start, :8000 free, :3007 node untouched; preclear env (RATIO=0.5/BUDGET=2000/KEEP_RECENT=2) set BEFORE startup; ARM B restart with env UNSET

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] **preclear enabled no-regression** — ✅ ARM A: 3 real-Azure turns (TCP/TLS/QUIC) completed + rendered with `ChainedCompactor([preclear, hybrid])` active; chat identical. (compaction semantic did NOT fire on plain chat — cheap count == turn count)
- [x] **default-OFF unchanged** — ✅ ARM B: restart env UNSET → bare `HybridCompactor` → "capital of Japan?"→"Tokyo" → completed
- [x] **THE walk (real UI)**: ✅ answers render / no broken behavior / labels real / mode real_llm; honest — compaction/preclear masking NOT UI-triggerable on plain chat (user-anchored + needs tool results + short single-send), CATCH = harness
- [x] Screenshot + observed-vs-intended → progress.md Day 3 (`dt-57139-preclear-on-no-regression.jpeg` + `dt-57139-default-off-unchanged.jpeg`; honest 兩者結合: CATCH=harness, UI=no-regression + chain wiring + byte-identical default)

---

## Day 4 — CHANGE-106 + design note 43 + closeout

### 4.1 CHANGE-106 + design note (spike)
- [x] ✅ **`CHANGE-106-layered-compaction-acon.md`** (gap + fix + per-layer A/B numbers + drive-through PASS + AD closed)
- [x] ✅ **`43-layered-compaction-acon-design.md`** (8/8 gate; §3 N/A justified — new Compactor impls of the EXISTING ABC, CompactionResult/Strategy unchanged → no new 17.md contract)

### 4.2 Closeout
- [x] ✅ retrospective.md Q1-Q7 + calibration (`layered-compaction-spike` 0.60, 1st pt ~0.97 IN band → KEEP)
- [x] ✅ Final gate sweep: mypy src 376 (0) · run_all 10/10 · pytest 2825 +5skip · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest 915 / mockup 51 untouched sentinels
- [x] ✅ Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile (auto-memory) · next-phase-candidates (CLOSED `AD-Context-Layered-Compaction-ACON`; advance → #1 next + 2 Phase 58 follow-ons) · sprint-workflow matrix (`layered-compaction-spike` row). (#330 flip still OPEN — sync main + resolve the 2-line Current-Sprint conflict before pushing 57.139 PR)
- [x] ✅ Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → no violations; v2 lints 10/10
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
