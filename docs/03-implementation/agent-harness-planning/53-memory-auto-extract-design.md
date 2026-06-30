# Memory-Formation Slice 2 — Option-B Deterministic Post-Send Extraction (Design Note)

**Purpose**: Extract the verified design of the deterministic memory-formation path (a cheap-tier `MemoryExtractor` run after every send, off the SSE generator) from the Sprint 57.149 implementation — the half that makes the platform form memory WITHOUT relying on the agent's discretion.
**Category / Scope**: Cat 3 (Memory) + Cat 5 (PromptBuilder profile dedup) + Cat 2 (chat wiring) / Phase 57 / Sprint 57.149
**Created**: 2026-06-28
**Status**: Active (verified ratio ~95%)
**Author**: self (solo-dev)

> **Modification History**
> - 2026-06-28: Initial extract from Sprint 57.149 (AD-Memory-Formation-Auto-Extract)

---

## 1. Spike Summary (US → what shipped)

Second slice of the memory-formation arc — closes `AD-Memory-Formation-Auto-Extract`. Makes the platform persist durable user facts deterministically after every conversation, independent of whether the agent chose to call `memory_write` (the 57.148 Option-A nudge is discretionary; this is the deterministic safety net).

- **US-1** wiring: a cheap-tier `MemoryExtractor` runs after every real_llm send (env-gated, default ON).
- **US-2** dedup: read existing facts via `profile()` first → a prompt-level "only NEW facts" block.
- **US-3** gate + cheap tier + `source="auto_extract"` provenance tag.
- **US-4** 3-leg drive-through (formation / recall / isolation, real Azure). **US-5** closeout.

## 2. Decision Matrix

### Extraction trigger timing

| Option | Mechanism | Decision |
|--------|-----------|----------|
| **Every send, after completion** | run the extractor on the just-finished conversation each send | **CHOSEN** — deterministic; cheap tier makes default-ON affordable; matches the 57.148 nudge default-ON posture |
| Only at "session end" | wait for a session-close signal | rejected — chat-v2 has NO explicit session-end (multiple bounded sends; client can just close the tab) |
| Only at ≥N user turns | gate on conversation length | rejected — needs an extra turn-counting heuristic for little gain (cheap tier already bounds cost) |

### Where the extraction runs (the key correctness decision)

