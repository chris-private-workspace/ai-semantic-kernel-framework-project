# Memory-Formation Slice 1 — User-Identity Write + Always-On Inject (Design Note)

**Purpose**: Extract the verified design of the memory-formation round-trip (proactive user-fact write + keyword-independent surfacing) from the Sprint 57.148 implementation — the pattern that makes the platform actually remember a user across sessions (the Claude-Code-memory equivalent).
**Category / Scope**: Cat 3 (Memory) + Cat 5 (Prompt Construction) + Cat 2 (system-prompt nudge) / Phase 57 / Sprint 57.148
**Created**: 2026-06-27
**Status**: Active (verified ratio ~95%)
**Author**: self (solo-dev)

> **Modification History**
> - 2026-06-27: Initial extract from Sprint 57.148 (AD-Memory-Formation-Identity Slice 1)

---

## 1. Spike Summary (US → what shipped)

First slice of the memory-formation arc — closes `AD-Memory-Formation-Identity`. Makes the platform persist a user's stated identity and recall it in a later session, fixing the live-drive-through failure ("new session → 我不知道你是誰").

- **US-1** formation: a system-prompt nudge so the agent proactively calls the already-wired `memory_write(scope='user')` when the user states durable self-facts.
- **US-2** surfacing: an always-on user-profile injection so user-scope long_term facts reach the prompt EVERY turn, regardless of whether the message keyword-matches them.
- **US-3** 2-session + isolation drive-through (real chat-v2 + Azure gpt-5.2). **US-4** closeout.

## 2. Decision Matrix

### Formation mechanism

| Option | Mechanism | Decision |
|--------|-----------|----------|
| **A — LLM nudge + reuse `memory_write`** | a system-prompt instruction; the agent decides in-band what to persist | **CHOSEN** — minimal (no new infra), in-band, drive-through-falsifiable |
| B — deterministic post-turn extraction | run an LLM extractor over each turn / at session end → write user memory | deferred — heavier (when/cost). NOTE: `agent_harness.memory.extraction.MemoryExtractor.extract_session_to_user` ALREADY exists (unwired) → the Option-B building block is present for a future slice |

### Surfacing mechanism (the gating design decision)

| Option | Mechanism | Decision |
|--------|-----------|----------|
| **Always-on `profile()` pull** | user-scope long_term, wildcard query, injected unconditionally every turn | **CHOSEN** — keyword-independent; the faithful equivalent of CC's always-injected identity |
| Nudge the agent to call `memory_search` at session start | rely on the LLM choosing a good query | rejected — also ILIKE query-gated + non-deterministic; unreliable for identity |
| Broaden the single per-build query to wildcard for ALL layers | one query → all layers wildcard | rejected — floods tenant/role/session layers; identity is user-scope only |

### Why always-on is REQUIRED (not optional)

The live injection (`_inject_memory_layers`) is ILIKE query-gated: it surfaces a user fact only when the current message keyword-matches it. An identity question ("你知道我是誰") shares no keyword with "User name is Chris" → 0 rows → not injected. So a nudge-to-write alone would write the fact but never recall it for the identity question = AP-4 Potemkin. The always-on `profile()` is what closes the round-trip.

## 3. Verified Invariants (file:line + verification)

1. **`profile()` is wildcard, user-scope, long_term** — `MemoryRetrieval.profile(tenant_id, user_id, top_k)` → `UserLayer.read(query="", time_scales=("long_term",), max_hints=top_k)`; `[]` without tenant/user or user layer. `memory/retrieval.py`. Verify: `test_retrieval.py::test_profile_pulls_user_layer_long_term_with_wildcard_query` + `::test_profile_only_dispatches_user_layer` + `::test_profile_returns_empty_without_tenant_or_user`.
2. **Bypasses the empty-query guard** — `MemoryRetrieval.search` has NO empty-query guard (`retrieval.py:67`, only `tenant_id is None`); the guard lives in the builder (`builder.py:581`). `profile()` calls the user layer directly so `query=""` reaches `UserLayer.read` → ILIKE `'%%'` matches all the user's rows. Verify: Day-0 D-empty-query-guard (progress.md) + the wildcard test asserts `last_query == ""`.
3. **Always-on merge into the user block** — `build()` pulls `profile()` (gated on `user_id is not None`), PREPENDS into `memory_layers["user"]`, dedups by `hint_id`. `prompt_builder/builder.py` (between `_inject_memory_layers` and `_apply_memory_budget`). Verify: `test_builder_memory_injection.py::test_profile_injected_even_when_query_mismatches` (search returns [], profile fact still rendered) + `::test_profile_deduped_against_query_gated_hints`.
4. **Within the Tier2 cap** — the merge happens BEFORE `_apply_memory_budget` (`builder.py:257`, ≤`max_memory_tokens` default 2000) so the merged set is bounded by the existing cap. Verify: code path + `test_builder_tier2` unchanged.
5. **Graceful-degrade** — a `profile()` exception logs + skips identity inject; build() never crashes. `builder.py`. Verify: `test_builder_memory_injection.py::test_profile_failure_degrades_gracefully`.
6. **Not pulled without user_id** — anonymous/legacy callers (user_id None) skip `profile()` → byte-identical to pre-57.148. Verify: `::test_profile_not_pulled_without_user_id`.
7. **Formation nudge rides the proven seam** — `MEMORY_FORMATION_NUDGE` appended to `system_prompt` in `handler.py` next to the skills catalog; reaches the LLM via the loop prepend (`loop.py:1970`). Gated on `memory_retrieval is not None`. `tools/memory_tools.py` + `api/v1/chat/handler.py`. Verify: `test_handler.py::test_real_llm_handler_includes_memory_formation_nudge` + `::test_echo_demo_handler_omits_memory_formation_nudge`.
8. **Per-user / per-tenant isolation preserved** — `profile()` threads tenant_id + user_id into `UserLayer.read`'s `WHERE tenant_id AND user_id` filter; the wildcard query does NOT bypass it. Verify: `test_tenant_isolation.py::test_profile_pull_isolated_by_tenant` + the live Leg-3 (priya sees 0 of jamie's facts).
9. **Drive-through (real, NOT gate-only)** — jamie@acme.com baseline 0 rows → S1 proactive `memory_write` ×2 (`'User name is Chris.'` 0.90 / `'Chris is responsible for developing the Knowledge Connector feature…'` 0.85, both perm) → NEW-session S2 "你知道我是誰嗎?" (0 keyword overlap) recalls "你是 Chris…Knowledge Connector" with 2 user-layer reads (trace `ddc56264…`) → priya (different user) "我不知道你是誰". Reproduce: progress.md Day 3 (real Azure gpt-5.2). Screenshots in `sprint-57-148/artifacts/`.

