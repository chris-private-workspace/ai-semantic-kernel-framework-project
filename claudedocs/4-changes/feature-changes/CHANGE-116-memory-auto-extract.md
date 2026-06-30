# CHANGE-116: Memory Option-B deterministic post-send fact extraction

**Date**: 2026-06-28
**Sprint**: 57.149
**Scope**: Cat 3 (Memory) + Cat 5/2 (chat wiring) — backend-only
**AD**: closes `AD-Memory-Formation-Auto-Extract` (57.148 carryover); memory-formation arc Slice 2

## Problem

57.148 shipped **Option A** — a system-prompt nudge so the agent *discretionarily* calls `memory_write(scope=user)`. Formation therefore depended on the agent **choosing** to write: a subtle fact, an ignored nudge, or a model that just answers without tool-calling → **nothing persisted**. The platform could not reliably form memory from what the user actually said.

## Root Cause

The `MemoryExtractor` that would close this (a deterministic post-conversation LLM scan → `UserLayer` write) has existed since Sprint 51.2 but was **never wired to any main flow** (manual-trigger only; the CARRY-027 auto-trigger queue never landed).

## Solution

Wire `MemoryExtractor` onto the chat path so it runs deterministically after **every** send (env-gated `CHAT_MEMORY_AUTO_EXTRACT`, default ON, cheap tier):

- `agent_harness/memory/layers/user_layer.py` — `write()` additive `source: str | None` → real `memory_user.source` column (NO migration; column pre-existed).
- `agent_harness/memory/extraction.py` — `extract_session_to_user(known_facts=...)` → `_build_known_block` prompt-level dedup ("emit only NEW facts"; empty = 51.2 byte-identical) + tags every write `source="auto_extract"`.
- `core/config/__init__.py` — `chat_memory_auto_extract: bool = True`.
- `api/v1/chat/handler.py` — `ChatMemoryExtractContext` (extractor + retrieval + message_store) + `build_chat_memory_extractor(model_policy, db, session_id, tenant_id)` (cheap `profile.cheap` tier; SOFT-None on missing env/db/session/tenant; self-contained so it threads NOTHING through `build_handler` → 0 of its ~12 callers touched).
- `api/v1/chat/router.py` — `_maybe_auto_extract` helper (gate + `profile()` dedup + best-effort swallow) run as a Starlette **`BackgroundTask`** after the SSE body (see §Design note).

The hook reads existing facts via the 57.148 `profile()` first (prompt-level dedup) and writes durable user facts to `UserLayer` tagged `source="auto_extract"` — distinguishable from agent-driven `memory_write` rows.

### Design note — BackgroundTask over synchronous-in-generator

The plan chose synchronous (fearing a fire-and-forget `asyncio.create_task` orphan, 57.97/57.143). The Day-3 drive-through showed the synchronous post-loop await blocks the SSE connection-close. Starlette `BackgroundTask` is NOT a fire-and-forget orphan (it runs in Starlette's managed response lifecycle), so it's strictly better: extraction runs after the response body, off the streaming generator, with its own DB sessions. (The `async generator ignored GeneratorExit` / OTel `Failed to detach context` ERROR logs were investigated and found PRE-EXISTING — `tracer.py:200 _span_cm`, the 57.71/57.142 OTel-on-SSE-close issue — NOT caused by the extraction.)

## Verification

- Gates: mypy `src` 0/392 · v2 lints 25 (incl. llm_sdk_leak) · pytest **3013 passed/6 skipped** (2999 → +14) · black/isort/flake8 clean · FE untouched.
- **Drive-through PASS** (real chat-v2 + real Azure gpt-5.2), 3 legs:
  1. **Formation** — dan states "Project Aurora, Oracle→PostgreSQL, Q3" → DB `[auto_extract]` conf 0.99 'Chris is currently handling Project Aurora…' (cheap-tier extractor ran).
  2. **Recall** — NEW session, 0-keyword-overlap question → agent recalls Aurora; Inspector shows `profile()` read the extractor row `memory_user:5d487f86`.
  3. **Isolation** — priya (different user) → "我不知道你是誰" (0 leak; per-user `WHERE user_id`).
  - Re-drive on the BackgroundTask version (priya, baseline 0) → `[auto_extract]` conf 0.78 SOC 2 row written after the response. Screenshots in `sprint-57-149/artifacts/`.

## Impact

Backend-only. `CHAT_MEMORY_AUTO_EXTRACT=false` OR `user_id=None` → byte-identical to 57.148. No migration / wire (stays 26) / frontend / loop.py edit. Adds one cheap-tier LLM call per real_llm send (default ON; env-disable to opt out).

**Carryover**: `AD-Memory-User-Upsert-By-Key` (guaranteed write-side dedup; `UserLayer.write` still INSERTs) · `AD-Memory-Formation-Session-Recall` (缺口 2) · `AD-Verification-Judge-Memory-Inject-Blind` (Day-3 finding: the in-loop judge false-positive-REJECTs memory-injected recalls) · CARRY-026 (semantic axis) · CARRY-027 (async queue).