| Option | Mechanism | Decision |
|--------|-----------|----------|
| **Starlette `BackgroundTask`** | runs after the SSE response body, in Starlette's managed lifecycle | **CHOSEN (Day-3 evolution)** — off the streaming generator; does NOT block the connection-close; NOT a fire-and-forget orphan |
| Synchronous inside `_stream_loop_events` | `await` after the loop, before the generator's `finally` | shipped Day 1-2, PASSED drive-through, but blocks the SSE connection-close ~1-2s; superseded |
| Fire-and-forget `asyncio.create_task` | detached task | rejected — the 57.97/57.143 orphaned-spawn-worker + request-session-lifecycle trap (this is what the plan's "synchronous over background" rationale feared — but a Starlette BackgroundTask is NOT this) |

### Dedup strategy

| Option | Mechanism | Decision |
|--------|-----------|----------|
| **Prompt-level (read profile, "only NEW")** | seed the extractor prompt with already-known facts | **CHOSEN** — lightweight; reuses the 57.148 `profile()` |
| Guaranteed write-side upsert-by-key | dedup at `UserLayer.write` | deferred — `AD-Memory-User-Upsert-By-Key` (MVP tolerates dup rows; `profile()` top-k by confidence) |

## 3. Verified Invariants (file:line + verification)

1. **`source="auto_extract"` tag on a real column** — `UserLayer.write(source=...)` writes the pre-existing `MemoryUser.source` column (`infrastructure/db/models/memory.py:230`); no migration. `agent_harness/memory/layers/user_layer.py`. Verify: `test_extraction.py::test_extract_tags_source_auto_extract` + the drive-through DB rows (`[auto_extract]`).
2. **Prompt-level dedup is additive** — `extract_session_to_user(known_facts=...)` → `_build_known_block`; empty/None/blank-only → "" (51.2 prompt byte-identical). `agent_harness/memory/extraction.py`. Verify: `test_extraction.py::test_build_known_block_empty_returns_blank` + `::test_known_facts_reach_extraction_prompt` + `::test_no_known_facts_prompt_has_no_dedup_block`.
3. **Cheap-tier, self-contained factory** — `build_chat_memory_extractor` binds `profile.cheap` (not the action tier) + the real `UserLayer`; SOFT-None on missing env/db/session/tenant (never raises, unlike `build_real_llm_handler`). `api/v1/chat/handler.py`. Verify: `test_handler.py::test_build_chat_memory_extractor_none_without_azure_env` + `::test_build_chat_memory_extractor_none_without_db_session_tenant` + `::test_build_chat_memory_extractor_returns_context_on_cheap_tier`.
4. **0 caller breakage** — the extractor is NOT threaded through `build_handler` (which returns the loop alone); the router calls `build_chat_memory_extractor` separately → none of `build_handler`'s ~12 callers (router / resume service / ~10 unit tests) changed. `api/v1/chat/handler.py` + `router.py`. Verify: `test_handler.py` (all pre-existing builder tests still green).
5. **Best-effort, off the generator** — `_maybe_auto_extract` runs as a `BackgroundTask` (`router.py` `StreamingResponse(background=...)`); a failure is logged + swallowed (never surfaces to the user). Verify: `test_memory_auto_extract.py::test_swallows_extractor_failure` + `::test_no_op_when_ctx_none` + `::test_no_op_when_no_user` + `::test_no_op_when_empty_ledger`.
6. **Dedup facts threaded from profile()** — the hook reads `profile(tenant_id, user_id)` → `known_facts` → the extractor. Verify: `test_memory_auto_extract.py::test_runs_extract_with_ledger_and_known_facts` (asserts the profile read + the known_facts arg).
7. **env gate = byte-identical off** — `CHAT_MEMORY_AUTO_EXTRACT=false` → the router builds no ctx → no-op (57.148 byte-identical). `core/config/__init__.py` + `router.py`. Verify: code path (the ctx build is `if req.mode == "real_llm" and settings.chat_memory_auto_extract`).
8. **Provider neutrality preserved** — the extractor issues its LLM call through the `ChatClient` ABC (no openai/anthropic import in `agent_harness/memory`). Verify: `v2 lints llm_sdk_leak` (25 green) + `test_extraction_worker.py::test_extraction_uses_chat_client_abc_no_sdk_leak`.
9. **Drive-through (real, NOT gate-only)** — dan states "Project Aurora, Oracle→PostgreSQL, Q3" → `[auto_extract]` conf 0.99 row; NEW session recalls it via `profile()` inject (Inspector read of `memory_user:5d487f86`); priya (different user) → "我不知道你是誰" (0 leak). BackgroundTask re-drive (priya) → `[auto_extract]` conf 0.78 SOC 2 row. Reproduce: progress.md Day 3 (real Azure gpt-5.2). Screenshots in `sprint-57-149/artifacts/`.

## 4. Cross-Category Contracts

- **No new 17.md contract / wire event / DB migration.** Reuses: `MemoryExtractor` (Cat 3, Sprint 51.2 — manual-trigger until now), `UserLayer` (Cat 3), `MemoryRetrieval.profile()` (Cat 3/5, Sprint 57.148), `DBMessageStore` (Cat 7, Sprint 57.127), the cheap `profile.cheap` tier (Sprint 57.97), and Starlette's `BackgroundTask`.
- `UserLayer.write` gains an additive `source: str | None = None` (default preserves all callers; only `MemoryExtractor` passes `"auto_extract"`). `MemoryExtractor.extract_session_to_user` gains `known_facts: list[str] | None = None` (additive). `ChatMemoryExtractContext` + `build_chat_memory_extractor` are NEW chat-layer helpers (not 11-category ABCs).

## 5. Open Invariants (deferred — NOT verified this sprint)

| Item | Status | Where |
|------|--------|-------|
| Guaranteed write-side dedup (UserLayer upsert-by-key) | deferred — MVP tolerates dup rows | `AD-Memory-User-Upsert-By-Key` |
| Async/queue extraction (Celery/Redis) | deferred — this is synchronous-after-response | CARRY-027 |
| Cross-session CONVERSATION recall + session-summary → Layer 5 | deferred | `AD-Memory-Formation-Session-Recall` (缺口 2) |
| In-loop verification judge false-positive on memory-injected recalls | NEW finding (Day 3) | `AD-Verification-Judge-Memory-Inject-Blind` |
| Memory semantic / Qdrant axis | unblocked, NOT wired | CARRY-026 |
| Per-tenant on/off of auto-extract | settings-only this sprint (anti-AP-6) | future C3-seam follow-on |
| Disconnect-mid-extraction durability (BackgroundTask on a CancelledError response) | best-effort; not exercised | acceptable for MVP (formation is best-effort) |

**Boundary statement**: verified = deterministic cheap-tier extraction after every real_llm send (env-gated) + prompt-level dedup + `source="auto_extract"` provenance + per-user/per-tenant isolation, end-to-end on the real chat path (write → cross-session recall → isolation), with the extraction off the SSE generator via BackgroundTask. NOT verified = guaranteed write-side dedup, async queue, cross-session conversation recall, semantic axis, the verification-judge-memory-blindness fix.

## 6. Rollback

- Per-request: `CHAT_MEMORY_AUTO_EXTRACT=false` OR `user_id=None` → no ctx built → BackgroundTask is a no-op → byte-identical to 57.148.
- Full revert: revert the 6 src EDITs (`user_layer.py`/`extraction.py`/`config`/`handler.py`/`router.py`) + the 5 test files. < 1 hr; no migration (the `source` column pre-existed + is nullable), no sentinel, no schema state (the written `memory_user` rows are inert data — deleting them resets). The 57.148 query-gated + nudge path is untouched underneath.

## 7. References

- `agent_harness/memory/{extraction,layers/user_layer,retrieval}.py` · `api/v1/chat/{handler,router}.py` · `core/config/__init__.py`
- `infrastructure/db/models/memory.py:230` (`MemoryUser.source`) · `agent_harness/observability/tracer.py:200` (the pre-existing OTel-on-SSE-close noise source)
- `.claude/rules/multi-tenant-data.md` (user/tenant isolation) · CHANGE-116 · Sprint 57.149 plan/checklist/progress/retrospective
- `52-memory-formation-identity-design.md` (Slice 1 — the always-on `profile()` inject this slice's writes feed) · `memory/feedback_drive_through_over_paper_metrics.md`

## 8. Modification History

- 2026-06-28: Initial creation (Sprint 57.149) — Option-B deterministic post-send extraction design extract.
