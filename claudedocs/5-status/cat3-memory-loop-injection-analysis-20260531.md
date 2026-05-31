# A-1 Deep Analysis: Cat 3 Memory — Injection into the Agent Loop

**Purpose**: Single-point deep analysis of why the agent never uses memory during reasoning, and exactly what it takes to wire Cat 3 Memory into the production chat loop. Analysis only — not an implementation plan.
**Category / Scope**: 範疇 3 (Memory) / cross-cutting wiring / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for a future sprint)

> **Modification History**
> - 2026-05-31: Initial creation — A-1 of the Area-A wiring-gap deep-analysis series; 2-agent parallel audit (current-code-truth + planning-target)

> **Related**
> - `integration-progress-20260531.md` — parent integration snapshot (Area A item 1)
> - `01-eleven-categories-spec.md §範疇3` — Cat 3 target spec
> - `17-cross-category-interfaces.md §3.1 / §4.1` — Memory tool + MemoryAccessed event contracts
> - `10-server-side-philosophy.md §原則3` — lead-then-verify anti-hallucination principle

---

## 0. Headline

This is **not "add one wire" — it is "add three wires, and two of them are blocked on A-2 (Cat 5 PromptBuilder)"**. The Cat 3 store is complete (Level 3). What is missing is loop-injection, and injection splits into **two independent tiers**, of which only Tier 1 can be shipped on its own.

---

## 1. Current state — store complete, all three loop wires cut

| Component | Status | Evidence |
|-----------|--------|----------|
| Memory store (5 scope × 3 timescale) | ✅ complete | `memory/_abc.py:46` (`MemoryScope`) / `:56` (`MemoryTimeScale`) / `:69` (`MemoryLayer` ABC); 5 layer impls (`system/tenant/role/user/session_layer.py`); `conflict_resolver.py` (4 rules); `retrieval.py` fan-out |
| `MemoryHint` contract (`verify_before_use` / `confidence` / `time_scale` / `last_verified_at` / `source_tool_call_id`) | ✅ | `_contracts/memory.py:51` |
| `memory_search` / `memory_write` ToolSpec + real handlers | ✅ exist | `tools/memory_tools.py:122` / `:160` (specs) / `:232` / `:270` (handler factories) |
| REST `/api/v1/memory/*` (3 GET, read-only) | ✅ exists | `api/v1/memory.py:243` / `:298` / `:351`; gated by `require_audit_role` |
| DB 5 tables + tenant_id + RLS | ✅ | `infrastructure/db/models/memory.py` (`memory_system/tenant/role/user/session_summary`) |
| **Memory tools registered in chat executor** | ❌ **cut wire 1** | `make_default_executor` (`business_domain/_register_all.py:128`) registers 18 business tools + `echo_tool` but **never calls** `register_builtin_tools(memory_retrieval=, memory_layers=)` (`tools/__init__.py:56`) |
| **Per-turn auto-inject of L1-L4 summary (<2K token)** | ❌ **cut wire 2** | auto-inject happens inside `PromptBuilder.build()`; but `build_real_llm_handler` does not pass `prompt_builder=` → `self._prompt_builder=None` (`handler.py:155-249`, `loop.py:881` guard) |
| **`verify_before_use` rules injected into system prompt** | ❌ **cut wire 3** | the rules are injected by PromptBuilder (`01.md §範疇3`: "由範疇 5 PromptBuilder 注入 system prompt"); no PromptBuilder → does not exist |
| `AgentLoopImpl` has a memory param | ❌ no injection site | ctor has 24 params (`loop.py:184-218`), none for memory |

**Net effect**: during reasoning the agent **cannot touch memory at all** — it can neither call `memory_search` (tool not registered in the chat executor) nor see a memory summary in its prompt (no PromptBuilder). The REST endpoint uses a **separate ORM-direct path** (`memory.py`, Sprint 57.12 Option B bypassing the ABC) that the loop never traverses.

---

## 2. Key finding — Cat 3 injection is two tiers; Tier 2 is blocked on A-2

The plan defines "Cat 3 live in the loop" as **two mechanisms** (`01.md §範疇3 工具驗收` + `17.md §3.1`):

| Tier | Mechanism | Depends on | Independently shippable |
|------|-----------|-----------|------------------------|
| **Tier 1** | **on-demand**: LLM calls `memory_search` / `memory_write` (via Cat 2 Registry) | Cat 2 (live) + memory tools registered | ✅ **yes** (no Cat 5 needed) |
| **Tier 2** | **auto-inject**: each turn injects an L1-L4 summary (<2K token) into the prompt + injects `verify_before_use` lead-then-verify rules into the system prompt | **requires Cat 5 PromptBuilder** (`02.md §約束5` "Loop must use PromptBuilder") | ❌ **blocked on A-2** |

> **This overturns the premise that the 6 Area-A items are independent**: the FULL version of A-1 (Cat 3) ⊂ A-2 (Cat 5). Tier 2 auto-inject AND the verify_before_use anti-hallucination mechanism both flow through PromptBuilder — neither is possible without A-2.

This also matches the planned sprint sequence: Sprint 51.2 brought Cat 3 to **Level 3** (tools + 5 layers; on-demand only), with full per-turn auto-inject explicitly waiting on Cat 5 (Sprint 52.2 in the plan — which never activated in the production chat path).

---

## 3. Target design recap (from `01.md §範疇3`, `17.md §3.1/§4.1`, `10.md §原則3`)

