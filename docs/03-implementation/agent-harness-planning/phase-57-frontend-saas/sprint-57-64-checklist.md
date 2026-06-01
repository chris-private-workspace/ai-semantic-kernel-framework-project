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
- [ ] Extend `make_default_executor` (`_register_all.py`) to accept opt-in memory deps + subagent dispatcher (backward-compatible when absent); thread `user_id` through `router.py`/`handler.py`
  - DoD: existing chat tests still pass; default (no deps) path unchanged
  - Verify: `pytest tests/integration/api/test_chat_e2e.py -q`
- [ ] ADD `make_chat_prompt_builder` / `make_chat_memory_deps` / `make_chat_subagent_dispatcher` to `_category_factories.py` (mirror existing `make_chat_*` pattern)
  - DoD: mypy strict clean; no SDK import in `agent_harness/**`
  - Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green)

### 1.2 Cat 5 PromptBuilder injection (US-1, keystone)
- [ ] Pass `prompt_builder=` (+ `memory_provider`) into `AgentLoopImpl(...)` at `handler.py:220-239`
  - DoD: chat path reaches `loop.py:881` true-branch (`loop._prompt_builder is not None`)
- [ ] Integration test: `PromptBuilt` emitted on chat SSE path (fallback NOT taken); negative guard (builder removed → no `PromptBuilt`)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -k cat5 -q`

---

## Day 2 — Cat 3 Memory + Cat 11 Subagent

### 2.1 Cat 3 memory tools (US-2)
- [ ] Wire `make_chat_memory_deps(db, tenant_id, user_id)` → `register_builtin_tools(...)` in `make_default_executor`; assert REAL handler (not `memory_placeholder_handler`)
  - DoD: memory tools registered with real retrieval/layers; tenant-scoped
- [ ] Integration test: `memory_search`/`memory_save` `ToolCallExecuted` on chat path; cross-tenant isolation; negative (no deps → memory tools absent)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -k cat3 -q`

### 2.2 Cat 11 subagent tools — A-3a (US-3)
- [ ] Resolve `SubagentResultReducer` (define in `_contracts/subagent.py` or reuse merge); update 17.md (`task_spawn` risk_level + reducer registration)
- [ ] Register `make_task_spawn_tool(dispatcher, parent_session_id=…)` + AS_TOOL wrappers into the executor registry (EXCLUDE `make_handoff_tool`)
  - DoD: FORK/TEAMMATE/AS_TOOL spawnable; HANDOFF stub tests unchanged (`test_handoff.py`, `test_loop.py:311-330` still assert `HANDOFF_NOT_IMPLEMENTED`)
- [ ] Integration test: FORK subagent spawn + `SubagentResult` merge on chat path; subagent failure does not crash parent (fail_soft); negative (no dispatcher → `task_spawn` unregistered)
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -k cat11 -q`

---

## Day 3 — Cross-cutting Tests + lint true-green + real_llm e2e

- [ ] Combined integration test: Cat 5 + Cat 3 + Cat 11 all active in one chat SSE run + multi-tenant scoping (memory + subagent per tenant)
- [ ] Flip `check_promptbuilder_usage.py` false-green → true-green (detect chat call-site `prompt_builder=`); confirm it FAILS when kwarg removed
  - Verify: `python scripts/lint/check_promptbuilder_usage.py` (green) + manual kwarg-removal regression check
- [ ] `real_llm` e2e: benign multi-turn Azure run → END_TURN with `PromptBuilt` event (gated on C-11 secrets)
  - Verify: `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q` (or GitHub Actions "E2E Real-LLM Smoke")
- [ ] Confirm LLM SDK leak 0 + mypy strict + 9/9 V2 lints

---

## Day 4 — Closeout

- [ ] Full validation sweep: `pytest` (all) / `mypy --strict` / `python scripts/lint/run_all.py` / frontend untouched / LLM SDK leak 0
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-0XX-chat-path-keystone-wiring.md`
- [ ] progress.md (Day 0-4 actuals) + retrospective.md (Q1-Q7)
- [ ] Calibration: record `medium-backend` ratio + `agent_factor` (if delegated) in `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`
- [ ] Update Area-A capstone: mark 候選 Sprint A shipped; note D3 correction confirmed in runtime
- [ ] PR (no push without authorization)
