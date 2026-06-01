# Sprint 57.64 Progress — Chat-Path Keystone Wiring

**Sprint**: 57.64 (Cat 5 PromptBuilder + Cat 3 memory tools + Cat 11 subagent tools A-3a)
**Branch**: `feature/sprint-57-64-chat-path-keystone-wiring` (from main `f0874f35`)
**Scope class**: `medium-backend` (0.80) / **Agent-delegated: yes** → `agent_factor` `mechanical-greenfield-design-decisions` 0.65

> Modification History
> - 2026-06-01: Initial creation (Day 0-4 actuals + closeout)

---

## Day 0 — Plan-vs-Repo Verify + Branch

Day-0 三-prong verify was performed by the planning researcher (D1-D8, folded into plan §0/§8) and re-confirmed at sprint start:

- **D1 (path)**: `make_default_executor` is at `business_domain/_register_all.py` (NOT under `agent_harness/`) — sibling package; File Change List cites the real path.
- **D2 (content)**: `make_default_executor` imports `agent_harness.tools` but never calls `register_builtin_tools` → memory tools absent from chat executor.
- **D3 (content) — drift correction**: `register_builtin_tools` registers memory but **NOT** subagent tools. A-1 (memory) and A-3a (subagent) do NOT share one call → A-3a budgeted a SEPARATE `make_task_spawn_tool` registration. Scope shift < 20% → continue (recorded in plan §0, not silently rewritten).
- **D4/D5**: `loop.py:196` ctor has `prompt_builder`; `:881` true-branch does the work; `handler.py:220-239` omitted `prompt_builder=` → fallback always taken.
- **D6 (AP-2 false-green)**: `check_promptbuilder_usage.py` root = `agent_harness` → never scans the chat handler.
- **D8 (schema/contract)**: `SubagentResultReducer` referenced but absent from `_contracts/subagent.py` → resolve define-vs-reuse on Day 2.

**Go/no-go**: GO. Branch created.

## Day 1 — Shared surface + Cat 5 (keystone) — commit `487432a9`

- Extended `make_default_executor` opt-in params (memory deps + dispatcher + parent_session_id, all default None → byte-identical 55.2 registry when absent).
- Added `make_chat_prompt_builder(chat_client)` to `_category_factories.py` (returns `DefaultPromptBuilder` with `MemoryRetrieval` + `InMemoryCacheManager` + `TiktokenCounter(gpt-4o)`).
- `build_real_llm_handler` passes `prompt_builder=` into `AgentLoopImpl(...)` → chat path reaches `loop.py:881` true-branch.
- Flipped `check_promptbuilder_usage.py` false-green → true-green (path-targeted AST positive check on the chat call-site; regresses if kwarg removed).
- NEW `test_chat_keystone_wiring.py` — 3 Cat 5 tests (injection completeness AP-4 / PromptBuilt-on-SSE / negative). **3 passed.**

## Day 2 — Cat 3 Memory + Cat 11 Subagent — commit `1701b4e4`

- `make_default_executor` opt-in: memory deps → `register_builtin_tools(...)` (REAL handlers, `is not memory_placeholder_handler` AP-4 guard); dispatcher → `task_spawn` (FORK/TEAMMATE) + one `agent_researcher` AS_TOOL (HANDOFF excluded).
- Added `_adapt_subagent_handler` (Cat 11 `(dict)->dict` ↔ Cat 2 `(ToolCall)->str` bridge) in the **registration layer** — keeps Cat 11/Cat 2 owners decoupled (no cross-category hashing).
- Added `make_chat_memory_deps(db)` (5-scope layers, tenant-scoped per-call via `ExecutionContext`) + `make_chat_subagent_dispatcher(...)` (per-request DI).
- `handler.py`/`router.py` thread `user_id`.
- 17.md: `task_spawn` risk_level = SEQUENTIAL/AUTO/MEDIUM; `SubagentResultReducer` resolved as **REUSE** (handler merges internally; no new contract).
- Tests +7 (Cat 3 ×4: real-handler / memory exec / cross-tenant isolation / negative; Cat 11 ×3: FORK spawn+merge / fail_soft / negative). **10 passed.**

Both Day 1 + Day 2 were implemented by sequential `code-implementer` agent delegation, then **independently re-verified** by the parent (re-ran tests + mypy + lints — not relying on the agent's self-report).

## Day 3 — Cross-cutting Tests + lint true-green + real_llm e2e

- NEW `test_combined_all_three_active_one_run` — one chat SSE run: PromptBuilt (Cat 5) + memory_write→memory_search round-trip (Cat 3) + FORK task_spawn merge (Cat 11), proving all three are simultaneously wired by `build_real_llm_handler`. Keystone file 10 → **11 passed**.
- `check_promptbuilder_usage` true-green confirmed (Day 1).
- **🚧 real_llm live e2e leg deferred** (confirmatory): PromptBuilt-on-chat-SSE proven deterministically by mock tests (primary gate); clean HTTP-level PromptBuilt assertion blocked by A-5 (LoopEvent→SSE surfacing) OUT of scope; live path already verified in C-11 (`64f29259`); Azure cost + `cost_ledger Δ≥2` FIX-024 known-red on gpt-5.2.
- LLM SDK leak 0 / mypy src 0/319 / 9/9 V2 lints confirmed.

## Day 4 — Closeout

- Full validation sweep: **pytest 1934 passed / 4 skipped** (+11 keystone tests this sprint); `mypy src/` 0/319; `python scripts/lint/run_all.py` 9/9 green; frontend untouched; LLM SDK leak 0.
- CHANGE-032 + this progress.md + retrospective.md + calibration matrix data point + Area-A capstone update.
- Commit Day 3+4 + push + PR (user-authorized).

## Commit ↔ checklist mapping

| Commit | Checklist |
|--------|-----------|
| `f0874f35` (PR #225) | plan + checklist + FIX-024 |
| `487432a9` | Day 1 §1.1 (partial) + §1.2 (Cat 5) + Day 3 lint flip |
| `1701b4e4` | Day 1 §1.1 (make_default_executor + 3 factories) + Day 2 §2.1 (Cat 3) + §2.2 (Cat 11) |
| (Day 3+4 commit) | Day 3 combined test + Day 4 closeout docs |
