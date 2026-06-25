# Sprint 57.144 — Checklist (Cat 2 tool-description lint + structured-error reflection)

[Plan](./sprint-57-144-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `74555317`)
- [x] **Prong 1 — path verify**: NEW files free (check_tool_descriptions.py / _error_taxonomy.py / benchmark_tool_error_reflection.py / fixtures / tests); EDIT files present (executor.py / tools.py / loop.py / run_all.py); `CHANGE-111` free; design-note number free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-tool-message-field** — grep loop tool-result→Message construction; confirm whether the LLM-visible tool message renders `ToolResult.content` vs `.error` (design enrich to write the rendered field)
  - [x] **D-runall-wiring** — read `scripts/lint/run_all.py` LINTS list + `tests/unit/scripts/lint/`; confirm the LIVE mechanism the new detector must wire into (run_all AND/OR pytest)
  - [x] **D-toolspec-call-shape** — grep all `ToolSpec(` across `tools/`, `skills/`, `subagent/`; confirm direct call + literal `description=` kwarg (note any indirect/helper construction the AST detector would miss)
  - [x] **D-retry-line** — re-verify `error_handling/retry.py` ErrorClass/matrix line range (56-82 vs 71-82) + `_abc.py:30-36`
  - [x] **D-loop-import-boundary** — confirm Cat 1 `loop.py` may import Cat 2 `tools/_error_taxonomy` public symbol (category-boundaries; loop already imports `ToolResult`)
