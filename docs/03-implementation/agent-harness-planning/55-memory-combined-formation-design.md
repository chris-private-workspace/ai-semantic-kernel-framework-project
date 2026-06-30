# 55 — Combined post-send memory formation (one LLM call for extract + summarize)

**Purpose**: Design note extracted from Sprint 57.152's real implementation — combine the two post-send cheap-tier formation calls (57.149 extract + 57.151 summarize) into ONE combined call. Amends the formation architecture of notes 53 + 54.
**Category / Scope**: 範疇 3 (Memory) / Phase 57 / Sprint 57.152
**Created**: 2026-06-30
**Status**: Active (shipped, drive-through STRONG PASS)
**Closes**: `AD-Memory-Formation-Combine-Extract-Summarize`

> **Modification History**
> - 2026-06-30: Initial extraction (Sprint 57.152)

---

## 1. Spike Summary (US-1/2/3/4 — what was wired)

The post-send hook made two cheap-tier LLM calls over the same ledger — `MemoryExtractor` (durable user facts, 57.149) + `SessionSummarizer` (rolling conversation summary, 57.151). This spike adds a `MemoryFormationWorker` that composes both and (default) makes ONE combined call returning both halves, halving background token + latency per send.

- US-1 worker: `MemoryFormationWorker._form_combined` (`agent_harness/memory/formation.py:117-167`) — one prompt → one `chat()` → parse → dispatch.
- US-2 reuse: `MemoryExtractor.write_facts` (`extraction.py:111-160`) + `SessionSummarizer.store_summary` (`session_summarizer.py:118-143`) — behavior-preserving dispatch halves the worker reuses.
- US-3 fallback: `_form_separate` (`formation.py:169-194`) + `chat_memory_combined_formation` flag (`core/config/__init__.py:184`).
- US-4 wiring: `ChatMemoryExtractContext.former` (`handler.py:798`) + `build_chat_memory_extractor` (`handler.py:863-885`) + `_maybe_auto_extract` (`router.py:700-731`).

## 2. Decision Matrix

| Decision | Options | Chosen | Why (rejected alternatives) |
|----------|---------|--------|------------------------------|
| **Combine strategy** | (a) one monolithic former replacing both workers / (b) a worker COMPOSING the two existing workers | **(b) compose** | (a) orphans `SessionSummarizer` (its only non-test caller is the chat path → AP-2/AP-4) + duplicates the write/dispatch logic. (b) reuses both workers' write code via extracted dispatch halves + keeps both live (the `combined=False` path calls their full methods). |
| **Where the combined logic lives** | (a) inline in the chat router `_maybe_auto_extract` / (b) a 範疇-3 worker | **(b) worker** | (a) = AP-3 cross-directory scattering (formation logic belongs in Cat 3, not the api layer). The router stays a thin caller (`former.form()`). |
| **Quality-regression safety** | (a) combined-only / (b) env flag with a two-call fallback | **(b) flag (default ON)** | A combined structured ask COULD degrade either half's quality vs two focused calls. The flag reverts to the proven 57.149+57.151 two-call path instantly (no redeploy). The fallback also keeps `extract_session_to_user` / `summarize_and_store` live on the chat path. Analogous to `chat_verification_correction_strategy` (57.136). |
| **Section conditioning** | (a) always ask for both / (b) condition prompt sections on wired collaborators + user | **(b) condition** | The two existing feature flags decide WHICH sections form. The combined prompt asks for the facts section only when an extractor is wired AND the user is known, and the summary section only when a summarizer is wired — so a single-feature config still makes ONE call (same cost as today) and an anon trace skips facts. |
| **Shared render/parse helpers** | (a) factor into a shared module / (b) small self-contained copies in the worker | **(b) self-contained** | `_render_messages` / `_content_text` already duplicate across `extraction.py` + `session_summarizer.py` (pre-existing). Refactoring 2 stable working files to dedup ~15 trivial lines is non-surgical (Karpathy §3) + risks their tests. The worker keeps its own; the dup is noted, not fixed. |

## 3. Verified Invariants (drive-through + tests)

