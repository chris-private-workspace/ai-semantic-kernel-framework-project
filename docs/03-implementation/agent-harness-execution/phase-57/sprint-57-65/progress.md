# Sprint 57.65 Progress — Memory Auto-Inject + Prompt-Cache Observability

**Sprint**: 57.65 (A-1 Tier2 memory auto-inject + A-2 Tier2 prompt-cache observability)
**Branch**: `feature/sprint-57-65-memory-autoinject-cache-observability` (from main, post-57.64 merge)
**Scope class**: `medium-backend` (0.80) / **Agent-delegated: yes** (staged code-implementer + parent independent re-verification, 57.64 pattern)

> Modification History
> - 2026-06-01: Initial creation (Day 0 drift findings + go decision)

---

## Day 0 — Plan-vs-Repo Verify + Branch

Day-0 三-prong was performed by a codebase-researcher reality audit (post-57.64) + a 4-question residual re-verify. Findings catalogued below; **go/no-go = GO** (scope shift < 20%; both Tier2s remain, reshaped per real code state).

### Drift findings (D1-D6 from audit; Q1-Q4 residual confirmations)

| ID | Finding | Implication (plan §Risks ref) |
|----|---------|-------------------------------|
| **D1** | A-2 caching call-site ALREADY wired: `loop.py:910-912` collects + `:939-943` forwards `cache_breakpoints` to `chat()`; Azure adapter applies `prompt_cache_key` via `extra_body` (`adapter.py:216-218`). Analyses' "動 loop.py at LLM-call site" is STALE | A-2 = observability ONLY; no call-site rewrite; do NOT wire dead `PromptCacheManager.apply_breakpoints` |
| **D2** | `TokenUsage.cached_input_tokens` exists (`_contracts/chat.py:104`), populated by Azure adapter (`:437-443`), but loop's `metrics_acc` drops it (`loop.py:961-964`) — flows only to billing | A-2 work = accumulate + emit on LoopCompleted |
| **D3** | A-1 hidden Potemkin: `_inject_memory_layers` (`builder.py:224`) FETCHES hints into `PromptSections.memory_layers`, but `_build_system_section` (`:283`) IGNORES them → never rendered. No `max_memory_tokens` cap (0 hits). `verify_before_use` never injected (0 hits in prompt_builder) | US-1 is net-new render+cap+verify, not a one-liner |
| **D4** | No `PromptInputs`/`memory_provider`/`MemoryLayerProvider` — memory via ctor `memory_retrieval: MemoryRetrieval` (`builder.py:168/176`) | wiring = pass real retrieval into ctor (not a new Protocol) |
| **D5** | `CacheBreakpoint` real fields: `position`/`section_id`/`content_hash`/`cache_control` (`_contracts/chat.py:147-160`), not `{index,kind}` | render/test against real fields |
| **D6** | `PromptBuilt` already emitted (`loop.py:915`) reading `layer_metadata["memory_layers_used"]` (`:918`) | becomes non-empty automatically once memory renders |
| **Q1** | `InMemoryCacheManager.get_cache_breakpoints()` returns NON-empty per-section breakpoints (`cache_manager.py:186-215`), gated by `policy.enabled`; Azure key derives from `section_id` only (`adapter.py:100-103`) → **stable across turns → cache-hit metric measurable** | confirm `_sections_from_policy` includes `memory_layers` only when memory present (key stability) — Day-1 note |
| **Q2** | NO Tracer/MetricsRegistry; metrics = event fields from `LoopMetricsAccumulator` (`_metrics.py:53-69`) → `LoopCompleted` (`:1026-1029`/`:1043-1046`). `LoopCompleted` has no cached field | add `cumulative_cached_input_tokens` to accumulator + `cached_input_tokens` to `LoopCompleted` (+ `LLMResponded` if routing via `on_event`); populate at `:961-969` inline + emission sites |
| **Q3** | `MemoryHint` (`_contracts/memory.py:64-79`): render `summary` (NO `content` field; `full_content_pointer` is a ref); scope axis = `layer`; flag `verify_before_use` | render contract fixed |
| **Q4** | user_id fix = ONE LINE: `loop.py:904` `user_id=None` → `user_id=ctx.user_id` (`ctx.user_id` in scope, used `:409`/`:1138`; `TraceContext.user_id` at `observability.py:67`); `build()` already threads user_id into `_inject_memory_layers` | the only loop.py LOGIC touch besides the A-2 metrics accumulation |