- **Data model**: 5 scope (system/tenant/role/user/session) × 3 timescale (short_term=Redis / long_term=PostgreSQL / semantic=Qdrant). `MemoryHint` = clue not fact.
- **Read**: BOTH per-turn auto-inject (L1-L4 summary <2K tokens, via PromptBuilder, prompt-cacheable via Cat 4 `cache_memory_layers`) AND on-demand `memory_search(query, layers, time_scales, top_k)`.
- **Write**: BOTH LLM-initiated `memory_write` (system scope rejected) AND background extraction worker (L5 session → L4 user at session end, SLA < 60s; auto-trigger deferred).
- **lead-then-verify**: when `verify_before_use=True`, agent MUST verify the hint against live state before acting; correct via `memory_write` on mismatch. Anti-hallucination for stale multi-tenant memory.
- **Observable signal of "live"**: a chat turn emits `MemoryAccessed` (scope / time_scale / confidence / verify_before_use / tenant_id); `PromptBuilt.layer_metadata.memory_layers_used` non-empty; memory written in session N retrievable in session N+1 for same user/tenant.
- **Prerequisite chain**: Cat 2 (tools) → Cat 3 (layers+tools) → Cat 5 (auto-inject + verify rules) ; + Cat 4 (cache) + Cat 12 (trace/MemoryAccessed).

---

## 4. Integration design (concrete landing points)

### Tier 1 (shippable now; ~1 sprint, medium-backend)
1. New factory `make_chat_memory_deps(db, tenant_id, user_id) → (MemoryRetrieval, dict[str, MemoryLayer])` in `api/v1/chat/_category_factories.py` (api layer, **LLM-neutral** — memory layers do not touch ChatClient, satisfying constraint 3).
2. Extend `make_default_executor` to accept memory deps and internally call `register_builtin_tools(registry, memory_retrieval=…, memory_layers=…)` (reuse existing real handlers).
3. Thread `db` / `tenant_id` / **`user_id`** down through the handler. Cat 7 (57.63) already threads `db`/`session_id`/`tenant_id`; **`user_id` is the new thread** (`get_current_user_id` already exists — used in tests).
4. Follow Cat 7's **all-or-nothing graceful degradation**: no deps → memory tools not registered → agent runs normally (like echo_demo).
5. (optional) Add a `MemoryAccessed` SSE event to `sse.py` (currently 14 events, none for memory) → frontend can show memory usage.
6. Integration test: a real `AgentLoopImpl.run()` actually invokes `memory_search`/`memory_write` (today's `test_memory_tools_integration.py` calls handlers directly, **not via the loop**).

### Tier 2 (bundle with A-2 Cat 5)
- `make_chat_prompt_builder(memory_layers, …)` injects the L1-L4 summary (<2K cap) + lead-then-verify system-prompt rules, and `prompt_builder=` is passed to `AgentLoopImpl`. This IS the A-2 work; Cat 3 Tier 2 is a consumer of it.

---

## 5. Risks / open research questions

1. **AP-10 mock-vs-real divergence**: REST reads ORM directly; loop tools use `MemoryLayer.read()` ABC — two read paths to the same tables. Reconcile, or at minimum document, or a bug fixed on one path won't surface on the other.
2. **MemoryLayer session lifecycle**: layers need the request's tenant-scoped DB session + RLS context (same pattern as Cat 7 `DBCheckpointer`). Confirm read/write are async + accept `trace_context`.
3. **semantic timescale (Qdrant) is a Sprint 51.2 stub**: `time_scales=["semantic"]` may be incomplete. Recommend Tier 1 supports `long_term` only first.
4. **role/session layers return 501 in REST** (Phase 58+) while all 5 layer impls exist — the loop tools must be consistent with REST on which scopes are exposed.
5. **<2K token cap enforcement point** (Tier 2, inside PromptBuilder) + **memory-layer prompt caching** (Cat 4 `cache_memory_layers`, optimization).
6. **Extraction worker auto-trigger** (session-end L5→L4) is still manual (Celery deferred) — related but independently scoped.

---

## 6. Recommendation

- **Sequencing**: because the full Cat 3 is blocked on Cat 5, the next analysis should be **A-2 (Cat 5 PromptBuilder)**, then land Cat 3 Tier 2 together with Cat 5. **Cat 3 Tier 1 (on-demand tools) can ship first as an independent, low-risk sprint**, giving the agent at least the ability to actively search/write memory.
- **Area-A real dependency graph**: `A-2 → (A-1 Tier 2)`; while `A-1 Tier 1` / A-3 / A-4 / A-5 / A-6 are relatively independent.

---

## 7. Definition-of-done signals (for the eventual sprint)

- **Tier 1**: a loop run emits a `ToolCallExecuted` for `memory_search`; `memory_write` in session N → `memory_search` retrieves it in session N+1 (same user/tenant); cross-tenant `memory_search` returns 0 of the other tenant's rows; all writes audited with `trace_context`.
- **Tier 2** (with A-2): `PromptBuilt.layer_metadata.memory_layers_used` non-empty; `MemoryAccessed` emitted per turn; lead-then-verify rules present in the assembled system prompt; auto-injected summary ≤ 2K tokens.

---

## 8. Method note

Synthesized from a 2-agent parallel read-only audit (current-code-ground-truth + planning-target-spec) on main `526be549` (Sprint 57.63 merged). Effort figures are judgement estimates, not commitments; calibration belongs in the eventual sprint plan §Workload.