## 4. Cross-Category Contracts

- **No new 17.md contract / wire event / DB migration.** Reuses: `MemoryRetrieval` + `UserLayer` (Cat 3, Sprint 51.2), the `memory_write`/`memory_search` ToolSpecs + ExecutionContext-scoped handlers (Cat 2, Sprint 52.5), `DefaultPromptBuilder.build()` (Cat 5, Sprint 52.2 + 57.65 Tier2), and the `handler.py` system-prompt seam (skills-catalog precedent, Sprint 57.113).
- `profile()` is a NEW public method on the existing `MemoryRetrieval` (additive; `search()` unchanged). `DefaultPromptBuilder` gains a `profile_top_k=5` ctor param (additive; default preserves all existing callers).

## 5. Open Invariants (deferred — NOT verified this sprint)

| Item | Status | Where |
|------|--------|-------|
| Deterministic post-turn fact extraction (Option B) | deferred (building block `MemoryExtractor` exists, unwired) | `AD-Memory-Formation-Auto-Extract` |
| Upsert-by-key in `UserLayer.write` (dedup dup identity rows) | deferred — MVP tolerates dups (profile top-k by confidence) | `AD-Memory-User-Upsert-By-Key` |
| Cross-session CONVERSATION/message recall + session summary → Layer 5 | deferred | `AD-Memory-Formation-Session-Recall` (缺口 2) |
| Memory semantic / Qdrant axis | unblocked, NOT wired | CARRY-026 (the 57.147 per-tenant Qdrant pattern is reusable) |
| tenant/role/session always-on injection | out of scope (identity = user-scope) | future memory-surfacing slice |
| Profile facts surviving the Tier2 cap under heavy memory pressure | known edge | drops by confidence; acceptable for identity (few rows) |

**Boundary statement**: verified = proactive user-scope identity write (nudge) + keyword-independent always-on surfacing (profile) + per-user/per-tenant isolation, end-to-end on the real chat path (write → cross-session recall → isolation). NOT verified = Option-B extraction, upsert dedup, cross-session conversation recall, semantic axis.

## 6. Rollback

- Per-call: `user_id=None` skips `profile()` entirely → byte-identical to pre-57.148. The nudge is gated on `memory_retrieval is not None`.
- Full revert: revert the 4 src EDITs (`retrieval.py`/`builder.py`/`memory_tools.py`/`handler.py`) + the 4 test EDITs. < 1 hr; no migration, no sentinel, no schema state (the `memory_user` rows written are inert data — deleting them resets). The pre-57.148 query-gated injection path is untouched underneath.

## 7. References

- `agent_harness/memory/{retrieval,layers/user_layer}.py` · `agent_harness/prompt_builder/builder.py` · `agent_harness/tools/memory_tools.py` · `api/v1/chat/handler.py`
- `agent_harness/orchestrator_loop/loop.py:1970` (system-prompt prepend seam) · `agent_harness/memory/extraction.py` (Option-B building block)
- `.claude/rules/multi-tenant-data.md` (user/tenant isolation) · CHANGE-115 · Sprint 57.148 plan/checklist/progress/retrospective
- `memory/feedback_drive_through_over_paper_metrics.md` · `claudedocs/5-status/v2-reality-audit-engine-vs-grounding-20260626.md` (north star: memory-equipped agents)

## 8. Modification History

- 2026-06-27: Initial creation (Sprint 57.148) — memory-formation identity write + always-on inject design extract.