### Reshaped scope (confirmed with user: 全包 / staged delegation + parent re-verify)
- **US-1 (A-1)**: `_category_factories.py` thread real `MemoryRetrieval`; `handler.py` thread it + (via Q4) loop user_id one-liner; **`builder.py` net-new** render(`summary` block) + `≤2000` cap (via `token_counter`) + `verify_before_use` injection.
- **US-2 (A-2)**: `_metrics.py` accumulator + `loop.py` accumulate `cached_input_tokens` + `LoopCompleted`/`LLMResponded` field + emit; no adapter/call-site change.
- **US-3**: integration tests + real_llm 2-turn e2e.

**Branch**: `feature/sprint-57-65-memory-autoinject-cache-observability` created; plan+checklist committed (1st commit).

## Day 1 — Stage 1 = A-1 Tier2 (memory render + cap + verify) — code-implementer delegated, parent re-verified

Covered checklist §1.1 + §1.2 + §2.1 (the whole A-1 builder/factory surface — cleaner than a calendar split).

**Implemented** (`a526a019be8f08b68`):
- `_category_factories.py`: `make_chat_prompt_builder(chat_client, memory_retrieval=None)` — uses real retrieval when given, empty `MemoryRetrieval(layers={})` otherwise (57.64 standalone preserved).
- `handler.py`: threads the SAME `memory_retrieval` (already built at `:216` for the executor) into `make_chat_prompt_builder` (one shared retrieval). Accepts + threads `user_id`.
- `loop.py:904`: `user_id=None` → `user_id=ctx.user_id` (the one-line user-layer scoping fix).
- `builder.py`: `max_memory_tokens=2000` ctor param + `_apply_memory_budget` (drops lowest-confidence→oldest via the neutral `token_counter`) + `_build_verify_before_use_block` appended to system role + `_inject_memory_layers` fixed `system→tenant→role→user→session` order.
- `templates.py`: `MEMORY_HINT_FORMAT` enriched to `- {summary} (confidence X.XX[, last verified <iso>])` + `_format_hint_line` + `VERIFY_BEFORE_USE_HEADER`. `full_content_pointer` NOT inlined.

**🔴 D3 CORRECTION (parent re-verify finding — preserve audit trail, do not silently rewrite Day-0 D3)**: the Day-0 audit's D3 ("memory hints fetched but `_build_system_section` ignores them → never rendered") was **a misdiagnosis**. Memory render machinery ALREADY EXISTED via `templates._memory_as_messages` (Sprint 52.2), consumed by the default `LostInMiddleStrategy` (8 existing tests assert it). `_build_system_section` is a DIFFERENT path. The REAL chat-path gap was: (a) the chat path fed an **empty** `MemoryRetrieval(layers={})` → nothing to render; (b) no `≤2000` cap; (c) no `verify_before_use` injection; (d) `user_id=None`. So Stage 1 = feed real layers + add cap/verify/enrichment/user_id — NOT "build a render that never existed". The code-implementer correctly put cap+verify in `build()`/templates (keeping the strategy render path) to avoid a DUPLICATE memory block + keep the 8 strategy tests green.

**Parent independent re-verification** (not trusting self-report, 57.64 discipline):
- Re-ran `pytest test_chat_tier2_wiring.py test_chat_keystone_wiring.py prompt_builder/` → **64 passed** (57.64 keystone 11 unchanged-green).
- Re-ran `mypy src/` → 0/319; `python scripts/lint/run_all.py` → 9/9 green (check_llm_sdk_leak clean).
- Read `builder.py`/`templates.py`/`test_templates.py` diffs: no duplicate block (hints render once via strategy; verify block is a separate instruction); cap/verify/order sound; `test_templates.py` assertion change = legitimate format-enrichment (stronger, not weakened); backward-compat preserved (`_build_system_section(None)` → byte-identical system role).
- Read `test_chat_tier2_wiring.py`: assertions are substantive (stored memory text present in `mock.last_request.messages`; cross-tenant tenant-A text absent from tenant-B prompt; verify header present; negative no-block) — AP-4 "prove render not fetch" satisfied.
- Minor (retro): `_measure_memory_tokens` `tools` param is forwarded but unused (calls `count(tools=None)`); docstring slightly overstates a "baseline subtraction" that isn't done. Harmless; note for cleanup.

**New tests**: `test_chat_tier2_wiring.py` (4 integration) + `test_builder_tier2.py` (11 unit) + 1 `test_templates.py` assertion update.

## Day 2 — Stage 2 = A-2 Tier2 (cache observability) — code-implementer delegated, parent re-verified

Covered checklist §2.2. The Azure cache pipe was already complete (Day-0 D1/D2); this is observability-only.

