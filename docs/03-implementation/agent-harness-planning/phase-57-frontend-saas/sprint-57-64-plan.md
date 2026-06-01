# Sprint 57.64 Plan — Chat-Path Keystone Wiring (Cat 5 PromptBuilder + Cat 3 Memory Tools + Cat 11 Subagent Tools)

**Purpose**: Wire the three "built-but-not-connected-to-loop" Area-A capabilities into the production `real_llm` chat path: inject Cat 5 `PromptBuilder` (the keystone — fallback path is currently always taken), register Cat 3 memory tools (currently absent from the chat executor), and register Cat 11 FORK/TEAMMATE/AS_TOOL subagent tools (A-3a; HANDOFF/A-3b is OUT). All changes live in the api/factory layer — **no `loop.py` edits** (every dep is already a `is not None`-gated loop param). Prove each fires on the chat SSE flow; close the AP-2 false-green lint; validate via a `real_llm` e2e (gated on C-11 secrets).
**Category / Scope**: Cat 5 + Cat 3 + Cat 11(A-3a) activation on api/v1/chat boundary; Phase 57.64
**Created**: 2026-06-01
**Status**: Draft (pending user scope approval; code execution gated)
**Source**: `claudedocs/5-status/area-a-integration-sequencing-capstone-20260531.md` (候選 Sprint A) + `cat5-promptbuilder-loop-injection-analysis-20260531.md` (A-2) + `cat3-memory-loop-injection-analysis-20260531.md` (A-1) + `cat11-handoff-loop-injection-analysis-20260531.md` (A-3) + Day-0 repo verify (researcher, D1-D8)

> **Modification History**
> - 2026-06-01: Initial creation — 候選 Sprint A keystone bundle; folds Day-0 drift D1-D8 (esp. D3 — A-1/A-3a do NOT share one function) into §0 + §8

---

## 0. Background

This sprint is the direct follow-up named OUT-of-scope by Sprint 57.63 §9 ("Cat 5 PromptBuilder + Cat 11 … on the chat path — not in this sprint; can be a follow-up activation sprint"). The Area-A sequencing capstone elects it as **候選 Sprint A (首發)** because it has the highest unlock value while touching no `loop.py` internals.

The bottleneck is not "not built" but "built and not connected to the loop". Day-0 repo verify (researcher) confirmed:

- **A-2 / Cat 5 (KEYSTONE)** — `AgentLoopImpl.__init__` already exposes `prompt_builder` (`loop.py:196`), and the true-branch at `loop.py:881` does the work; but `build_real_llm_handler` (`handler.py:155-249`) omits `prompt_builder=` from the ctor call (`:220-239`), so `self._prompt_builder is None` → the fallback path is **always** taken (D4, D5). Its downstream (A-1 Tier2 auto-inject, half of Cat 4 prompt caching, A-5c diagnostic visibility) all unblock once this lands.
- **A-1 / Cat 3 (memory tools)** — `make_default_executor` (`backend/src/business_domain/_register_all.py:128-182`) registers only `ECHO_TOOL_SPEC` + business tools; it imports `agent_harness.tools` (L40) but **never calls `register_builtin_tools`** (D2). So memory tools (and also sandbox/web/approval) are absent from the chat executor.
- **A-3a / Cat 11 (subagent tools)** — FORK/TEAMMATE/AS_TOOL executors work (`subagent/dispatcher.py:91`); the tools `make_task_spawn_tool`/`make_handoff_tool` live in `agent_harness/subagent/tools.py:51/:128`; none are registered on the chat executor. Routes via the Cat 2 tool registry (handler closes over the dispatcher) — **no loop.py change**.

### ⚠️ Day-0 drift correction (D3) — folded from capstone premise

The capstone framed A-1T1 and A-3a as "two beneficiaries of the SAME `register_builtin_tools` gap". **Repo verify shows this is only partly true**: `register_builtin_tools` (`agent_harness/tools/__init__.py:56-120`) registers echo+sandbox+web+approval+**memory** but **NOT** subagent tools. The truly shared element is "`make_default_executor` does not accept opt-in deps / does not register builtin tools" — A-1T1 is one `register_builtin_tools(...)` call; **A-3a needs a SEPARATE registration** of `make_task_spawn_tool(...)` + AS_TOOL wrappers. The bundle remains coherent (all three edit the same files: `_register_all.py` + new `_category_factories.py` factories + `handler.py`, none touch `loop.py`), but it is "one change surface, two registration calls", not "one call feeds both". Scope shift < 20% → continue (per §Step 2.5 go/no-go); recorded here, not silently rewritten.

