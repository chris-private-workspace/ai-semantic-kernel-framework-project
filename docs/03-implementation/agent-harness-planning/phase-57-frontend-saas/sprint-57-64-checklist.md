# Sprint 57.64 Checklist — Chat-Path Keystone Wiring (Cat 5 PromptBuilder + Cat 3 Memory Tools + Cat 11 Subagent Tools)

**Plan**: [`sprint-57-64-plan.md`](./sprint-57-64-plan.md)
**Created**: 2026-06-01
**Status**: Draft (code gated on scope approval)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Day-0 prong items below were PRE-VERIFIED by the planning researcher (D1-D8 in plan §0/§8); re-confirm at sprint start before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [ ] **Prong 1 (path)**: confirm `make_default_executor` at `backend/src/business_domain/_register_all.py:128` (NOT under `agent_harness/`, D1); `_category_factories.py` exists (57.63); `make_task_spawn_tool`/`make_handoff_tool` at `agent_harness/subagent/tools.py:51/:128`
  - Verify: `grep -n "def make_default_executor" backend/src/business_domain/_register_all.py`
- [ ] **Prong 2 (content)**: confirm `register_builtin_tools` registers memory but NOT subagent (D3, `tools/__init__.py:56-120`); confirm `handler.py:220-239` omits `prompt_builder=` (D5); confirm `loop.py:196` has `prompt_builder` param + `:881` true-branch (D4); confirm `check_promptbuilder_usage.py` root = `agent_harness` → false-green (D6); confirm `memory_placeholder_handler` fallback (`tools/__init__.py:117-120`)
  - Verify: `grep -n "register_builtin_tools\|memory_placeholder_handler" backend/src/agent_harness/tools/__init__.py`
- [ ] **Prong 3 (schema)**: confirm memory tables + subagent ORM already exist (NO new migration); resolve `SubagentResultReducer` presence in `_contracts/subagent.py` (D8 — absent → define)
  - Verify: `grep -rn "class SubagentResult\|class SubagentResultReducer" backend/src/agent_harness/_contracts/subagent.py`
- [ ] Catalogue drift findings (re-confirm D1-D8) in progress.md; go/no-go for Day 1

### 0.2 Branch + decisions
- [ ] Create branch `feature/sprint-57-64-chat-path-keystone-wiring` from main
- [ ] Confirm scope decisions: A-3a includes FORK/TEAMMATE/AS_TOOL, EXCLUDES HANDOFF; `SubagentResultReducer` define-vs-reuse; Agent-delegated yes/no (Workload 4-segment); C-11 secrets set? (real_llm e2e leg gated)

---

## Day 1 — Shared surface + Cat 5 (keystone)

### 1.1 Shared change surface
- [x] Extend `make_default_executor` (`_register_all.py`) to accept opt-in memory deps + subagent dispatcher (backward-compatible when absent); thread `user_id` through `router.py`/`handler.py` (Day 2 ✅ — params default None, byte-identical 55.2 when absent; user_id via router→handler + TraceContext)
  - DoD: existing chat tests still pass; default (no deps) path unchanged
  - Verify: `pytest tests/integration/api/test_chat_e2e.py -q`
- [x] ADD `make_chat_prompt_builder` / `make_chat_memory_deps` / `make_chat_subagent_dispatcher` to `_category_factories.py` (mirror existing `make_chat_*` pattern)
  - ✅ all 3 done (`make_chat_prompt_builder` Day 1; `make_chat_memory_deps` + `make_chat_subagent_dispatcher` Day 2)
  - DoD: mypy strict clean; no SDK import in `agent_harness/**`
  - Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green)

### 1.2 Cat 5 PromptBuilder injection (US-1, keystone)
- [x] Pass `prompt_builder=` into `AgentLoopImpl(...)` (`handler.py` ~L226-244) (Day 1 ✅)
  - DoD: chat path reaches `loop.py:881` true-branch (`loop._prompt_builder is not None`)
  - 🔸 `memory_provider` deferred to Day 2 (ties to Cat 3 memory wiring)
- [x] Integration test: `PromptBuilt` emitted on chat SSE path (fallback NOT taken); negative guard (builder removed → no `PromptBuilt`) (Day 1 ✅ — `test_chat_keystone_wiring.py`, 3 passed)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -q` → 3 passed

---

## Day 2 — Cat 3 Memory + Cat 11 Subagent

### 2.1 Cat 3 memory tools (US-2)
- [x] Wire `make_chat_memory_deps` → `register_builtin_tools(...)` in `make_default_executor`; assert REAL handler (not `memory_placeholder_handler`) (Day 2 ✅ — `is not` identity guard)
  - DoD: memory tools registered with real retrieval/layers; tenant-scoped (per-call via ExecutionContext from TraceContext)
- [x] Integration test: `memory_search`/`memory_write` exec on chat path; cross-tenant isolation; negative (no deps → memory tools unregistered) (Day 2 ✅ — 4 tests; cross-tenant: tenant_b same session → `[]`)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -q` → 10 passed

