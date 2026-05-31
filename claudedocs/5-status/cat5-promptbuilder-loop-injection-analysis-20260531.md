# A-2 Deep Analysis: Cat 5 PromptBuilder — Injection into the Agent Loop

**Purpose**: Single-point deep analysis of why the production loop assembles no structured prompt (no caching / no memory / no lost-in-middle / no PromptBuilt event), and exactly what it takes to wire Cat 5 PromptBuilder into the production chat loop. Analysis only — not an implementation plan.
**Category / Scope**: 範疇 5 (Prompt Construction) / cross-cutting wiring / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for a future sprint)

> **Modification History**
> - 2026-05-31: Initial creation — A-2 of the Area-A wiring-gap deep-analysis series; 2-agent parallel audit (current-code-truth + planning-target)

> **Related**
> - `integration-progress-20260531.md` — parent integration snapshot (Area A item 2)
> - `cat3-memory-loop-injection-analysis-20260531.md` — A-1; its Tier 2 is blocked on this analysis's subject
> - `01-eleven-categories-spec.md §範疇5` / `17-cross-category-interfaces.md §Contract 5` / `04-anti-patterns.md §AP-8` / `02-architecture-design.md §約束5` / `10-server-side-philosophy.md` (prompt caching pillar)

---

## 0. Headline

Cat 5 is the **hub of Area A**. The PromptBuilder is fully built (ABC + `DefaultPromptBuilder` + `PromptArtifact` contract + the loop integration point + unit tests) but **never injected into the production loop** — every real turn takes the raw-message fallback. Activating it unlocks, in one move: **Cat 3 memory auto-injection (A-1 Tier 2), the `verify_before_use` anti-hallucination enforcement, the Cat 4 prompt-cache half, lost-in-middle ordering, and the `PromptBuilt` observability event**. The catch: the *inject* part needs no loop.py change (the true-branch already exists), but the *caching* part does.

---

## 1. Current state — fully built, fallback always taken

| Component | Status | Evidence |
|-----------|--------|----------|
| `PromptBuilder` ABC + `DefaultPromptBuilder` | ✅ built | `prompt_builder/_abc.py:95` (`build(inputs, *, trace_context) -> PromptArtifact`); `builder.py:54` (ordered: system → tools → memory block → conversation w/ lost-in-middle) |
| `PromptInputs` (incl. `memory_provider`, `max_memory_tokens=2000`, `enable_cache`) | ✅ | `prompt_builder/_abc.py:43`; `MemoryLayerProvider` Protocol `_abc.py:71` |
| `PromptArtifact` / `CacheBreakpoint` contracts | ✅ | `_contracts/prompt.py:73` (`messages`/`cache_breakpoints`/`estimated_input_tokens`/`layer_metadata`); `:51` (`CacheBreakpoint{index, kind}`) |
| lost-in-middle strategy | ✅ | `prompt_builder/lost_in_middle.py` `reorder_for_lost_in_middle()` |
| Loop integration point (true-branch) | ✅ exists | `loop.py:196` ctor `prompt_builder | None=None`; `:235` stored; `:881` `if self._prompt_builder is not None:` → build() → `messages_for_llm = artifact.messages`; `:913` reads `layer_metadata["memory_layers_used"]` + emits `PromptBuilt` |
| Loop fallback (else-branch) | ✅ exists | `loop.py:918-922` `messages_for_llm = state.messages`; `cache_breakpoints = []`; **no** memory, **no** reorder, **no** `PromptBuilt` event |
| `PromptCacheManager` (Cat 4 cache side) | ✅ built / ❌ unwired | `context_mgmt/cache_manager.py` `apply_breakpoints(...)` exists but **never instantiated/called** in `loop.py`/`handler.py` |
| `check_promptbuilder.py` lint | ✅ exists / ⚠️ false-green | `scripts/lint/check_promptbuilder.py` flags naked role-dict assembly in `agent_harness/**`; does **not** catch the loop fallback (it forwards existing `state.messages`, not a fresh literal) |
| Unit tests | ✅ isolation only | `tests/unit/agent_harness/prompt_builder/test_builder.py` (~12) + `test_lost_in_middle.py`; **no** loop-integration test |
| **Injected into production chat path** | ❌ **no injection site** | `build_real_llm_handler` (`handler.py:155-249`) never passes `prompt_builder=` nor `memory_provider=`; no `make_chat_prompt_builder` in `_category_factories.py` |