---

## 1. Sprint Goal

Activate Cat 5 PromptBuilder, Cat 3 memory tools, and Cat 11 FORK/TEAMMATE/AS_TOOL subagent tools on the production `real_llm` chat path by extending the api/factory layer (`make_default_executor` opt-in deps + new `make_chat_*` factories + `build_real_llm_handler` injection), with integration tests proving each fires on the chat SSE flow, the `check_promptbuilder_usage` lint flipped from false-green to true-green, and a `real_llm` e2e proving the wired flow. **No `loop.py` edits.** LLM-provider neutrality preserved: all deps constructed at the api/adapter layer; `agent_harness/**` stays SDK-import-clean.

---

## 2. User Stories

- **US-1 (Cat 5 PromptBuilder — KEYSTONE)** — As a platform owner, I want the production chat path to build prompts through the structured `PromptBuilder` (with memory layers) instead of the naked fallback, so prompt assembly is centralized and memory-injectable (AP-8). → new `make_chat_prompt_builder(chat_client, memory_provider=None)`; `handler.py:220` passes `prompt_builder=` (+ `memory_provider`) into `AgentLoopImpl(...)`.
- **US-2 (Cat 3 Memory tools)** — As an operator, I want the agent to have on-demand memory tools (`memory_search`/`memory_save`) on the chat path, so it can recall and persist tenant-scoped context. → new `make_chat_memory_deps(db, tenant_id, user_id)`; extend `make_default_executor` to call `register_builtin_tools(registry, handlers, memory_retrieval=…, memory_layers=…)`.
- **US-3 (Cat 11 Subagent tools — A-3a)** — As a platform owner, I want the agent to spawn FORK/TEAMMATE/AS_TOOL subagents on the chat path, so multi-agent decomposition works on the main flow. → new `make_chat_subagent_dispatcher(chat_client, …)`; register `make_task_spawn_tool(dispatcher, parent_session_id=…)` + AS_TOOL wrappers into the executor registry. HANDOFF excluded.
- **US-4 (Validation + lint true-green)** — As a reviewer, I want integration tests proving each capability fires on the chat SSE path (+ multi-tenant scoping + negative "turned-off" tests), the `check_promptbuilder_usage` lint detecting the chat call-site, and a `real_llm` e2e, so "wired" is true at runtime, not just in isolated tests.

---

## 3. Technical Specifications

### 3.0 Shared change surface (prerequisite for US-1/2/3)
- **`make_default_executor`** (`backend/src/business_domain/_register_all.py:128-182`) — extend to accept opt-in deps (memory deps, subagent dispatcher) and, when present, call `register_builtin_tools(...)` (memory) + register subagent tools. Keep current behavior when deps absent (backward-compatible default).
- **New `make_chat_*` factories** in `backend/src/api/v1/chat/_category_factories.py` (file already exists from 57.63; ADD functions) — mirror the existing `make_chat_compactor` (`:71`) / `make_chat_state_deps` (`:87`) / `make_chat_error_deps` (`:105`) / `make_chat_verifier_registry` (`:134`) pattern exactly (D8). New: `make_chat_prompt_builder`, `make_chat_memory_deps`, `make_chat_subagent_dispatcher`. LLM-neutral: adapter passed as `ChatClient` ABC; no SDK import in `agent_harness/**`.
- **Threading**: `user_id` must reach `make_chat_memory_deps` — `get_current_user_id` already available in router scope; thread alongside the `tenant_id`/`db`/`session_id` plumbing 57.63 already added.

### 3.1 Cat 5 PromptBuilder (US-1)
- `PromptBuilder` + `DefaultPromptBuilder` already built. Loop true-branch: `loop.py:881` (reached only when `self._prompt_builder is not None`).
- `make_chat_prompt_builder(chat_client, memory_provider=None)` → `DefaultPromptBuilder(...)`; pass into `AgentLoopImpl(prompt_builder=…, memory_provider=…)` at `handler.py:220-239`.
- 1 new factory + 1 ctor kwarg; no loop.py change. 17.md §2.1 PromptBuilder contract.

### 3.2 Cat 3 Memory tools (US-2)
- `register_builtin_tools` (`agent_harness/tools/__init__.py:56-120`) registers memory tools when memory deps provided; **AP-4 caveat**: it falls back to `memory_placeholder_handler` (`:117-120`) — must wire the REAL retrieval/layers, assert the real handler (not the stub).
- `make_chat_memory_deps(db, tenant_id, user_id)` builds the memory provider/retrieval + layers (tenant-scoped per multi-tenant 鐵律).
- `make_default_executor` threads these into `register_builtin_tools(...)`.

