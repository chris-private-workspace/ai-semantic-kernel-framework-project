# Sprint 57.65 — Checklist (Memory Auto-Inject + Prompt-Cache Observability — A-1 Tier2 + A-2 Tier2)

**Plan**: [`sprint-57-65-plan.md`](./sprint-57-65-plan.md)
**Created**: 2026-06-01
**Status**: Draft (code gated on scope approval)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Day-0 prongs below were largely PRE-VERIFIED by the post-57.64 reality audit (D1-D6 in plan §0); re-confirm the residual unknowns at sprint start before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [ ] **Prong 1 (path)**: confirm `make_chat_prompt_builder` at `_category_factories.py:104` (hard-codes `MemoryRetrieval(layers={})` `:131`); `make_chat_memory_deps` `:137`; `DefaultPromptBuilder` ctor `memory_retrieval` `builder.py:168/176`; `_inject_memory_layers` `:224/:350-359`; `_build_system_section` `:283`; loop metrics_acc `loop.py:961-969` + `LoopCompleted` `:1026-1046` + `build()` call `:901-918` (user_id=None `:904`)
  - Verify: `grep -n "def make_chat_prompt_builder\|MemoryRetrieval(layers={})" backend/src/api/v1/chat/_category_factories.py`
- [ ] **Prong 2 (content)**: confirm (a) `_build_system_section` does NOT consume `memory_layers` today (D3); (b) NO `max_memory_tokens` anywhere (`grep -rn max_memory_tokens backend/src` = 0); (c) NO `verify_before_use` in `prompt_builder/**` (`grep -rn verify_before_use backend/src/agent_harness/prompt_builder` = 0); (d) `loop.py:961-964` metrics_acc reads only prompt/completion (drops `cached_input_tokens`); (e) Azure adapter `_compute_prompt_cache_key` + `extra_body[prompt_cache_key]` `adapter.py:216-218` + populates `cached_input_tokens` `:437-443`; (f) `PromptCacheManager.apply_breakpoints` zero prod call sites; (g) **InMemoryCacheManager emits non-empty cache_breakpoints?** (chat path `_category_factories.py:132`) — if no-op, note as the only caching-side fix
  - Verify: `grep -rn "verify_before_use\|max_memory_tokens" backend/src/agent_harness/prompt_builder`
- [ ] **Prong 3 (schema)**: NO new DB table/migration (memory tables exist); confirm `LoopCompleted` (`_contracts/events.py`) current fields → decide reuse-existing-metrics-path vs add cache-hit field; confirm `TokenUsage.cached_input_tokens` `_contracts/chat.py:104`
  - Verify: `grep -n "class LoopCompleted\|cached_input_tokens" backend/src/agent_harness/_contracts/events.py backend/src/agent_harness/_contracts/chat.py`
- [ ] Catalogue drift findings (re-confirm D1-D6 + the InMemoryCacheManager breakpoint question) in progress.md; go/no-go for Day 1

### 0.2 Branch + decisions
- [ ] Create branch `feature/sprint-57-65-memory-autoinject-cache-observability` from main
- [ ] Confirm scope decisions: render-grouping shape (scope-grouped hint block); cap truncation order (lowest-confidence/oldest first); verify-rule text source; user_id via trace_context vs threaded param; cache-hit metric via existing Tracer path vs new `LoopCompleted` field; Agent-delegated yes/no (Workload 4-segment); C-11 secrets set? (real_llm e2e leg gated)

---

## Day 1 — Shared surface + A-1 render core

### 1.1 Shared change surface
- [ ] Extend `make_chat_prompt_builder(chat_client, memory_retrieval=None)` to use the real retrieval (default empty preserves 57.64 standalone); thread the SAME `MemoryRetrieval` built for the executor + real `user_id` through `handler.py`
  - DoD: existing 57.64 keystone tests still pass; default (no retrieval) path byte-identical to 57.64
  - Verify: `pytest tests/integration/api/test_chat_keystone_wiring.py -q`