**Implemented** (`a46b648b9e1d26730`):
- `_contracts/events.py`: `LLMResponded.cached_input_tokens: int = 0`; `LoopCompleted.cached_input_tokens: int = 0` + `cache_hit_rate: float = 0.0` (safe defaults — no existing constructor breaks).
- `_metrics.py`: `LoopMetricsAccumulator.cumulative_cached_input_tokens`; on_event LLMResponded branch accumulates it; NEW `cache_hit_rate` property (cached/input, `input<=0 → 0.0`) = single DRY rate source.
- `loop.py:964-973`: inline `metrics_acc.cumulative_cached_input_tokens += response.usage.cached_input_tokens` (the path that runs) + `LLMResponded(... cached_input_tokens=...)` emission (`:991`); BOTH `LoopCompleted` sites (END_TURN terminator `:1037-1046` + FINAL `:1057-1066`) populate `cached_input_tokens` + `cache_hit_rate=metrics_acc.cache_hit_rate`.
- `17-cross-category-interfaces.md`: registered the 3 new LoopEvent fields (§4.1).

**Parent independent re-verification** (57.64 discipline):
- Re-ran `pytest test_chat_tier2_wiring.py test_chat_keystone_wiring.py tests/unit/.../orchestrator_loop/` → **59 passed**.
- Re-ran `mypy src/` → 0/319; `run_all.py` → 9/9 green.
- Read `events.py`/`_metrics.py`/`loop.py` diffs: inline AND on_event both accumulate (AP-10 — no mock/real divergence); div-0 guarded; DRY `cache_hit_rate` property consumed by both emission sites; LoopCompleted constructed manually (NOT via `to_loop_completed_payload`) so no double-spec.
- Read the new tests: `test_tier2_cache_hit_metric_emitted` asserts the RATE VALUE (`cache_hit_rate == pytest.approx(0.6)` for cached=60/input=100) — substantive, not just `>0`; 2-turn accumulation (cold→warm) + zero/div-0 cases.
- Minor (retro): `to_loop_completed_payload()` accumulator helper was NOT updated with the 2 new fields (still returns 6; pinned by `test_..._returns_six_fields`). The loop emission doesn't use the helper (manual construction), so not a runtime bug — but it's a latent inconsistency if a future caller builds `LoopCompleted(**payload)`. Note for cleanup.

**New tests**: `test_chat_tier2_wiring.py` +3 integration (cache-hit value / 2-turn accum / zero-guard) + `test_metrics_accumulator.py` +2 unit.

## Day 3 — combined test + full sweep

- NEW `test_tier2_memory_render_and_cache_metric_one_run` (parent-authored, mirrors 57.64 combined pattern): ONE run proves A-1 (stored memory text in assembled prompt + `memory_layers_used` "session") AND A-2 (`cache_hit_rate == approx(0.4)`, cached=80/input=200) co-exist without interference. tier2 file → **8 passed**.
- **Full sweep**: `pytest` → **1955 passed / 4 skipped** (+21 vs 1934 baseline: 11 builder + 8 tier2 + 2 metrics-accum); `mypy src/` 0/319; `run_all.py` 9/9 green; frontend untouched; 57.64 keystone (11) + strategy (8) unchanged-green.
- 🚧 real_llm live e2e leg DEFERRED (confirmatory; A-5 events→SSE OOS for HTTP-level memory/cache assertion; live path verified C-11; Azure cost + FIX-024 cost red).

## Day 4 — closeout

- CHANGE-033 + retrospective.md (Q1-Q7) + this progress.md.
- Calibration: `medium-backend` 0.80 + `agent_factor mechanical-greenfield-design-decisions` 0.65 — **caveated low-confidence** (3rd consecutive agent-delegated sprint with no clean wall-clock) → KEEP 0.65, no baseline change, does NOT trigger below-band-watch. New `AD-Calibration-AgentDelegated-WallClock-Measure`. Recorded `calibration-log.md §3`.
- Area-A capstone: 候選 Sprint B shipped; D1/D2/D3 corrections runtime-confirmed.
- MEMORY.md pointer + `project_phase57_65_*.md` subfile; CLAUDE.md lean Current Sprint/Last Updated.
- Commit Day 3+4 + push + PR (user-authorized, 57.64 pattern).

## Commit ↔ checklist mapping
| Commit | Checklist |
|--------|-----------|
| (plan+checklist commit) | plan + checklist |
| (Stage 1 commit `a526a019`-built) | Day 1 §1.1 + §1.2 + Day 2 §2.1 (A-1 render + cap + verify) |
| (Stage 2 commit `a46b648b`-built) | Day 2 §2.2 (A-2 cache observability) |
| (Day 3+4 commit) | Day 3 combined test + Day 4 closeout docs |
