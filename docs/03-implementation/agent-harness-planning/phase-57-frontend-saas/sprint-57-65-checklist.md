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
