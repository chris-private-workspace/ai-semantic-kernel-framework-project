# Sprint 57.149 Plan — Memory Option-B deterministic post-send fact extraction

**Summary**: Wire the already-built-but-unwired `MemoryExtractor` (Cat 3, since 51.2) onto the chat main flow — after every send completes, deterministically scan the conversation for durable user facts and persist them to `UserLayer`, so the platform forms memory **even when the agent never calls `memory_write`**. This closes the formation-reliability half of `AD-Memory-Formation-Auto-Extract` (a 57.148 carryover) and is **Slice 2** of the memory-formation arc (57.148 = Slice 1: identity write nudge + always-on inject). Backend-only (NO migration / wire / frontend). Drive-through MANDATORY (user-facing memory). **Spike sprint → design note 53 required.**

**Status**: Approved-to-execute (user 2026-06-28 AskUserQuestion trail: grounding 線 → memory Option B 確定性抽取 → trigger strategy = every-send, env-gated default ON)
**Branch**: `feature/sprint-57-149-memory-auto-extract`
**Base**: `main` HEAD `694e0062` (Sprint 57.148 flip merge; == feature `4fe02965`)
**Slice**: closes `AD-Memory-Formation-Auto-Extract`; memory-formation arc Slice 2/N
**Scope decisions**: (a) trigger = **every send, synchronous after `LoopCompleted`**, cheap tier, env-gated `CHAT_MEMORY_AUTO_EXTRACT` **default ON** (b) dedup = **lightweight prompt-level** (read existing `profile()` → extractor instructed to emit only NEW facts) — full upsert-by-key DEFERRED (c) extractor-written rows tagged `source="auto_extract"` for drive-through attribution + audit + future dedup (additive `UserLayer.write` param) (d) backend-only — NO migration / wire (stays 26) / frontend; `CHAT_MEMORY_AUTO_EXTRACT=false` = byte-identical to 57.148

---

## 0. Background

### The gap (`AD-Memory-Formation-Auto-Extract`)

57.148 shipped **Option A** (a system-prompt nudge → the agent *discretionarily* calls `memory_write(scope=user)`). Formation therefore still depends on the agent **choosing** to write: a subtle fact, an ignored nudge, or a model that just answers without tool-calling → **nothing is persisted**. The `MemoryExtractor` that would close this (a deterministic post-conversation scan) has existed since Sprint 51.2 but **was never wired to any main flow** (manual-trigger only; the CARRY-027 auto-trigger queue never landed).

### Why it matters (the missing capability)

This is the **長壽個人代理** vision pillar (reality-audit §9; baseline 5%). Deterministic formation means the platform remembers durable user facts **independent of the agent's self-flagging discipline** — the difference between "the agent might remember if it bothers to write" and "the platform reliably forms memory from what the user said".

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `694e0062`) | Anchor |
|-------|--------------------------------------|--------|
| Extractor exists, never wired | `MemoryExtractor.extract_session_to_user` — cheap LLM extractor (`temperature=0`) → parse JSON `[{content, confidence}]` → `UserLayer.write`; provider-neutral (ChatClient ABC) | `agent_harness/memory/extraction.py:55-111` |
| No main-flow driver | nothing in the chat path calls it; CARRY-027 queue never built | `extraction.py:13-14` (docstring) |
| Loop-completion seam | the SSE driver sees `LoopCompleted` after `loop.run()` finishes | `api/v1/chat/router.py:796` |
| User layer available to build extractor | the chat memory deps dict already constructs a real `UserLayer` | `api/v1/chat/_category_factories.py:303` |
| Full message ledger available | per-session Cat-3 ledger (own tenant-scoped session, 57.127/143) | `_category_factories.py:378` `make_chat_message_store` → `DBMessageStore` |
| `UserLayer.write` always INSERTs | new `uuid4()` per write; `conflict_resolver` is READ-side only (picks a hint), not write-side dedup | `user_layer.py:135` / `conflict_resolver.py:50` |
| Cheap tier available | the verification judge already runs on `profile.cheap` (57.97) | `handler.py:722` |

