# Sprint 57.164 — Checklist (Tool-error taxonomy surfaced in chat-v2 UI)

[Plan](./sprint-57-164-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `2614303c`)
- [x] **Prong 1 — path verify**: all 11 EDIT targets exist + 2 REGEN targets exist; `CHANGE-131` slug free ✅
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-parity-two-events-one-type** — parity test is data-driven + asserts both branches share field set → auto-passes; **item 15 UNTOUCHED**
  - [x] **D-wire-count-tests** — count asserts test TYPES (stays 26 on field add); **item 17 UNTOUCHED**
  - [x] **D-drivethrough-trigger** — 3 `_build_failure`→chip paths confirmed (INVOCATION/WRONG_TOOL/PARAMETER); web_search=FATAL excluded; Day-3 candidates ranked
  - [x] **D-off-test-flips** — only `test_executor.py` 2 OFF-asserts (:345, :404) flip; integration test = ADD assertion (not flip)
- [x] **Prong 3 — schema verify**: N/A (no DB) — confirmed
- [x] **D-baselines** — pytest 3235 collected (3230+5skip) · wire 26 · mypy `src` 400/0 · run_all 11/11 (Vitest 930 / mockup 51 defer Day 2)
- [x] **Catalog drift** — progress.md Day-0 table ✅
- [x] **Go/no-go** — scope net ~−5% (reduction) → PROCEED

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-164-tool-taxonomy-ui` (from `main` `2614303c`) ✅

---

## Day 1 — Backend decouple + wire the taxonomy (US-1 + US-2)

### 1.1 Decouple classification from the lever (US-1)
- [x] **`executor.py:_build_failure` — always classify** ✅ classify unconditional; `content=render_reflection() if lever else ""`; docstring updated
- [x] **`loop.py:3068-3086` rare path — mirror decouple** ✅ `_tax`/`_err_taxonomy` always; only `_err_content` gated
- [x] **`_error_taxonomy.py` docstring** ✅ "classification always; lever gates LLM content" + MHist line

### 1.2 Thread taxonomy to the wire (US-2)
- [x] **`events.py` `ToolCallFailed` += `error_taxonomy: str | None = None`** ✅ (mypy 400/0)
- [x] **`loop.py` 2 emit sites (`_run_turns` + resume) += `error_taxonomy=result.error_taxonomy`** ✅
- [x] **`sse.py` both branches** — Executed=None / Failed=value ✅ (+ MHist)
- [x] **`event_wire_schema.py` `tool_call_result` += `"error_taxonomy": "string | null"`** ✅ count 26 (+ MHist); parity test auto-passes
- [x] **Codegen regen** ✅ `loopEvents.generated.ts` + `events.json` regen'd with `error_taxonomy` (git diff confirmed)

### 1.x Partial gate
- [x] mypy `src` 400/0 · run_all 11/11 (incl. event_schema_sync) · black/isort/flake8 clean · target backend pytest 117/117 ✅

---

## Day 2 — Frontend surface + tests (US-3)

### 2.1 FE capture + render (US-3)
- [x] **`types.ts` `ToolBlock` += `errorTaxonomy?: string | null`** ✅
- [x] **`chatStore.ts` `tool_call_result` case** — set `errorTaxonomy: ev.data.error_taxonomy` ✅ (build/tsc clean)
- [x] **`ToolBlock.tsx` conditional chip** — head row `.badge danger` + `data-testid` when `errorTaxonomy` present ✅ (`styles-mockup.css` byte-identical; mockup-fidelity 51 baseline)

### 2.2 Tests (backend OFF-flips + FE)
- [x] **`test_executor.py`** — 2 OFF-asserts flip to `== "invocation"` / `== "wrong_tool"` (keep `content == ""`); renamed `..._content_byte_identical` + docstring ✅
- [x] **`test_loop_error_handling.py`** — ADD (not flip) `test_rare_path_emits_taxonomy_on_wire_even_when_lever_off` (`ToolCallFailed.error_taxonomy == "invocation"`) ✅
- [x] **`test_sse.py`** — tool_call_result failure `error_taxonomy == "failed_api"` + success `is None` ✅
- [x] **`chatStore.mergeEvent.test.ts`** — helper +`error_taxonomy`; new capture test + success null assert ✅
- [x] **`eventSchema.generated.test.ts`** — UNTOUCHED (count 26; auto-passes) ✅ D-wire-count-tests confirmed
- [x] **`blocks.test.tsx`** — chip renders when present + absent otherwise (2 tests) ✅
- [x] **fixture drift** — `demoLoopEvents.ts` (2) + `LoopVisualizer.test.tsx` + `chatStore.pauseResume.test.ts` += `error_taxonomy: null` (tsc required-field, 57.116-class) ✅

### 2.x Full gate
- [x] mypy `src` 400/0 · run_all 11/11 · Vitest **933** (930+3) · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean · backend pytest **3231 passed, 5 skipped** (+1) ✅

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.0 🔴 Drive-through-discovered scope extension (user AskUserQuestion → Option a)
- [x] **Finding**: chip WIRED but NOT reachable on live 主流量 — tool failures `loop_terminated` (Cat 8 FATAL at `loop.py:3113/3028`) BEFORE the `ToolCallFailed` emit (`:3172`). Evidence: 404 + schema both → `loop_terminated{fatal_exception}`.
- [x] **Fix (loop.py, 2 terminate sites)**: emit `ToolCallFailed(+error_taxonomy)` before `yield LoopTerminated` — dominant (`result.error_taxonomy`) + rare (`classify_tool_error(exc)`). FE unchanged (loop_terminated only flips pending → chip persists). +1 test assertion (`test_fatal_exception_terminates_loop`: ToolCallFailed(invocation) precedes LoopTerminated). mypy 400/0 · flake8 clean · integration 9/9.

### 3.1 Clean restart (Risk Class E)
- [x] Backend `dev.py restart backend` → fresh sole worker (PID 52148, 8:19:30; old workers cleared) → new loop.py loaded; re-login (restart invalidated session)

### 3.2 Drive-through (MANDATORY — NOT gate-only) — 🟢 PASS
- [x] **Real tool failure** (lever OFF, real Azure gpt-5.2, session 3829811e): `get incident INC-99999` → `mock_incident_get` → mock 404
- [x] **THE surface (real UI)**: ToolBlock shows **`tool error taxonomy: failed_api`** chip; label real (httpx 404 → FAILED_API); output = real 404 error; turn `terminated` badge; loop trace shows `tool_call_result · ERROR` BEFORE `loop_terminated`. Success/pending tools show NO chip (Day-2 Vitest). Agent behavior unchanged (no LLM read).
- [x] Screenshots (`artifacts/…PASS-taxonomy-chip.png` + `…terminated-not-chip.png`) + observed-vs-intended → progress.md Day 3
- [x] Bonus live: HITL approval gate + Approve flow; memory recall (BOREALIS-9)

---

## Day 4 — CHANGE-131 + closeout

### 4.1 CHANGE-131
- [x] **`CHANGE-131-tool-error-taxonomy-ui.md`** ✅ (gap + Option B decouple + wire chain + reachability fix + drive-through PASS + ③3 AD closed). NO design note.

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`frontend-feature-with-event-wire-addition` 0.55, 4th data point ~1.4-1.55 OVER → KEEP 0.55, cause = drive-through-discovered mid-sprint loop.py extension) ✅
- [x] Final gate sweep: mypy 400/0 · run_all 11/11 · pytest **3231/5skip** · Vitest **933** · mockup 51 byte-identical · build/lint clean · LLM-SDK-leak clean ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (PR-pending) · MEMORY.md pointer + subfile `project_phase57_164_tool_taxonomy_ui.md` · next-phase-candidates (③3 CLOSED, ③2→57.165, shipped pointer) · sprint-workflow matrix (4th data point + Day-0 lesson) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/10/11 → 0 violations; v2 lints 11/11 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