**Net effect**: `self._prompt_builder is None` at runtime → the `loop.py:918` fallback is **always** taken on the production path. Each real turn sends the raw running conversation with no structured assembly, no cache breakpoints applied, no memory block, no lost-in-middle reorder, and emits no `PromptBuilt` event. `memory_provider` is likewise never passed (doubly gating Cat 3).

---

## 2. Key finding — Cat 5 is the hub; activating it unlocks four things

Per `01.md §範疇3/4/5`, `02.md §約束5`, `17.md §Contract 5`, the loop calls `PromptBuilder.build()` every turn, and **four capabilities flow through it**:

| Unlocked by Cat 5 | Why it's gated | Source |
|-------------------|----------------|--------|
| **Cat 3 memory auto-injection (A-1 Tier 2)** | the L1-L4 <2K summary is assembled **inside** `DefaultPromptBuilder._build_memory_block()` via `PromptInputs.memory_provider` | `builder.py:~140`; `01.md §範疇5` |
| **`verify_before_use` enforcement** | the lead-then-verify rules are injected into the **system prompt BY PromptBuilder** | `01.md §範疇3` "由範疇5 PromptBuilder 注入 system prompt" |
| **Cat 4 prompt-cache half** | `PromptBuilder` emits `cache_breakpoints`; `PromptCacheManager` (Cat 4) turns them into provider `cache_control` | `01.md §範疇4`; `10.md` (caching pillar) |
| **`PromptBuilt` observability + lost-in-middle** | both only happen in the `loop.py:881` true-branch | `loop.py:881-916` |

> This confirms the A-1 conclusion and generalises it: **A-2 is the prerequisite for A-1 Tier 2, and it also unlocks the dormant cache half of Cat 4.** Cat 5 can run with an empty `memory_provider` (degrades gracefully), so it is shippable independently — but its full value needs Cat 3 deps (A-1 Tier 1) supplied alongside.

---

## 3. Target design recap (from `01.md §範疇5`, `17.md §Contract 5`, `04.md §AP-8`)

- **Single assembler**: every LLM call's prompt MUST come from `PromptBuilder.build()` (AP-8). Naked `messages=[...]` assembly is a lint failure.
- **Per-turn structure**: System → Tools → Memory summary (<2K) → [mid-context] → Recent turns → User message; lost-in-middle puts salient content at head+tail.
- **Cache breakpoints** after system / tools / memory; consumed by Cat 4 `PromptCacheManager`; target steady-state **cache hit > 50%**.
- **Observable**: `PromptBuilt` event per turn with `messages_count` / `estimated_input_tokens` / `cache_breakpoints_count` / `memory_layers_used`.
- **DoD / "Level 4"**: sole assembler in the *main loop*, memory auto-injected <2K, breakpoints emitted **and consumed** (>50% hit), lost-in-middle applied, lint green across the production path, token budget respected (over-budget → Cat 4 compaction before the call).

---

## 4. Integration design (concrete landing points)