### 3.3 Cat 11 Subagent tools — A-3a (US-3)
- `make_chat_subagent_dispatcher(chat_client, …)` constructs the dispatcher (FORK/TEAMMATE/AS_TOOL executors at `subagent/dispatcher.py:91`).
- Register `make_task_spawn_tool(dispatcher, parent_session_id=…)` (`subagent/tools.py:51`) + AS_TOOL wrappers into the executor registry; handler closes over the dispatcher → routes via `loop.py:1141` `tool_executor.execute`. **No loop.py change.**
- **EXCLUDE** `make_handoff_tool` — HANDOFF executor is a hollow uuid4 stub (`subagent/modes/handoff.py:37-62`) and the loop HANDOFF branch terminates with `HANDOFF_NOT_IMPLEMENTED` (`loop.py:1051-1058`). A-3b is OUT (§9).
- **Day-0 unknown**: `SubagentResultReducer` is referenced but absent from `_contracts/subagent.py` (`SubagentResult`/`SubagentBudget` already defined, 17.md :64-65). Resolve (define or use existing merge) on Day 0/2.

### 3.4 Lint true-green + validation (US-4)
- `scripts/lint/check_promptbuilder_usage.py` default root is `backend/src/agent_harness` (`:152`); the chat handler is OUTSIDE that root → never scanned → **false-green** (D6, AP-2). Add a POSITIVE check: assert the chat call-site passes `prompt_builder=` (extend lint root or add a targeted assertion). A passing lint must regress if the kwarg is removed.
- Integration tests assert `PromptBuilt` / memory `ToolCallExecuted` / subagent FORK spawn-and-merge on the chat SSE path; each with a NEGATIVE "deps removed → capability absent" guard (AP-4).
- `real_llm` e2e proves the wired flow (gated on C-11 secrets — see §8).

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/_category_factories.py` | ADD `make_chat_prompt_builder` / `make_chat_memory_deps` / `make_chat_subagent_dispatcher` (mirror existing `make_chat_*` pattern) |
| `backend/src/business_domain/_register_all.py` | extend `make_default_executor` to accept opt-in memory deps + subagent dispatcher; call `register_builtin_tools(...)` (memory) + register `task_spawn`/AS_TOOL subagent tools when present |
| `backend/src/api/v1/chat/handler.py` | pass `prompt_builder=` (+ `memory_provider`) into `AgentLoopImpl(...)`; thread `user_id`; pass memory deps + dispatcher into the executor factory |
| `backend/src/api/v1/chat/router.py` | thread `user_id` (alongside 57.63's tenant_id/db/session_id) into the handler/executor build |
| `backend/src/agent_harness/_contracts/subagent.py` | define `SubagentResultReducer` if absent (Day-0 confirm) — 17.md single-source |
| `scripts/lint/check_promptbuilder_usage.py` | flip false-green → true-green: detect the chat handler call-site passes `prompt_builder=` |
| `backend/tests/integration/api/test_chat_keystone_wiring.py` | **NEW** — assert `PromptBuilt` (Cat 5) / memory tool exec (Cat 3) / subagent FORK (Cat 11) on chat SSE path + multi-tenant scoping + negative turned-off guards |
| `backend/tests/integration/api/test_chat_e2e_real_llm.py` (or e2e workflow) | extend — `real_llm` e2e of the wired flow |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | set `task_spawn` risk_level (row :165); register `SubagentResultReducer` if newly defined (§near :64-65) |
| `claudedocs/4-changes/feature-changes/CHANGE-0XX-chat-path-keystone-wiring.md` | change record |

**No DB migration** (memory tables + subagent ORM already exist) — confirm Day-0 Prong-3.

---

## 5. Acceptance Criteria

- `build_real_llm_handler` passes `prompt_builder=` (+ `memory_provider`) into `AgentLoopImpl`; `make_default_executor` registers memory tools (real handler, not the placeholder stub) + FORK/TEAMMATE/AS_TOOL subagent tools when deps present.
- Integration tests prove on the chat SSE path: `PromptBuilt` emitted (Cat 5, fallback NOT taken); a `memory_search`/`memory_save` `ToolCallExecuted` (Cat 3); a FORK subagent spawn + `SubagentResult` merge (Cat 11). Memory + subagent scoped by `tenant_id` (cross-tenant isolation test). Each capability has a NEGATIVE test (deps removed → capability absent, agent still runs).
- `check_promptbuilder_usage` lint is true-green: passes now, FAILS if `prompt_builder=` is removed from the chat call-site.
- `real_llm` e2e: one benign multi-turn Azure run reaches END_TURN with a `PromptBuilt` event in the stream (gated on C-11 secrets being set).
- All existing tests green; `mypy --strict` clean; 9/9 V2 lints (incl. **LLM SDK leak 0** — `agent_harness/**` no `import openai/anthropic`); frontend untouched; HANDOFF stub tests (`test_handoff.py`, `test_loop.py:311-330`) still assert `HANDOFF_NOT_IMPLEMENTED` (unchanged — A-3a excludes HANDOFF).

---

## 6. Deliverables

- [ ] 3 new `make_chat_*` factories (LLM-neutral, mirror existing pattern)
- [ ] `make_default_executor` opt-in deps + memory tool registration (US-2)
- [ ] Cat 5 PromptBuilder injected + tested on chat path (US-1, keystone)
- [ ] Cat 11 FORK/TEAMMATE/AS_TOOL subagent tools registered + tested (US-3; HANDOFF excluded)
- [ ] `SubagentResultReducer` resolved (define or reuse) + 17.md updated
- [ ] `check_promptbuilder_usage` lint flipped to true-green (AP-2)
- [ ] integration test (3 capabilities + multi-tenant + negative guards) + real_llm e2e
- [ ] CHANGE record + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: `medium-backend` (0.80). **Agent-delegated: TBD-Day-1-decision** (resolve at Day 1 start; likely `yes` → `mechanical-greenfield-design-decisions` 0.65 given the new factory + registration design + `SubagentResultReducer` decision).

> Bottom-up est ~13 hr → class-calibrated commit ~10.5 hr (mult 0.80) → agent-adjusted commit TBD (apply `agent_factor` sub-class per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` if Day-1 = `yes`).

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D3 drift**: A-1/A-3a do NOT share one `register_builtin_tools` call (subagent tools are a separate module) | Plan §0 corrected; A-3a budgets a separate registration call; bundle stays coherent (same files, no loop.py) |
| **D1 path**: `make_default_executor` is at `business_domain/_register_all.py`, NOT under `agent_harness/` | File Change List cites real path; it's a sibling package |
| **D6 / AP-2 false-green lint**: `check_promptbuilder_usage` never scans the chat handler (root = `agent_harness`) | US-4 adds a POSITIVE assertion that regresses on kwarg removal — lint alone cannot catch it |
| **AP-4 Potemkin (memory)**: `register_builtin_tools` falls back to `memory_placeholder_handler` | Wire REAL retrieval/layers; integration test asserts the real handler + negative "no deps → not registered" |
| **AP-4 Potemkin (subagent)**: HANDOFF is a hollow stub | EXCLUDE `make_handoff_tool`; keep stub tests asserting `HANDOFF_NOT_IMPLEMENTED`; A-3b deferred (§9) |
| **`SubagentResultReducer` undefined contract** | Day-0 resolve: define in `_contracts/subagent.py` (17.md single-source) or reuse existing `SubagentResult` merge |
| **real_llm acceptance gated on C-11** | C-11 (3 Azure secrets) must be set before the `real_llm` e2e leg; mock integration tests are the primary gate; e2e is confirmatory |
| **LLM-neutrality** (Risk: SDK into agent_harness) | Construct PromptBuilder/memory/dispatcher with the adapter via `ChatClient` ABC at api layer; `check_llm_sdk_leak` gates |
| **Module-level singleton test isolation** (Risk Class C) | autouse reset fixtures per `.claude/rules/testing.md` §Module-level Singleton Reset |
| Day-0 unknowns: `SubagentResultReducer`; memory dep ctor shapes; no-new-migration | Day-0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema) before Day 1 |

---

## 9. Out of Scope

- **A-3b Cat 11 HANDOFF** — hollow executor + missing platform session-boot; needs a design spike + design note (8-point gate). Separate sprint.
- **A-1 Tier2 (memory auto-inject)** + **A-2 Tier2 (prompt caching)** — these touch `loop.py`; next sprint (候選 Sprint B).
- **A-4 loop tracer / A-5 events→SSE / A-6 frontend real-data** — independent Area-A items; separate sprints per the capstone.
- **B-area (budget/verification correctness) / C-area** — outside Area A.