→ The fix must: build the extractor at composition (cheap tier + user layer), thread it to the SSE driver, and after `LoopCompleted` load this send's messages + read existing profile facts, then run the extractor (prompt: only NEW facts) and persist — all env-gated, synchronous, graceful-degrade.

### The design (backend-only: 1 factory + 1 handler thread + 1 router post-completion hook + extractor dedup param + env gate + source tag + tests)

```
NEW   _category_factories.py  make_chat_memory_extractor(chat_client_cheap, user_layer) -> MemoryExtractor | None
EDIT  extraction.py           extract_session_to_user(..., known_facts: list[str] = []) — prompt lists known facts → "emit only NEW"
                              + write tagged source="auto_extract"
EDIT  user_layer.py           write(..., source: str | None = None)  — additive; default None = 57.148 byte-identical
EDIT  handler.py              build the extractor (cheap tier + memory_layers["user"]) + return it alongside the loop / thread to router
EDIT  router.py               after LoopCompleted (env-gated): load ledger + profile → extractor.extract_session_to_user → best-effort
EDIT  core/config/__init__.py chat_memory_auto_extract: bool = True   (env CHAT_MEMORY_AUTO_EXTRACT)
```

**Why every-send-synchronous over background** (the alternative considered): a `LoopCompleted`-time fire-and-forget background task hits the 57.97/57.143 orphaned-spawn-worker + request-session-lifecycle traps. Synchronous (after the answer has already streamed) only delays the SSE connection close by ~1-2s — the answer is already on screen — and keeps the DB session lifecycle deterministic. Cost is one cheap-tier call per send (the cheap tier makes default-ON affordable, matching the 57.148 nudge-default-ON posture so "the platform actually remembers" is the default).

### Ground truth (recon head-start — code read on `main` HEAD `694e0062`; ALL re-verified §checklist 0.1)

- `extraction.py:66-111` — `extract_session_to_user(*, session_id, tenant_id, user_id, messages, trace_context=None)` returns `list[UUID]` of new rows; `[]` on empty messages / empty extraction.
- `extraction.py:41-52` — `_EXTRACTION_PROMPT` (the dedup hook: append a "already known, do not repeat" block).
- `_category_factories.py:264-307` — `make_chat_memory_deps(db) -> (MemoryRetrieval, layers)`; `layers["user"]` is the real `UserLayer`.
- `handler.py:722` — `profile.cheap` is the resolved cheap ChatClient (verification judge tier).
- `handler.py:581` — `make_chat_prompt_builder(chat_client, memory_retrieval=...)`; the same `memory_retrieval` exposes `profile(tenant_id, user_id, top_k)` (57.148).
- `router.py:733-797` — `_stream_loop_events` drives `loop.run()`; `LoopCompleted` at `:796` (`natural_completion=True`).
- `router.py:662-679` — `_stream_loop_events` signature (the thread target for the extractor + ids).

**Baselines (57.148 closeout)**: pytest 2999 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — filled in §checklist 0.1)

- **D-msgstore-load** — grep `DBMessageStore.load` / `MessageStore` ABC: confirm a load method returns the full ledger as `list[Message]` (extractor input); confirm the boundary (whole ledger vs this-send) + whether a `_cap` is needed.
- **D-write-source** — grep `MemoryUser` ORM: confirm a `source` column exists so `UserLayer.write(source=...)` persists it (vs metadata JSONB fallback).
- **D-extractor-msg-type** — confirm `MemoryExtractor` consumes `agent_harness._contracts.Message` and the ledger yields the same type (no adapter needed).
- **D-handler-return** — `build_real_llm_handler` returns ONLY the loop (`:789`); confirm how to surface the extractor to the router (return tuple vs build in router from deps) — pick the thinner thread.
- **D-cheap-tier** — confirm `profile.cheap` is in scope where the extractor is built.

## 1. Sprint Goal