### A-2 Tier 1 — inject PromptBuilder (no loop.py change; the value most of Area A waits on)
1. New factory `make_chat_prompt_builder(chat_client, memory_provider=None) → DefaultPromptBuilder` in `api/v1/chat/_category_factories.py` (api layer; LLM-neutral — token estimate via `ChatClient.count_tokens()` ABC, Contract 8).
2. In `build_real_llm_handler`: construct it and pass **`prompt_builder=`** (and **`memory_provider=`** from A-1's `make_chat_memory_deps`) into `AgentLoopImpl`.
3. The `loop.py:881` true-branch already does the rest (build → artifact.messages → `PromptBuilt`). **No loop.py edit needed for injection** — same pattern as 57.63's Cat 4/7/8.
4. **Tighten the lint / add a guard test**: `check_promptbuilder` is false-green on the fallback. Add an integration assertion that the chat path's `loop._prompt_builder is not None` and that a run emits `PromptBuilt`, so a future regression to the fallback is caught.
5. Graceful degradation: with `memory_provider=None`, PromptBuilder still runs (system/tools/lost-in-middle/PromptBuilt) — memory block just empty. Best paired with A-1 Tier 1 so memory is real.

### A-2 Tier 2 — realize caching (overlaps Area B; requires loop.py change)
- Wire `PromptCacheManager.apply_breakpoints(artifact.messages, artifact.cache_breakpoints)` → provider `cache_control` markers on the `ChatClient.chat()` call. Today `cache_breakpoints` are collected at `loop.py` then **discarded** (only fed to the never-emitted event). Applying them is a behavioral change to the loop's LLM-call site — the kind of loop.py churn 57.63 deliberately avoided. Defer to an Area-B optimization sprint.

### A-2 Tier 0 — make `PromptBuilt` reach the frontend (overlaps A-5)
- `sse.py` has 14 events, none for `PromptBuilt` (nor memory/state/compaction). Backend tracing gets it regardless; frontend visibility needs an `sse.py` serializer addition — same class as A item 5.

---

## 5. Risks / open research questions

1. **loop.py churn for caching (Tier 2)**: 57.63's safe pattern was "inject via existing ctor param; existing guarded call-site activates". Cache realization breaks that pattern (must change the ChatClient-call site). Keep Tier 1 (inject, no churn) separate from Tier 2 (cache, churn).
2. **Lint false-green**: `check_promptbuilder` only flags fresh role-dict assembly in `agent_harness/**`; the production fallback (forwarding `state.messages`) is invisible. Without tightening, "Cat 5 wired" could silently regress. Add a positive assertion (chat path uses PromptBuilder), not just the negative naked-assembly check.
3. **System-prompt double-application**: in the fallback, the system prompt is applied separately at the ChatClient call; when PromptBuilder is active, system prompt goes into `artifact.messages`. Confirm no double-injection.
4. **Compaction ↔ build ordering**: compactor (Cat 4, injected 57.63) runs at `loop.py:828`, PromptBuilder at `:881` — compact-then-build looks correct (over-budget trimmed before assembly), but confirm the token-budget estimate uses the post-compaction state.
5. **memory_provider lifecycle**: a `MemoryLayerProvider` wrapping Cat 3 layers must bind to the request's tenant-scoped DB session + RLS (same concern as A-1 risk 2).
6. **Cache hit measurement (Tier 2)**: need a Cat 12 metric to verify the >50% acceptance bar.

---

## 6. Recommendation

- **Bundle A-1 Tier 1 + A-2 Tier 1 into one sprint**: register memory tools (A-1 Tier 1) AND inject `prompt_builder` + `memory_provider` (A-2 Tier 1). One coherent "make the agent memory-aware + structured-prompt" delivery, **no loop.py change**, unlocking on-demand memory + auto-inject + verify_before_use + lost-in-middle + PromptBuilt in a single shot.
- **Defer caching (A-2 Tier 2) to an Area-B sprint** — it needs loop.py call-site change and a cache-hit metric; it's an optimization, not a correctness gap.
- **Sequence**: A-2 Tier 1 should land with (or just before) A-1 Tier 2; the recommended bundle does both.

**Revised Area-A dependency graph**: `A-2 Tier 1` is the keystone — it directly enables `A-1 Tier 2` (memory auto-inject + verify_before_use). `A-2 Tier 2` (caching) ≈ Area B. `A-5` (events→SSE) overlaps the PromptBuilt-visibility gap.

---

## 7. Definition-of-done signals (for the eventual sprint)

- **Tier 1**: every `real_llm` turn takes `loop.py:881` true-branch; a run emits `PromptBuilt` (messages_count / estimated_input_tokens / cache_breakpoints_count / memory_layers_used); when `memory_provider` supplied, memory summary present and ≤ 2K tokens; `verify_before_use` rules present in the assembled system prompt; lint tightened so a fallback regression fails CI; integration test asserts `loop._prompt_builder is not None`.
- **Tier 2** (Area B): `cache_breakpoints` applied to the `ChatClient` call as `cache_control`; steady-state cache hit > 50% measured via a Cat 12 metric.

---

## 8. Method note

Synthesized from a 2-agent parallel read-only audit (current-code-ground-truth + planning-target-spec) on main `526be549` (Sprint 57.63 merged). Effort/tier framing are judgement estimates, not commitments; calibration belongs in the eventual sprint plan §Workload.