- [ ] Confirm tools + prompt share ONE `MemoryRetrieval` instance (no double-build); mypy strict clean; no SDK import
  - Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green)

### 1.2 A-1 memory render (US-1)
- [ ] `_build_system_section` (`builder.py:283`) consumes `PromptSections.memory_layers` → deterministic scope-grouped system-prompt text block (hint summary + confidence + last_verified_at)
  - DoD: a build() with non-empty retrieval renders a memory block IN `artifact.messages` system content; empty retrieval → no block, no crash (AP-4: prove render, not just fetch)
  - Verify: `pytest tests/unit/agent_harness/prompt_builder/test_builder.py -q`
- [ ] Integration: chat SSE run with real layers → `PromptBuilt.memory_layers_used` non-empty + memory text present in assembled system prompt
  - Verify: new `test_chat_tier2_wiring.py` (memory-render case)

---

## Day 2 — A-1 cap + verify + A-2 observability

### 2.1 A-1 token cap + verify_before_use (US-1)
- [ ] `max_memory_tokens` (default 2000) added to builder config/ctor (`_abc.py` / `builder.py`); render step truncates lowest-confidence/oldest hints first until under budget (via neutral `token_counter`)
  - DoD: a render with > 2000 tokens of hints is truncated to ≤2000; test asserts the cap
- [ ] `verify_before_use` lead-then-verify rule block injected into system prompt when any rendered hint has `verify_before_use=True` (static rule text + to-verify list); absent when no flagged hint
  - DoD: test asserts presence with a flagged hint, absence without; per `10.md §原則3`
  - Verify: `pytest tests/unit/agent_harness/prompt_builder/ -q`

### 2.2 A-2 prompt-cache observability (US-2)
- [ ] Accumulate `cached_input_tokens` in `metrics_acc` (`loop.py:961-969`) alongside prompt/completion (today dropped — D2)
  - DoD: a loop run with `cached_input_tokens>0` carries it through to completion
- [ ] Emit Cat 12 cache-hit-rate (= cached/prompt, div-0 guarded) on `LoopCompleted` (`loop.py:1026-1046`) via existing Tracer/metrics path (or new field if Day-0 decided); register in 17.md if contract changed
  - DoD: metric emitted with mock usage `cached_input_tokens>0`; =0 / no-crash when absent
  - Verify: `pytest tests/integration/api/test_chat_tier2_wiring.py -q` (cache-metric case)

---

## Day 3 — Cross-cutting tests + real_llm e2e + lint

- [ ] Combined integration test: one chat SSE run renders capped memory block + verify rules + emits cache-hit metric; cross-tenant isolation (tenant-B prompt shows none of tenant-A's hints); negative guards (empty retrieval → no block; no cached tokens → metric 0)
- [ ] `real_llm` e2e: 2-turn Azure run → turn-2 `cached_input_tokens>0` + non-empty memory block when memory exists (gated on C-11 secrets; assert via loop event/metric — A-5 OOS for HTTP-level)
  - Verify: `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q` (or GitHub Actions "E2E Real-LLM Smoke")
- [ ] Confirm LLM SDK leak 0 + mypy strict + 9/9 V2 lints + frontend untouched

---

## Day 4 — Closeout

- [ ] Full validation sweep: `pytest` (all) / `mypy --strict` / `python scripts/lint/run_all.py` / frontend untouched / LLM SDK leak 0
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-0XX-memory-autoinject-cache-observability.md`
- [ ] progress.md (Day 0-4 actuals) + retrospective.md (Q1-Q7)
- [ ] Calibration: record `medium-backend` ratio + `agent_factor` (if delegated) in `calibration-log.md §3`
- [ ] Update Area-A capstone: mark 候選 Sprint B shipped; note D1/D2/D3 drift corrections runtime-confirmed
- [ ] MEMORY.md pointer + `memory/project_phase57_65_*.md` subfile (per §Sprint Closeout) + CLAUDE.md lean Current Sprint/Last Updated
- [ ] PR (no push without authorization)