- [x] **Prong 3 — schema verify**: N/A (NO DB table / migration / ORM column this sprint)
- [x] **D-baselines** — pytest 2881+5skip · mypy src 0/381 · Vitest 922 · wire 26 · run_all LINTS 10 scripts (aggregate "21" re-verify at gate)
- [x] **Catalog drift** — progress.md Day-0 table (D-IDs + finding + implication + §Risks cross-ref)
- [x] **Go/no-go** — scope-shift % → proceed / revise / abort

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-144-tool-desc-lint-reflection` (from `main` `74555317`)

---

## Day 1 — Half A lint detector + Half B taxonomy (US-1, US-2 part)

### 1.1 tool-description lint detector
- [x] **`scripts/lint/check_tool_descriptions.py`** — AST detector (mirror check_llm_sdk_leak)
  - DoD: `find_violations(root)` finds `ToolSpec(...)` calls; checks description non-empty + `>= MIN_DESCRIPTION_LEN` + no placeholder + param-level descriptions; test tools allow-listed; `main(--root)` exit 0/1
  - Verify: `python -m scripts.lint.check_tool_descriptions --root backend/src` → `OK` exit 0
- [x] **`tests/unit/scripts/lint/test_tool_descriptions.py`** — pytest mirror (importlib load + positive/negative cases)
  - DoD: tests a passing spec + a stub (empty/short) + a missing-param-desc + an allow-listed tool
  - Verify: `cd backend && pytest tests/unit/scripts/lint/test_tool_descriptions.py`
- [x] **run_all / pytest wiring** — register detector per D-runall-wiring
  - DoD: the live lint mechanism executes the new detector (run_all LINTS 10→11)
  - Verify: `python scripts/lint/run_all.py` shows 11 green

### 1.2 error-taxonomy pure module
- [x] **`agent_harness/tools/_error_taxonomy.py`** — `ErrorTaxonomy` enum + `classify_tool_error` + `render_reflection`
  - DoD: pure (no I/O/LLM); 5 taxonomy branches (PARAMETER / WRONG_TOOL / FAILED_API / INVOCATION / UNKNOWN); `render_reflection` returns a short actionable string
  - Verify: `cd backend && python -c "from agent_harness.tools._error_taxonomy import classify_tool_error"`
- [x] **`tests/unit/agent_harness/tools/test_error_taxonomy.py`** — unit tests for each branch + render
  - Verify: `cd backend && pytest tests/unit/agent_harness/tools/test_error_taxonomy.py`

### 1.x partial gate
- [x] mypy + flake8 + black on the new files

---

## Day 2 — Half B executor enrich + loop.py B2 refactor + env lever (US-2, US-3)

### 2.1 executor enrich + ToolResult field
- [x] **`_contracts/tools.py`** — `ToolResult += error_taxonomy: str | None = None`
  - DoD: optional field; ABC signature unchanged; success=True leaves it None
- [x] **`tools/executor.py`** — enrich failure ToolResult (lever-gated) writing the LLM-visible field (D-tool-message-field)
  - DoD: handler-exception path + schema/validation `_fail` path set `error_taxonomy` + enrich `content` when `CHAT_TOOL_ERROR_REFLECTION` on; byte-identical when off
  - Verify: `cd backend && pytest tests/unit/agent_harness/tools/ -k executor`

### 2.2 loop.py rare-path refactor (B2)
- [x] **`loop.py:3023-3030`** — build content via `render_reflection(classify_tool_error(...))` when lever on; byte-identical when off
  - DoD: rare executor-raises path produces same structured reflection as dominant path; import Cat 2 public symbol
  - Verify: `cd backend && pytest tests/integration/orchestrator_loop/ -k error` (existing error-path tests still green)

### 2.3 env lever
- [x] **`CHAT_TOOL_ERROR_REFLECTION`** — module-level `_reflection_enabled()` (per-call env read, no cached state — Risk Class C); default off
  - DoD: off = today's behavior; on = enriched; documented WHY default-off-pending-A/B

### 2.x Full gate
- [x] mypy `src` 0/381 · run_all LINTS 11/11 · backend pytest 2881+new · Vitest 922 · `npm run lint && npm run build` clean · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — A/B harness + real-Azure drive-through (US-4)
_(Pure-backend/eval spike — NO chat-v2 UI surface. Verification = gate + real-Azure A/B harness, explicitly "gate-only + real-SDK", NOT a UI drive-through.)_

### 3.1 A/B harness + corpus + CI-safe test
- [x] **`backend/scripts/benchmark_tool_error_reflection.py`** — mirror benchmark_correction_hygiene
  - DoD: `load_cases` + `build_messages(case, arm)` (plain vs enriched) + `run_arm` (real LLM) + `build_report` (pure: next-turn fix-rate + mean tokens; 5pp materiality) + `main()` Azure profile
- [x] **`tests/fixtures/tools/tool_error_reflection_cases.yaml`** — corpus (missing-param / wrong-tool / sim-API-error; innocuous text, no content-filter trip)
- [x] **`tests/unit/scripts/test_benchmark_tool_error_reflection.py`** — CI-safe (MockChatClient, NO Azure)
  - Verify: `cd backend && pytest tests/unit/scripts/test_benchmark_tool_error_reflection.py`

### 3.2 Real-Azure A/B (MANDATORY — the spike's CATCH; NOT gate-only)
- [x] Clean Azure env; run `RUN_AZURE_INTEGRATION=1 ... python scripts/benchmark_tool_error_reflection.py`
- [x] **Record verdict**: per-arm next-turn fix-rate + token delta → go/no-go on flipping the lever default
- [x] Verdict + numbers → progress.md Day 3 (explicit: real-SDK harness, not a UI drive-through)

---

## Day 4 — CHANGE-111 + closeout

### 4.1 CHANGE-111 + design note
- [x] **`CHANGE-111-tool-desc-lint-error-reflection.md`** (gap + fix both halves + A/B verdict + AD closed)
- [x] **Spike design note** (next number after 47) — 8-point quality gate (header per US / file:line / decision matrix Half A-vs-register + reflection-on-vs-off / verification command / fixture ref / open invariants (rare-path covered? content-filter caveats) / rollback / 17.md cross-ref — ToolResult field add)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`tool-reflection-and-lint-spike` 0.60, 1st data point; flag if ratio out of band → re-point)
- [x] Final gate sweep: mypy · run_all LINTS 11 · pytest · Vitest · build · lint · LLM-SDK-leak
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Tool-Description-Lint-Reflection` — last canonical item; Phase 58 pool remains) · sprint-workflow matrix (`tool-reflection-and-lint-spike` row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; run_all LINTS 11/11
- [x] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push outward-facing) → post-merge status flip after gh-verified MERGED