On every chat send, when `CHAT_MEMORY_AUTO_EXTRACT` is on, the platform deterministically extracts durable user facts from the just-completed conversation and persists them to user memory — **proven by a drive-through where the agent does NOT call `memory_write` in the run, yet a NEW session recalls the fact** (formation via extractor alone, recall via the 57.148 always-on `profile()` inject). Gates all green + design note 53 + CHANGE-116.

## 2. User Stories

- **US-1** (extractor wiring): 作為平台，我希望每次對話完成後自動掃描抽取 durable user facts，以便即使 agent 沒主動 `memory_write` 也能形成記憶。
- **US-2** (prompt-level dedup): 作為平台，我希望抽取前先讀已知 facts 並只抽新的，以便不重複寫入相同記憶（在完整 upsert-by-key 落地前的輕量防重）。
- **US-3** (env gate + cheap tier + source tag): 作為營運者，我希望此功能可 env 開關、跑在 cheap tier、寫入標記 `source="auto_extract"`，以便控成本 + 審計 + 區分 nudge-vs-extract 來源。
- **US-4** (drive-through, MANDATORY): 作為用戶，我陳述了一個 durable fact 但 agent 該輪沒呼叫 `memory_write`，以便新 session 仍記得我（證明 extractor 獨立形成記憶）。
- **US-5** (closeout): CHANGE-116 + design note 53 + retrospective + navigators.

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO wire event / NO frontend / NO loop.py edit)

```
NEW   backend/src/api/v1/chat/_category_factories.py   make_chat_memory_extractor(chat_client, user_layer) -> MemoryExtractor | None
EDIT  backend/src/agent_harness/memory/extraction.py   + known_facts param → prompt dedup block; + source="auto_extract" on write
EDIT  backend/src/agent_harness/memory/layers/user_layer.py   write(..., source: str | None = None)  (additive)
EDIT  backend/src/api/v1/chat/handler.py               build extractor (profile.cheap + memory_layers["user"]) + surface to router
EDIT  backend/src/api/v1/chat/router.py                _stream_loop_events: after LoopCompleted (env-gated) → load ledger + profile → extract (best-effort)
EDIT  backend/src/core/config/__init__.py              chat_memory_auto_extract: bool = True
UNTOUCHED  agent_harness/orchestrator_loop/loop.py · prompt_builder/builder.py · all wire/codegen/frontend
```

### 3.1 Extractor factory (US-1) — `_category_factories.py`

- `make_chat_memory_extractor(chat_client, user_layer) -> MemoryExtractor | None`: returns `MemoryExtractor(chat_client, user_layer)` when both present; `None` otherwise (mirrors the all-present-or-None guard of `make_chat_message_store`). `chat_client` = the cheap tier; `user_layer` = `memory_layers["user"]` from `make_chat_memory_deps`.

### 3.2 Extractor build + thread to router (US-1) — `handler.py` + `router.py`

- `build_real_llm_handler` already holds `profile.cheap` (`:722`) + `memory_layers` (`:360`). Build the extractor there. Surface it to the router via the thinner of: (a) return `(loop, extractor)` tuple, or (b) build it in the router from the same deps — **decided Day-0 D-handler-return** (favor the smaller diff).
- `_stream_loop_events` gains an `memory_extractor: MemoryExtractor | None = None` param (+ the cheap-call is fine; default None = no-op).

### 3.3 Post-completion extraction hook (US-1) — `router.py`

- After the `async for` loop over `loop.run()` finishes (natural completion), env-gated on `settings.chat_memory_auto_extract` AND `memory_extractor is not None` AND `user_id is not None`:
  1. load this session's messages from `message_store` (boundary per D-msgstore-load; cap to recent K if needed),
  2. read existing facts via `memory_retrieval.profile(tenant_id, user_id)` → `known_facts: list[str]`,
  3. `await memory_extractor.extract_session_to_user(session_id, tenant_id, user_id, messages, known_facts=known_facts, trace_context=...)`,
  4. wrap in try/except → log + swallow (NEVER break the SSE stream / fail the send). Runs after the answer has streamed (only the connection-close is delayed).

