# Sprint 57.130 — Checklist (chat-v2 LoopTerminated wire surface — wire the server-side-only `LoopTerminated` Cat-8 event to the chat-v2 SSE stream so a FATAL-terminated run stops hanging. Backend: add `LoopTerminated` to `serialize_loop_event` (mirror `tripwire_triggered`) + `WIRE_SCHEMA` (24→25, a NEW wire type) → codegen regenerates `loopEvents.generated.ts`; parity test 24→25 + `LoopTerminated` UNWIRED→WIRED. Frontend: `mergeEvent` `loop_terminated` case flips the dangling pending `ToolBlock` → error (stuck-chip fix) + records `turn.terminated={reason,detail}` rendered as a `.badge.danger` "terminated · {reason}" + sets the turn terminal (composer unfreezes). **Drive-through MANDATORY** — stage a REAL fatal termination → UI shows the reason + the pending chip clears. Closes `AD-LoopTerminated-Wire-Surface`. CHANGE-097; NO design note (cross-stack wire-surfacing).)

[Plan](./sprint-57-130-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch ✅

### 0.1 Three-prong Day-0 verify (against `main` HEAD `b9334946`)
- [x] **Prong 1 — path verify**: all edit targets exist (NOTE: parity test under `backend/tests/`, not `backend/src/`); `CHANGE-097` free ✅
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-loopterminated-emission-sites** — `grep "LoopTerminated("` → defined `events.py:297`; emitted ONLY `loop.py:2939` + `:3008` (no 3rd) ✅
  - [x] **D-serializer-precedent-shape** — `tripwire_triggered` `{type,data}` envelope (`sse.py:300-307`); chain ends `NotImplementedError` `:481`; wrapper auto-injects `trace_id` ✅
  - [x] **D-wire-count-24-vs-fe-union** — `len(WIRE_SCHEMA)`==**24** (canonical); run_all green → FE generated already in sync at 24 (recon "23" was a miscount) ✅
  - [x] **D-codegen-invocation** — `scripts/codegen/generate_event_schemas.py` + `check_event_schema_sync.py` (run_all #10); `loopEvents.generated.ts` is codegen-only ✅
  - [x] **D-mergeEvent-default-noncrash** — `default` uses `const _exhaustive: never = ev` (exhaustive guard → tsc FORCES the new case); `loop_end`/`tool_call_result` shapes captured ✅
  - [x] **D-pending-toolblock-identify** — pending predicate `b.type==="tool" && b.status==="pending"` ✅
  - [x] **D-mockup-fidelity-zero-delta** — terminated badge reuses `.badge.danger` (`styles-mockup.css:526`, `var(--danger)`) → 0 new CSS / 0 new oklch ✅
  - [x] **D-drive-through-trigger** — chosen: `web_search` raises `WebSearchConfigError` (unset `BING_SEARCH_API_KEY`) → unregistered → FATAL → terminate mid-tool ✅
- [x] **Prong 3 — schema verify**: N/A (no new DB table / migration / ORM) ✅
- [x] **D-baselines** — pytest 2727+5skip · wire 24(→25) · Vitest 904 · mockup 51 · mypy 0/372 · run_all 10/10 ✅
- [x] **Catalog drift** — progress.md Day-0 table (+ 2 Day-0-MISSED drifts found mid-impl: see below) ✅
- [x] **Go/no-go** — clean cross-stack surfacing; scope shift 0% → proceeded ✅
- [x] **Day-0-MISSED (caught mid-impl, logged in progress.md/retro)**: (1) **codegen `WIRE_TYPE_TO_INTERFACE` map** needs the new wire-type → interface entry (first codegen run hard-failed); (2) **3 hardcoded `24` count-test locations** (parity + FE `eventSchema.generated.test.ts` + `test_loop_start_active_skill.py`), not 1 ✅

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-130-chatv2-loop-terminated-wire-surface` (from `main` `b9334946`) ✅

---

## Day 1 — Backend: serialize + wire 24→25 + codegen (US-1/2) ✅

### 1.1 Serialize `LoopTerminated` (US-1)
- [x] **`sse.py` (EDIT)**: import `LoopTerminated` + serializer branch before `NotImplementedError` (`{type:"loop_terminated",data:{reason,detail,last_state_version}}`, mirrors `tripwire_triggered`); MHist + Last Modified ✅ — mypy 0/372

### 1.2 Wire registry 24→25 (US-2)
- [x] **`event_wire_schema.py` (EDIT)**: appended `"loop_terminated"` (`detail`/`last_state_version` nullable forms ARE in `_RECOGNIZED_TS_TYPES`); Purpose/Key-Components/section header 24→25 + MHist → `len==25` ✅
- [x] **`test_event_wire_schema_parity.py` (EDIT)**: `==24`→`==25` + renamed test; `LoopTerminated` UNWIRED→WIRED; docstring counts refreshed → parity **33 passed** ✅

### 1.3 Codegen regen (US-2)
- [x] **codegen**: added `"loop_terminated":"LoopTerminatedEvent"` to `WIRE_TYPE_TO_INTERFACE`; ran `generate_event_schemas.py` → `loopEvents.generated.ts` (`LoopTerminatedEvent` + union + `KNOWN_LOOP_EVENT_TYPES`) + `events.json` regenerated; `check_event_schema_sync` green ✅

### 1.4 Backend gate (partial)
- [x] black/isort/flake8 clean · mypy `src` **0/372** · run_all **10/10** (wire **25**, check_event_schema_sync ✅, LLM-SDK-leak clean) ✅

---

## Day 2 — Frontend: mergeEvent + turn field + chip + tests (US-3/4/5) ✅

### 2.1 `mergeEvent` `loop_terminated` + turn field (US-3/4)
- [x] **`types.ts` (EDIT)**: `AgentTurn += terminated?:{reason;detail?}` + MHist/Last Modified; de-brittled stale `user_message` "wire count stays 24" comment ✅
- [x] **`chatStore.ts` (EDIT)**: `case "loop_terminated"` after `loop_end` — flip active-turn pending `ToolBlock`→error (output "terminated:{reason}") + `turn.terminated` + `waiting:false` + status `"completed"` (no new enum); Description case-list + MHist ✅ — build clean

### 2.2 Terminated badge render (US-4)
- [x] **`AgentTurn.tsx` (EDIT)**: head renders `<span className="badge danger">terminated · {reason}</span>` when `turn.terminated`; reuses existing `.badge.danger` → NO new CSS / oklch; MHist ✅ — `check:mockup-fidelity` 51 byte-identical; `diff styles-mockup.css` empty

### 2.3 FE tests (US-5)
- [x] **`chatStore.mergeEvent.test.ts` (EDIT)**: `loopTerminated` fixture + 3 tests (pending-tool flip / terminated-record+status / no-pending-no-crash) → 58 passed ✅
- [x] **`eventSchema.generated.test.ts` (EDIT)**: count `24→25` + `loop_terminated` recognition test ✅

### 2.4 Backend serializer test (US-5)
- [x] covered by the parity `test_serializer_field_set_matches_registry` parametrized case (LoopTerminated now WIRED) ✅

### 2.5 Full gate
- [x] mypy `src` **0/372** · run_all **10/10** (**25**) · backend pytest **2727+5skip** · Vitest **908** (+4) · `npm run lint && npm run build` clean · mockup **51** (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean ✅
  - NOTE: `tests/unit/api/v1/chat/` ALONE shows 2 `test_audit_log_observer` failures — pre-existing Risk Class C isolation artifact (pass in full suite); NOT this change

---

## Day 3 — Drive-through (US-6) — real UI + real backend + real LLM — **PASS** ✅

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale PID 40596; :8000 FREE (no orphans); fresh `uvicorn api.main:app` (bg `b1537857y`) → "startup complete"; Vite :3007 untouched ✅

### 3.2 Drive-through (MANDATORY — NOT gate-only) — **PASS** (real Azure gpt-5.2, jamie@acme.com/acme-prod)
- [x] Trigger: `web_search` (unset `BING_SEARCH_API_KEY`) → `WebSearchConfigError` → unregistered → FATAL → `LoopTerminated(fatal_exception)` mid-tool ✅
- [x] turn: gpt-5.2 called `web_search` → handler raised → terminate ✅
- [x] **THE fix (real UI)**: pending `web_search` chip → **error** (output `terminated: fatal_exception`); turn head **`terminated · fatal_exception`** `.badge.danger`; `lastAgentHasLiveDot:0` (not stuck running); composer textbox editable (unfrozen) ✅
- [x] End-to-end proof: the render requires serializer (backend) + `KNOWN_LOOP_EVENT_TYPES` (codegen) + new `mergeEvent` case all live ✅
- [x] Screenshot `.playwright-mcp/drivethrough-57130-loop-terminated-PASS.jpeg` + observed-vs-intended → progress.md Day 3 ✅

---

## Day 4 — CHANGE-097 + closeout ✅

### 4.1 CHANGE-097
- [x] **`CHANGE-097-chatv2-loop-terminated-wire-surface.md`** (root cause + cross-stack fix + drive-through PASS + AD closed) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-fatal-terminate-wire-surface` 0.55, 1st data point ratio ~1.29 slightly over → KEEP single-data-point; drive-through-trigger-hunt the variance source) + progress.md final ✅
- [x] Final gate sweep: mypy 0/372 · run_all 10/10 (25) · pytest 2727+5skip · Vitest 908 · mockup 51 · build clean · black/isort/flake8 clean · LLM-SDK-leak clean ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-LoopTerminated-Wire-Surface`) · sprint-workflow matrix `chatv2-fatal-terminate-wire-surface` 0.55 row
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations (REMOVES an AP-4 Potemkin); v2 lints 10/10 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
