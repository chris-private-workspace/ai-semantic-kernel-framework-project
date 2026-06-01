# Sprint 57.65 — Checklist (Memory Auto-Inject + Prompt-Cache Observability — A-1 Tier2 + A-2 Tier2)

**Plan**: [`sprint-57-65-plan.md`](./sprint-57-65-plan.md)
**Created**: 2026-06-01
**Status**: Draft (code gated on scope approval)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Day-0 prongs below were largely PRE-VERIFIED by the post-57.64 reality audit (D1-D6 in plan §0); re-confirm the residual unknowns at sprint start before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [x] **Prong 1 (path)**: confirmed all paths (audit + residual re-verify) — `make_chat_prompt_builder` `:104`/empty retrieval `:131`; `_inject_memory_layers` `:224/:350-359`; `_build_system_section` `:283`; loop metrics_acc `:961-969` + `LoopCompleted` `:1026-1046` + build() `:901-918` (user_id=None `:904`)
- [x] **Prong 2 (content)**: confirmed (a) `_build_system_section` ignores `memory_layers` (D3); (b) NO `max_memory_tokens` (0 hits); (c) NO `verify_before_use` in prompt_builder (0 hits); (d) metrics_acc drops `cached_input_tokens` (D2); (e) Azure `prompt_cache_key` + populates cached_input_tokens (D1); (f) `apply_breakpoints` dead in prod; (g) **InMemoryCacheManager emits NON-empty per-section breakpoints** (`cache_manager.py:186-215`), Azure key from `section_id` only → stable cross-turn → metric measurable (Q1)
- [x] **Prong 3 (schema)**: NO new DB table/migration. `LoopCompleted` fields = stop_reason/total_turns/total_tokens/input_tokens/output_tokens/provider/model (no cached field → ADD `cached_input_tokens`); metrics via event fields NOT registry (Q2); `TokenUsage.cached_input_tokens` `chat.py:104` confirmed
- [x] Catalogued D1-D6 + Q1-Q4 in progress.md Day 0 table; **go/no-go = GO** (scope shift < 20%)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-65-memory-autoinject-cache-observability` created; plan+checklist committed (1st commit)
- [x] Scope decisions resolved: render = scope(`layer`)-grouped `summary` block; cap truncation = lowest-confidence/oldest first via `token_counter`; verify-rule = static lead-then-verify block + flagged-hint list; user_id = one-line `loop.py:904` `ctx.user_id` (Q4); cache-hit metric = NEW `cached_input_tokens` field on `LoopMetricsAccumulator` + `LoopCompleted` (no registry — Q2); **Agent-delegated: yes** (staged, 57.64 pattern); C-11 real_llm leg gated (defer per A-5 OOS like 57.64)

---

## Day 1 — Shared surface + A-1 render core

### 1.1 Shared change surface
- [x] `make_chat_prompt_builder(chat_client, memory_retrieval=None)` uses real retrieval (default empty preserves 57.64); `handler.py` threads the SAME `MemoryRetrieval` (`:216`, shared with executor) + `user_id` (Stage 1 ✅ — parent re-verified)
  - DoD: 57.64 keystone tests still pass; default path byte-identical → 64 passed (incl. 11 keystone unchanged)
- [x] Tools + prompt share ONE `MemoryRetrieval` (handler reuses the `:216` instance — verified in diff); mypy 0/319; no SDK import (check_llm_sdk_leak green)

### 1.2 A-1 memory render (US-1)
- [x] Memory render wired (Stage 1 ✅) — NOTE: render machinery pre-existed via `templates._memory_as_messages` + `LostInMiddleStrategy` (52.2; Day-0 D3 misdiagnosed it as missing — see progress.md Day 1 correction). Real fix = feed real layers + fixed `system→tenant→role→user→session` order + enriched hint line (summary + confidence + last_verified_at). `_build_system_section` carries only the verify block (avoids duplicate memory block)
  - DoD: build() with real retrieval renders memory IN assembled prompt; empty retrieval → no block, no crash (AP-4) → asserted in `test_builder_tier2.py` (11) + `test_chat_tier2_wiring.py` negative case
- [x] Integration: chat SSE run with real layers → `PromptBuilt.memory_layers_used` non-empty + stored memory text present in `mock.last_request.messages` (Stage 1 ✅ — `test_tier2_memory_renders_into_assembled_prompt`)

---

## Day 2 — A-1 cap + verify + A-2 observability

### 2.1 A-1 token cap + verify_before_use (US-1) — done in Stage 1 (with A-1)
- [x] `max_memory_tokens=2000` on `DefaultPromptBuilder` ctor; `_apply_memory_budget` drops lowest-confidence→oldest via neutral `token_counter` until ≤2000 (Stage 1 ✅)
  - DoD: cap asserted in `test_builder_tier2.py` (under-budget / drops-lowest-confidence / ties-on-oldest / no-op cases)
- [x] `_build_verify_before_use_block` injects lead-then-verify text + flagged summaries into system role when any hint `verify_before_use=True`; absent otherwise (Stage 1 ✅)
  - DoD: `test_builder_tier2.py` (present/absent/skips-capped-hint) + `test_chat_tier2_wiring.py::test_tier2_verify_before_use_rule_present`

### 2.2 A-2 prompt-cache observability (US-2) — Stage 2
- [x] Accumulate `cached_input_tokens` in `metrics_acc` — inline `loop.py:964-973` AND on_event `_metrics.py` LLMResponded branch (both, AP-10 no divergence); NEW `cumulative_cached_input_tokens` on `LoopMetricsAccumulator` (Stage 2 ✅)
  - DoD: a run with `cached_input_tokens>0` carries it to completion → asserted (cached=60)
- [x] Emit Cat 12 cache-hit-rate on `LoopCompleted` — NEW `cached_input_tokens` + `cache_hit_rate` fields (div-0 guarded `cache_hit_rate` property = DRY source); both emission sites (`:1037-1046` + `:1057-1066`); `LLMResponded.cached_input_tokens` too; registered in 17.md §4.1 (Stage 2 ✅)
  - DoD: `test_tier2_cache_hit_metric_emitted` asserts `cache_hit_rate == approx(0.6)`; 2-turn accum + zero/div-0 cases → 59 passed; mypy 0/319; 9/9 lints

---

## Day 3 — Cross-cutting tests + real_llm e2e + lint

- [x] Combined integration test: `test_tier2_memory_render_and_cache_metric_one_run` — ONE run renders memory (stored text in prompt + `memory_layers_used` "session") AND `cache_hit_rate == approx(0.4)` (cached=80/input=200) → A-1 + A-2 co-exist, no interference. Cross-tenant + negative + cap covered by the 7 prior tier2 tests (Day 3 ✅ — tier2 file 8 passed)
- 🚧 `real_llm` live e2e leg DEFERRED (confirmatory, same rationale as 57.64): HTTP-level assertion of memory-block / cache_hit_rate blocked by A-5 (events→SSE) OUT of scope — both are in-process LoopEvent/loop-state, not yet client SSE; the live real_llm path was already exercised in C-11; Azure cost + `cost_ledger` FIX-024 known-red. Mock integration tests (memory render + `cache_hit_rate` value) are the primary gate per plan §3.3. Live confirmation available on request.
  - Verify (when run): `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q`
- [x] LLM SDK leak 0 + mypy strict 0/319 + 9/9 V2 lints + frontend untouched (Day 3 ✅ — full sweep **1955 passed / 4 skipped**; +21 tests vs 1934 baseline)

---

## Day 4 — Closeout

- [x] Full validation sweep: pytest **1955 passed / 4 skipped**; `mypy src/` 0/319; `run_all.py` 9/9; frontend untouched; SDK leak 0 (Day 4 ✅)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-033-memory-autoinject-cache-observability.md` (Day 4 ✅)
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7) (Day 4 ✅)
- [x] Calibration: `medium-backend` 0.80 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 caveated low-confidence (3rd consec agent-delegated no-clean-wall-clock) → KEEP, no baseline change; new `AD-Calibration-AgentDelegated-WallClock-Measure`; recorded `calibration-log.md §3` (Day 4 ✅)
- [x] Area-A capstone: 候選 Sprint B shipped; D1/D2/D3 corrections runtime-confirmed (Day 4 ✅)
- [x] MEMORY.md pointer + `project_phase57_65_*.md` subfile + CLAUDE.md lean Current Sprint/Last Updated (Day 4 ✅)
- [ ] PR (no push without authorization)