### 3.4 Prompt-level dedup (US-2) — `extraction.py`

- `extract_session_to_user(..., known_facts: list[str] = [])`: when non-empty, append a block to `_EXTRACTION_PROMPT` — "The following facts are ALREADY remembered; do NOT repeat them, emit only NEW durable facts: <list>". MVP best-effort (the model may still echo); full guaranteed dedup = `AD-Memory-User-Upsert-By-Key` (out of scope).

### 3.5 env gate + source tag (US-3) — `config` + `extraction.py` + `user_layer.py`

- `chat_memory_auto_extract: bool = True` (env `CHAT_MEMORY_AUTO_EXTRACT`). `false` → the §3.3 hook is skipped → byte-identical to 57.148.
- `UserLayer.write(..., source: str | None = None)`: additive; persists into the `MemoryUser.source` column (D-write-source) or metadata fallback. Default `None` = all existing callers unchanged. `MemoryExtractor` passes `source="auto_extract"`.

### 3.x What is explicitly NOT done

- **Guaranteed write-side dedup / upsert-by-key** → `AD-Memory-User-Upsert-By-Key` (this sprint only does prompt-level best-effort).
- **Async/queue extraction (Celery/Redis)** → CARRY-027 (this sprint is synchronous-after-completion).
- **Cross-session CONVERSATION recall + session-summary → Layer 5** → `AD-Memory-Formation-Session-Recall` (缺口 2).
- **Semantic / Qdrant axis** → CARRY-026.
- **Per-tenant on/off override** → settings-only this sprint (anti-AP-6; a future C3-seam follow-on).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 392 (0 err) · run_all 11/11 · pytest 2999 + new · Vitest 922 (untouched) · mockup 51 (`diff` empty, untouched) · `npm run lint && npm run build` (NO `--silent`, untouched) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.3/US-4 drive-through (MANDATORY — real UI + backend + Azure).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/chat/_category_factories.py` | EDIT (new `make_chat_memory_extractor`) |
| 2 | `backend/src/agent_harness/memory/extraction.py` | EDIT (`known_facts` param + `source` on write) |
| 3 | `backend/src/agent_harness/memory/layers/user_layer.py` | EDIT (additive `source` param) |
| 4 | `backend/src/api/v1/chat/handler.py` | EDIT (build extractor + surface) |
| 5 | `backend/src/api/v1/chat/router.py` | EDIT (post-completion extraction hook) |
| 6 | `backend/src/core/config/__init__.py` | EDIT (`chat_memory_auto_extract`) |
| 7 | `backend/tests/unit/agent_harness/memory/test_extraction.py` | EDIT (+known_facts + source tests) |
| 8 | `backend/tests/integration/memory/test_extraction_worker.py` | EDIT (+dedup + source integration) |
| 9 | `backend/tests/.../test_chat_*` (router/handler extraction wiring) | EDIT (+gate ON/OFF + best-effort swallow) |
| 10 | `docs/.../sprint-57-149-{plan,checklist}.md` | NEW |
| 11 | `docs/.../agent-harness-execution/phase-57/sprint-57-149/{progress,retrospective}.md` | NEW |
| 12 | `docs/03-implementation/agent-harness-planning/53-memory-auto-extract-design.md` | NEW (spike design note) |
| 13 | `claudedocs/4-changes/feature-changes/CHANGE-116-memory-auto-extract.md` | NEW |
| — | `agent_harness/orchestrator_loop/loop.py` · `prompt_builder/builder.py` · any wire/codegen/frontend | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `CHAT_MEMORY_AUTO_EXTRACT` default ON; `make_chat_memory_extractor` returns a real `MemoryExtractor` on the chat path; `=false` makes the §3.3 hook a no-op (byte-identical to 57.148).
2. After a send completes, the extractor runs synchronously (cheap tier), best-effort (an extractor exception is logged + swallowed — the send + SSE stream never fail).
3. Prompt-level dedup: when `known_facts` is non-empty the prompt instructs "only NEW facts"; extractor-written rows carry `source="auto_extract"`.
4. Multi-tenant: extracted writes inherit the originating request's tenant_id + user_id (never cross-tenant); covered by an isolation test.
5. **Drive-through PASS (MANDATORY, real UI + backend + Azure LLM)** — user states a durable fact in a phrasing where the agent does NOT call `memory_write` that run (verified via Inspector: no `memory_write` tool call); after completion the extractor writes the fact (DB row `source="auto_extract"`); a NEW session recalls it via the 57.148 always-on `profile()` inject; a different user does not. Screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Memory-Formation-Auto-Extract` CLOSED; CHANGE-116 + design note 53 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 extractor factory + build + router post-completion hook (synchronous, env-gated)
- [ ] US-2 prompt-level dedup (`known_facts` → "only NEW")
- [ ] US-3 env gate + cheap tier + `source="auto_extract"` tag
- [ ] US-4 drive-through (agent does NOT memory_write → extractor forms → new session recalls → isolation)
- [ ] US-5 CHANGE-116 + design note 53 + retrospective + navigators