### 2.2 Cat 11 subagent tools — A-3a (US-3)
- [x] Resolve `SubagentResultReducer`: **REUSE** — handler merges `SubagentResult` internally (spawn→wait_for→dict); no new contract. 17.md `task_spawn` risk_level = SEQUENTIAL/AUTO/MEDIUM (Day 2 ✅)
- [x] Register `make_task_spawn_tool(dispatcher, parent_session_id=…)` + 1 AS_TOOL (`agent_researcher`) into the executor registry (EXCLUDE `make_handoff_tool`) (Day 2 ✅ — `_adapt_subagent_handler` Cat11→Cat2 bridge in registration layer)
  - DoD: FORK/TEAMMATE/AS_TOOL spawnable; HANDOFF stub tests unchanged (`test_handoff.py`, `test_loop.py` still assert `HANDOFF_NOT_IMPLEMENTED` — 57 passed)
- [x] Integration test: FORK subagent spawn + `SubagentResult` merge on chat path; subagent failure does not crash parent (fail_soft); negative (no dispatcher → `task_spawn` unregistered) (Day 2 ✅ — 3 tests)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -q` → 10 passed

---

## Day 3 — Cross-cutting Tests + lint true-green + real_llm e2e

- [x] Combined integration test: Cat 5 + Cat 3 + Cat 11 all active in one chat SSE run + multi-tenant scoping (memory + subagent per tenant) (Day 3 ✅ — `test_combined_all_three_active_one_run`: PromptBuilt + memory_write→memory_search round-trip + FORK task_spawn merge in one run; keystone file 10 → 11 passed)
- [x] Flip `check_promptbuilder_usage.py` false-green → true-green (detect chat call-site `prompt_builder=`); confirm it FAILS when kwarg removed (Day 1 ✅ — coupled w/ Cat 5; path-targeted AST positive check; regression confirmed)
  - Verify: `python scripts/lint/check_promptbuilder_usage.py` (green) + manual kwarg-removal regression check
- 🚧 `real_llm` e2e live leg DEFERRED (confirmatory, not primary gate) — reason: (1) PromptBuilt on the chat SSE flow is proven DETERMINISTICALLY by the mock integration tests (`test_cat5_chat_path_emits_prompt_built` + combined), the plan's stated primary gate; (2) a clean HTTP-level `PromptBuilt`-in-stream assertion is blocked by A-5 (LoopEvent→SSE surfacing) being OUT of scope (§9) — PromptBuilt is an in-process LoopEvent, not yet a client SSE event; (3) the live real_llm path was ALREADY exercised end-to-end in C-11 (`64f29259`, reached END_TURN + audit_log Δ=1); (4) re-running incurs Azure cost and the `cost_ledger Δ≥2` assertion is FIX-024 known-red on gpt-5.2. Live confirmation available on request.
  - Verify (when run): `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q` (or GitHub Actions "E2E Real-LLM Smoke")
- [x] Confirm LLM SDK leak 0 + mypy strict + 9/9 V2 lints (Day 3 ✅ — `check_llm_sdk_leak` 0; `mypy src/` 0/319; `python scripts/lint/run_all.py` 9/9 green)

---

## Day 4 — Closeout

- [x] Full validation sweep: `pytest` (all) / `mypy --strict` / `python scripts/lint/run_all.py` / frontend untouched / LLM SDK leak 0 (Day 4 ✅ — pytest 1934 passed / 4 skipped; mypy src 0/319; 9/9 V2 lints; frontend untouched; SDK leak 0)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-032-chat-path-keystone-wiring.md` (Day 4 ✅)
- [x] progress.md (Day 0-4 actuals) + retrospective.md (Q1-Q7) (Day 4 ✅)
- [x] Calibration: recorded in `calibration-log.md §3` (the post-REFACTOR-005 home for per-sprint calibration-retro entries) — `medium-backend` 0.80 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 as a **CAVEATED low-confidence point** (multi-session + `/compact`); KEEP 0.65, no baseline change, does NOT trigger the below-band-watch (needs clean measurement). `sprint-workflow.md §Active` block unchanged (no multiplier change). (Day 4 ✅)
- [x] Update Area-A capstone: mark 候選 Sprint A shipped; note D3 correction confirmed in runtime (Day 4 ✅)
- [ ] PR (no push without authorization)
