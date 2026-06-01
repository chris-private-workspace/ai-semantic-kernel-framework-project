# CHANGE-032: Chat-path keystone wiring — Cat 5 PromptBuilder + Cat 3 memory tools + Cat 11 subagent tools (A-3a)

**Date**: 2026-06-01
**Sprint**: 57.64
**Scope**: cross-category activation at the `api/v1/chat` + `business_domain` factory layer — Cat 5 (Prompt Construction) + Cat 3 (Memory) + Cat 11 (Subagent Orchestration); **no `loop.py` edits**
**Status**: ✅ Shipped (feature branch `feature/sprint-57-64-chat-path-keystone-wiring`; PR pending)

---

## Problem

Three Area-A capabilities were **built but not connected to the production `real_llm` chat loop** (Area-A integration sequencing capstone, 2026-05-31; Day-0 repo verify D1-D8):

1. **Cat 5 (KEYSTONE)** — `AgentLoopImpl.__init__` exposes `prompt_builder` (`loop.py:196`) and the structured build true-branch lives at `loop.py:881`, but `build_real_llm_handler` (`handler.py`) omitted `prompt_builder=` from the ctor call → `self._prompt_builder is None` → the **naked fallback path was ALWAYS taken** on the chat flow. This also blocks downstream A-1 Tier2 auto-inject, half of Cat 4 prompt caching, and A-5c diagnostic visibility.
2. **Cat 3 (memory tools)** — `make_default_executor` (`business_domain/_register_all.py`) registered only echo + 18 business tools; it never called `register_builtin_tools`, so `memory_search`/`memory_write` (and sandbox/web/approval) were **absent from the chat executor**.
3. **Cat 11 (subagent tools, A-3a)** — FORK/TEAMMATE/AS_TOOL executors work (`subagent/dispatcher.py:91`) and `make_task_spawn_tool` exists (`subagent/tools.py:51`), but none were **registered on the chat executor**.

A secondary AP-2 false-green: `check_promptbuilder_usage.py` scans root `agent_harness` only — the chat handler is OUTSIDE that root → never scanned → the missing `prompt_builder=` was undetectable by lint.

## Root Cause / Background

The bottleneck was **"built and not connected to the loop"**, not "not built". Every loop dependency is already a `is not None`-gated ctor param, so activation is a pure api/factory-layer wiring change. Day-0 drift D3 corrected the capstone premise: A-1 (memory) and A-3a (subagent) do **not** share one `register_builtin_tools` call — `register_builtin_tools` registers memory but NOT subagent tools, so A-3a needs a **separate** registration of `make_task_spawn_tool` + an AS_TOOL wrapper. The bundle stayed coherent (same files, no `loop.py`), but it is "one change surface, two registration calls".

## Solution

All changes at the api/factory layer; `agent_harness/**` stays SDK-import-clean (LLM-provider neutral).