## 7. Workload Calibration

- Scope class **`memory-formation-extract-spike` 0.60** (NEW class, sibling to 57.148 `memory-formation-identity-spike` 0.60 — the **2nd** memory-formation-* spike; honours the 57.148 retro "if a 2nd memory-formation-*-spike lands > 1.20, re-point toward 0.85"). Real-code core (factory + extractor dedup + router hook + `UserLayer.write` source + env gate + tests + drive-through) holds the 0.60 spike multiplier per the 57.137 lesson (a >~3 hr implementation core, NOT a tiny-code-wrapped-in-ceremony 0.85 re-point).
- **Agent-delegated: no** (parent-direct; `agent_factor` 1.0 → 3-segment form).
- Bottom-up est ~7-9 hr (factory + handler/router thread ~2 / extractor dedup + source ~1.5 / env gate ~0.5 / tests ~2 / drive-through ~2-3) → class-calibrated commit ~4.5-5.5 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Cost: every send +1 LLM call | cheap tier (`profile.cheap`, 57.97); env gate to disable; `temperature=0` short extractor prompt |
| dup amplification (every send re-scans) | prompt-level dedup (read `profile()` first); `source="auto_extract"` for audit; full upsert deferred to `AD-Memory-User-Upsert-By-Key` |
| SSE close latency (~1-2s after answer streamed) | synchronous AFTER the answer streams (answer already on screen); only the connection-close is delayed — acceptable vs the orphan/session risk of background |
| Extractor failure breaks the send | §3.3 try/except → log + swallow; NEVER fail the send or the SSE stream |
| **Risk Class E** (env-loaded behavior masked by stale `--reload`) | Day-3 clean restart: kill stale reloader + orphan spawn-workers, confirm sole live worker via `Win32_Process` PID/PPID/StartTime, set `CHAT_MEMORY_AUTO_EXTRACT` BEFORE restart, capture startup log |
| Drive-through can't prove extractor (vs 57.148 nudge) attribution | choose a phrasing where the agent answers WITHOUT `memory_write` (verify via Inspector: 0 memory_write tool calls that run); `source="auto_extract"` DB tag confirms provenance |
| message-ledger boundary unknown | Day-0 D-msgstore-load resolves whole-ledger vs this-send + cap-K before the hook is coded |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Guaranteed write-side dedup / upsert-by-key — `AD-Memory-User-Upsert-By-Key`.
- Async/queue extraction (Celery/Redis) — CARRY-027.
- Cross-session conversation recall + session-summary → Layer 5 — `AD-Memory-Formation-Session-Recall` (缺口 2).
- Memory semantic / Qdrant axis — CARRY-026.
- Per-tenant on/off override of auto-extract — future C3-seam follow-on.