- **One combined call writes both halves** — Verify: `pytest tests/unit/agent_harness/memory/test_formation.py::test_combined_one_call_writes_both` (spy `chat_call_count == 1` + both dispatch collaborators invoked). Drive-through: a `memory_session_summary` row + `memory_user [auto_extract]` rows written at the SAME `15:20:30` timestamp from one send.
- **Fallback makes two calls** — Verify: `::test_combined_false_uses_separate_two_calls` (the worker's own `chat_call_count == 0`; delegates to `extract_session_to_user` + `summarize_and_store`).
- **Section conditioning** — `::test_only_extractor_one_call_facts_only` / `::test_only_summarizer_one_call_summary_only` / `::test_no_user_skips_facts_still_forms_summary`.
- **Dispatch halves behavior-preserving** — the existing `test_extraction.py` (9) / `test_session_summarizer.py` (6) / `test_extraction_worker.py` / `test_tenant_isolation.py` stay green untouched (the single-call methods now end with `write_facts` / `store_summary`).
- **Byte-identical when off** — `chat_memory_combined_formation=false` → `_form_separate` (the 57.149+57.151 two-call path). Verify: `::test_combined_false_uses_separate_two_calls`.
- **Provider-neutral** — `MemoryFormationWorker` uses the ChatClient ABC; AP-8 allowlist entry (background formation, same as `extraction.py`). Verify: `python scripts/lint/run_all.py` (llm_sdk_leak + check_promptbuilder_usage green).

Test fixtures: `test_formation.py` uses `adapters._testing.mock_clients.MockChatClient` (`chat_call_count`) + `_ExtractorStub` / `_SummarizerStub` recording dispatch calls. Drive-through DB inspector: `%TEMP%/.../scratchpad/db_57152.py` → `artifacts/db-evidence-combined-formation.txt`.

## 4. Cross-Category Contracts (17.md single-source)

No NEW cross-category ABC contract. `MemoryFormationWorker` is a 範疇-3 composition over the existing `MemoryExtractor` + `SessionSummarizer` (both 範疇 3); `write_facts` / `store_summary` are additive public methods on those existing classes. The worker rides the existing post-send BackgroundTask seam (範疇 12 cross-cutting / chat router) the 57.149/151 callers used. 17.md needs no new entry (additive within Cat 3's existing surface).

## 5. Open Invariants (deferred — NOT verified this sprint)

- A formal real-Azure A/B harness measuring combined-vs-separate formation QUALITY (does asking for both in one call degrade either half?) — `AD-Memory-Combined-Formation-AB-Quality` (mirrors the 57.136/137/138 benchmark pattern; the flag + drive-through suffice for this sprint, gpt-5.2 handled the combined ask cleanly).
- The recall final-answer carryovers surfaced at Leg-2 drive-through (NOT changed by this sprint): `AD-Verification-Judge-Memory-Inject-Blind` (57.149 — judge rejects memory-injected recall as fabrication) + cross-session identity-conflict synthesis (a dev-fixture artifact of reusing one user with multiple fictional personas).
- Incremental (non-full-ledger) summarization — `AD-Memory-Session-Summary-Incremental` (57.151 carryover, unchanged).
- `extracted_to_user_memory` coordination flag — `AD-Memory-Session-Summary-Extract-Coordination` (57.151 carryover, unchanged).

## 6. Rollback

Backend-only, additive, flag-gated. Runtime disable: `CHAT_MEMORY_COMBINED_FORMATION=false` → the proven two-call path (byte-identical to 57.151), no redeploy. Code revert: the worker + the two dispatch methods are additive (the single-call methods are unchanged in behavior); removing `formation.py` + reverting the 3 wiring edits (ctx field, build function, `_maybe_auto_extract`) restores the 57.151 two-call hook. Estimated revert: < 0.5 day. No migration to undo (no schema change).

## 7. References

- `53-memory-auto-extract-design.md` — the 57.149 extractor half (amended here).
- `54-memory-session-recall-design.md` — the 57.151 summarizer half (amended here).
- `agent_harness/memory/formation.py` — `MemoryFormationWorker`.
- `agent_harness/memory/extraction.py:write_facts` / `session_summarizer.py:store_summary` — the reused dispatch halves.
- `api/v1/chat/router.py:_maybe_auto_extract` — the post-send seam.
- CHANGE-119 · `sprint-57-152-plan.md` · `sprint-57-152/artifacts/` (drive-through).

## 8. 8-Point Quality Gate self-check

1. ✅ Section headers map to US (§1 US-1/2/3/4). 2. ✅ Every technical claim has file:line. 3. ✅ Decision matrix (§2, 5 decisions with rejected alternatives). 4. ✅ Verification commands (§3, pytest per invariant + run_all). 5. ✅ Test fixture reference (§3 MockChatClient + DB inspector). 6. ✅ Open invariants explicitly bounded (§5, verified vs deferred incl. the Leg-2 carryovers). 7. ✅ Rollback path (§6, env flag + code revert). 8. ✅ 17.md cross-ref (§4 — additive, no new contract).