- **`business_domain/_register_all.py`** — extended `make_default_executor` with opt-in, backward-compatible deps (`memory_retrieval` + `memory_layers` + `subagent_dispatcher` + `parent_session_id`, all default `None`; byte-identical to the 55.2 echo+18-business-tools registry when absent). When memory deps present → `register_builtin_tools(...)` wires the **REAL** `memory_search`/`memory_write` handlers (AP-4 Potemkin guard: asserted `is not memory_placeholder_handler`). When dispatcher present → registers `task_spawn` (FORK/TEAMMATE) + one `agent_researcher` AS_TOOL wrapper (HANDOFF excluded — hollow stub). Added a thin `_adapt_subagent_handler` (Cat 11 `(dict)->dict` ↔ Cat 2 `(ToolCall)->str` bridge) in the **registration layer** so the two category owners stay decoupled (no cross-category hashing).
- **`api/v1/chat/_category_factories.py`** — added `make_chat_prompt_builder(chat_client)` (returns `DefaultPromptBuilder` with `MemoryRetrieval` + `InMemoryCacheManager` + `TiktokenCounter`), `make_chat_memory_deps(db)` (5-scope layers, tenant-scoped per-call via `ExecutionContext`), `make_chat_subagent_dispatcher(...)` (per-request DI). Mirrors the existing `make_chat_*` pattern (57.63).
- **`api/v1/chat/handler.py`** — `build_real_llm_handler` now passes `prompt_builder=` into `AgentLoopImpl(...)` and threads the memory deps + dispatcher + `user_id` into `make_default_executor`.
- **`api/v1/chat/router.py`** — threads `user_id` (alongside 57.63's tenant_id/db/session_id).
- **`scripts/lint/check_promptbuilder_usage.py`** — added a path-targeted AST positive check asserting the chat call-site passes `prompt_builder=` (flips the AP-2 false-green to true-green; regresses if the kwarg is removed).
- **`17-cross-category-interfaces.md`** — set `task_spawn` risk_level (SEQUENTIAL/AUTO/MEDIUM); resolved `SubagentResultReducer` as **REUSE** (the handler merges `SubagentResult` internally — no new contract).
- **`backend/tests/integration/api/test_chat_keystone_wiring.py`** (NEW, 11 tests) — Cat 5 injection completeness (AP-4) + PromptBuilt-on-SSE + negative; Cat 3 real-handler + memory exec + cross-tenant isolation + negative; Cat 11 FORK spawn+merge + fail_soft + negative; **combined all-three-active-in-one-run** (Day 3).

## Verification

- `test_chat_keystone_wiring.py` — **11 passed** (10 per-cat + 1 combined).
- Cross-tenant isolation is a true strong-isolation assertion: tenant-B `memory_search` over the same `session_id` returns `[]` for a tenant-A write (composite `(tenant_id, session_id)` key).
- `subagent`/`loop` suites — HANDOFF stub tests still assert `HANDOFF_NOT_IMPLEMENTED` (A-3a excludes HANDOFF; unchanged).
- Full sweep: **pytest 1934 passed / 4 skipped**; `mypy src/` **0 issues / 319 files**; `python scripts/lint/run_all.py` **9/9 green** (incl. `check_promptbuilder_usage` true-green + `check_llm_sdk_leak` 0); frontend untouched.
- `real_llm` live e2e leg **deferred (confirmatory)** — PromptBuilt-on-chat-SSE is proven deterministically by the mock integration tests (the plan's primary gate); a clean HTTP-level PromptBuilt assertion is blocked by A-5 (LoopEvent→SSE surfacing) being out of scope; the live real_llm path was already exercised end-to-end in C-11 (`64f29259`); re-running incurs Azure cost and the `cost_ledger Δ≥2` assertion is FIX-024 known-red on gpt-5.2.

## Impact

- **Runtime**: the production `real_llm` chat path now (a) builds prompts through the structured `PromptBuilder` (centralized assembly, memory-injectable — AP-8) instead of the naked fallback, (b) exposes `memory_search`/`memory_write` (tenant-scoped), and (c) can spawn FORK/TEAMMATE/AS_TOOL subagents. This unblocks 候選 Sprint B (A-1 Tier2 memory auto-inject + A-2 Tier2 prompt caching — both touch `loop.py`).
- **Scope**: backend + lint script + docs only; no frontend, no DB migration (memory tables + subagent ORM already existed). No `loop.py` edits.
- **Out of scope (unchanged)**: A-3b Cat 11 HANDOFF (hollow executor — separate spike); A-1/A-2 Tier2 (loop.py — 候選 Sprint B); A-4/A-5/A-6 (tracer / events→SSE / frontend real-data).
- **Follow-ups noted in retrospective** (small, not blocking): `TiktokenCounter` hard-codes `gpt-4o` while the live deployment is gpt-5.2 (ties to FIX-024 pricing drift); `make_chat_memory_deps(db)` accepts then discards `db` (session-scope only for now); the AS_TOOL wrapper hard-codes a single `agent_researcher` role.
