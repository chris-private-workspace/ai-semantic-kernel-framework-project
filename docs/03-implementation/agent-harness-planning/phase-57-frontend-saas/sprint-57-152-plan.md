# Sprint 57.152 Plan — combine post-send extract + summarize into one LLM call

**Summary**: The chat post-send memory formation makes TWO cheap-tier LLM calls per send — `MemoryExtractor` (durable user facts → `UserLayer`, 57.149) + `SessionSummarizer` (rolling conversation summary → `memory_session_summary`, 57.151). This sprint introduces a `MemoryFormationWorker` that COMPOSES the two existing workers and (default) makes ONE combined LLM call returning both the facts array and the summary object, halving background token + latency per send. Closes `AD-Memory-Formation-Combine-Extract-Summarize`. Backend-only, NO migration / wire / frontend. A `chat_memory_combined_formation` flag (default ON) gates combined-vs-separate so the proven two-call path stays a one-env-var fallback (de-risks any combined-prompt quality regression AND keeps both single-call methods reachable on the chat path). Drive-through is MANDATORY (the post-send formation runs on the real chat-v2 main flow). A short design note (55) amends the 53+54 formation architecture.

**Status**: Approved-to-execute (user picked `AD-Memory-Formation-Combine-Extract-Summarize` from the Sprint 57.151 closeout candidate list, 2026-06-30)
**Branch**: `feature/sprint-57-152-memory-combined-formation`
**Base**: `main` HEAD `a6e8d586` (Sprint 57.151 flip PR #357 merged — cross-session conversation recall closed)
**Slice**: closes `AD-Memory-Formation-Combine-Extract-Summarize` (a memory-formation arc follow-on; the arc 57.148→151 is closed, this is an efficiency consolidation over it)
**Scope decisions**: (a) NEW `MemoryFormationWorker` COMPOSES the existing `MemoryExtractor`+`SessionSummarizer` (does NOT replace/delete them — avoids AP-2/AP-4 orphaning); (b) default combined = 1 call, env fallback to the proven 2-call path; (c) reuse the dispatch halves (`write_facts`/`store_summary` extracted, behavior-preserving) so the combined parse feeds the SAME write code; (d) reuse the two EXISTING flags (`chat_memory_auto_extract`/`chat_session_summary`) to decide which sections to form — only the NEW `chat_memory_combined_formation` flag is added.

---

## 0. Background

### The gap (`AD-Memory-Formation-Combine-Extract-Summarize`)

The chat post-send hook `_maybe_auto_extract` (`router.py:679`) loads the session ledger ONCE, then makes **two independent** cheap-tier LLM calls over the SAME conversation:

- `extractor.extract_session_to_user(...)` → JSON array `[{content, confidence}]` → `UserLayer.write` (per item; 57.150 dedup upsert).
- `summarizer.summarize_and_store(...)` → JSON object `{summary, key_decisions, unresolved_issues}` → `DBSessionSummaryStore.upsert_summary`.

Two calls over one conversation = ~2× background token + ~2× latency per send, for two reads of the same input.

### Why it matters (the missing capability)

Background memory formation runs after EVERY real_llm send (default both flags ON). Halving its LLM cost is a direct token + latency saving on the highest-frequency background path, with no user-visible behavior change when the combined prompt is well-formed.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `a6e8d586`) | Anchor |
|-------|-------------------------------------|--------|
| Two calls, one ledger | `_maybe_auto_extract` loads ledger once, calls extractor THEN summarizer | `router.py:703-724` |
| Extractor: prompt+call+parse+write | `extract_session_to_user` = render → `chat()` → `_parse_extraction` → write loop | `extraction.py:79-129` |
| Summarizer: prompt+call+parse+store | `summarize_and_store` = render → `chat()` → `_parse_summary` → `upsert_summary` | `session_summarizer.py:89-123` |
| ctx carries both workers | `ChatMemoryExtractContext{extractor, retrieval, message_store, summarizer}` | `handler.py:798-813` |
| both share `profile.cheap` | `build_chat_memory_extractor` builds both on the same cheap client | `handler.py:862-877` |

→ The fix introduces a worker that builds ONE combined prompt (facts + summary sections), makes ONE `chat()` call, parses one object, and dispatches to the SAME write code (`write_facts` + `store_summary`) — composing the two existing workers, not replacing them.

### The design (backend-only: 1 new worker + 2 behavior-preserving method extractions + 1 flag + wiring swap)

```
NEW   agent_harness/memory/formation.py        — MemoryFormationWorker: combined prompt + 1 chat() + parse + dispatch; OR _form_separate (flag off)
EDIT  agent_harness/memory/extraction.py       — extract write_facts() dispatch half from extract_session_to_user (behavior-preserving)
EDIT  agent_harness/memory/session_summarizer.py — extract store_summary() dispatch half from summarize_and_store (behavior-preserving)
EDIT  agent_harness/memory/__init__.py         — export MemoryFormationWorker
EDIT  api/v1/chat/handler.py                   — ctx {extractor,summarizer} -> {former}; build_chat_memory_extractor builds the worker
EDIT  api/v1/chat/router.py                    — _maybe_auto_extract calls former.form() once (wants_user_facts gates profile())
EDIT  core/config/__init__.py                  — chat_memory_combined_formation: bool = True
EDIT  scripts/lint/check_promptbuilder_usage.py — allowlist agent_harness/memory/formation.py (AP-8 background utility-LLM)
```

WHY compose (not replace): `MemoryExtractor` has standalone tests + a 51.2 manual-trigger role (NOT orphaned); `SessionSummarizer`'s only non-test caller is the chat path — replacing it would orphan it (AP-2/AP-4). The worker reuses both via their extracted dispatch methods, AND the `combined=False` fallback path calls their full single-call methods → both stay live on the chat path.

### Ground truth (recon head-start — code read on `main` HEAD `a6e8d586`; ALL re-verified §checklist 0.1)

- `extraction.py:111-129` — the fact-write loop (content/confidence/clamp/`source="auto_extract"`) → extract verbatim into `write_facts`.
- `session_summarizer.py:114-123` — the `summary.strip()` guard + `upsert_summary` → extract verbatim into `store_summary`.
- `extraction.py:131-148` — `_build_known_block(known_facts)` staticmethod (the dedup block) → reusable by the combined prompt.
- `router.py:706-718` — `profile()` known_facts read is gated on `extractor is not None and user_id is not None` → becomes `former.wants_user_facts and user_id is not None`.
- `handler.py:862-877` — both workers built on `profile.cheap`; the worker takes the same cheap client.
- `check_promptbuilder_usage.py:54-62` — `extraction.py` + `session_summarizer.py` already allowlisted; `formation.py` joins them.

**Baselines (57.151 closeout)**: pytest 3042 · wire 26 · Vitest 922 · mockup 51 · mypy 0/396 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-ctx-field-rename** — `ChatMemoryExtractContext.{extractor,summarizer}` → `{former}` breaks `test_memory_auto_extract.py` (`_ctx(extractor,...)`) + `test_handler.py:157` (`ctx.extractor._chat_client`). Grep both, update to the worker shape (expected test maintenance for a behavior change, NOT deletion).
- **D-allowlist-formation** — `formation.py` `.chat()` will trip AP-8 (check_promptbuilder_usage) → add to ALLOWLIST_PATTERNS Day-1 same as the 57.151 `session_summarizer.py` precedent.
- **D-write-facts-session-id** — confirm `extract_session_to_user`'s `session_id` param is unused in the write loop (it is) so `write_facts` need not take it.

## 1. Sprint Goal

Replace the two per-send cheap-tier formation LLM calls with ONE combined call (default), proven by: (1) a unit test asserting the worker calls `chat_client.chat` exactly once while writing BOTH a user fact AND a session summary; (2) a MANDATORY drive-through on real chat-v2 + real Azure showing a single send forms BOTH a `memory_user` (auto_extract) row AND a `memory_session_summary` row from the one combined call, with byte-identical recall behavior to 57.151. Produces CHANGE-119 + a short design note 55 (amends the 53+54 formation architecture).

## 2. User Stories

- **US-1** (worker): 作為平台，我希望一個 `MemoryFormationWorker` 用單次 cheap-tier 呼叫同時抽 user facts + 摘要對話，以便省一半 background token/latency。
- **US-2** (reuse): 作為維護者，我希望 worker 重用既有 `MemoryExtractor`/`SessionSummarizer` 的 dispatch 邏輯（不重寫、不刪除），以便不孤兒化既有類別、不破既有測試。
- **US-3** (fallback): 作為營運者，我希望 `chat_memory_combined_formation` flag（default ON）能一鍵切回已驗證的 two-call path，以便 combined-prompt 品質若退化可即時回退（不需 redeploy）。
- **US-4** (wiring): 作為 chat 主流量，我希望 `_maybe_auto_extract` 改為單次 `former.form()`，以便兩段 formation 在一次呼叫內完成。
- **US-5** (drive-through, MANDATORY): 作為使用者，我希望真 chat-v2 一次送出後，背景單次呼叫同時形成 user fact + session summary，且跨 session recall 行為與 57.151 一致。
- **US-6** (closeout): 文件 + 測試 + 校準 + design note 55 + CHANGE-119 + navigators。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO new wire event / NO frontend / NO new table)

```
NEW   agent_harness/memory/formation.py
EDIT  agent_harness/memory/extraction.py          (+ write_facts; refactor extract_session_to_user to call it)
EDIT  agent_harness/memory/session_summarizer.py  (+ store_summary; refactor summarize_and_store to call it)
EDIT  agent_harness/memory/__init__.py            (export MemoryFormationWorker)
EDIT  api/v1/chat/handler.py                       (ctx fields; build the worker)
EDIT  api/v1/chat/router.py                        (_maybe_auto_extract → former.form())
EDIT  core/config/__init__.py                      (chat_memory_combined_formation flag)
EDIT  scripts/lint/check_promptbuilder_usage.py    (allowlist formation.py)
NEW   tests/unit/agent_harness/memory/test_formation.py
EDIT  tests/unit/api/v1/chat/test_memory_auto_extract.py  (ctx → former shape)
EDIT  tests/unit/api/v1/chat/test_handler.py              (ctx assertion → worker)
UNTOUCHED  loop.py / migrations / wire schema / DBSessionSummaryStore / UserLayer / retrieval.py / builder.py
```

### 3.1 MemoryFormationWorker (US-1/US-3) — `agent_harness/memory/formation.py`

- `__init__(self, chat_client: ChatClient, *, extractor: MemoryExtractor | None = None, summarizer: SessionSummarizer | None = None, combined: bool = True)`.
- `wants_user_facts` property → `self._extractor is not None` (router uses it to gate the `profile()` known_facts read).
- `async def form(*, messages, session_id, tenant_id, user_id=None, known_facts=None, trace_context=None) -> None`:
  - empty ledger / no collaborators → return.
  - `combined=True` → `_form_combined`; else `_form_separate`.
- `_form_combined`: build ONE prompt with the facts section (only when `extractor and user_id`) + the summary section (only when `summarizer`) + the `_build_known_block` dedup (reuse `MemoryExtractor._build_known_block`); ONE `chat()` (temp 0.0); parse the combined JSON object `{facts:[{content,confidence}], summary, key_decisions, unresolved_issues}`; dispatch `extractor.write_facts(facts, ...)` + `summarizer.store_summary({summary,key_decisions,unresolved_issues}, session_id=...)`.
- `_form_separate`: delegate to `extractor.extract_session_to_user(..., known_facts=...)` + `summarizer.summarize_and_store(...)` (the proven 2-call path; keeps both methods live on the chat path).
- Provider-neutral: `self._chat_client` is the ChatClient ABC (no openai/anthropic import). Own tolerant combined-JSON parse + own `_render_messages`/`_content_text`/`_coerce_str_list` (small, self-contained; the pre-existing identical helpers in extraction/summarizer are NOT refactored per Karpathy §3 surgical — noted in design note as known minor dup).

### 3.2 write_facts dispatch half (US-2) — `agent_harness/memory/extraction.py`

- NEW `async def write_facts(self, items: list[dict], *, tenant_id, user_id, trace_context=None) -> list[UUID]`: the content/confidence/clamp/`source="auto_extract"` write loop verbatim from `extract_session_to_user`.
- Refactor `extract_session_to_user` → `... parse → return await self.write_facts(extracted, tenant_id=..., user_id=..., trace_context=...)`. Behavior-preserving (existing 51.2 tests call the public method, unchanged contract incl. the unused `session_id` param).

### 3.3 store_summary dispatch half (US-2) — `agent_harness/memory/session_summarizer.py`

- NEW `async def store_summary(self, parsed: dict, *, session_id: UUID) -> None`: the `summary.strip()` guard + `upsert_summary` verbatim from `summarize_and_store`.
- Refactor `summarize_and_store` → `... parse → if parsed is None: return; await self.store_summary(parsed, session_id=...)`. Behavior-preserving (existing 57.151 tests call the public method).

### 3.4 Wiring (US-4) — `handler.py` + `router.py`

- `ChatMemoryExtractContext`: fields `{extractor, summarizer}` → `{former: MemoryFormationWorker}` (keep `retrieval`, `message_store`).
- `build_chat_memory_extractor`: same env/db/session/tenant/flag guards; build `extractor`/`summarizer` exactly as today (gated by their flags), then `former = MemoryFormationWorker(profile.cheap, extractor=extractor, summarizer=summarizer, combined=settings.chat_memory_combined_formation)`; return ctx with `former`. Still None when both feature flags off.
- `_maybe_auto_extract`: load ledger once; `known_facts = profile()` read only when `ctx.former.wants_user_facts and trace_context.user_id is not None`; ONE `await ctx.former.form(messages=ledger, session_id=, tenant_id=, user_id=trace_context.user_id, known_facts=, trace_context=)`. Best-effort swallow unchanged.

### 3.5 Config flag (US-3) — `core/config/__init__.py`

- `chat_memory_combined_formation: bool = True` (env `CHAT_MEMORY_COMBINED_FORMATION`). Comment: True = ONE combined cheap-tier call doing both sections; False = the proven 57.149+57.151 two-call path. Independent of the two feature flags (which decide WHICH sections form).

### 3.x What is explicitly NOT done

- NOT deleting `MemoryExtractor`/`SessionSummarizer` or their single-call methods (kept live via dispatch reuse + the `combined=False` path).
- NOT refactoring the pre-existing duplicated `_render_messages`/`_content_text` across the 3 files (surgical; noted as known minor dup).
- NO migration / NO new wire event / NO frontend / NO loop.py change / NO A/B benchmark harness (the flag fallback + drive-through cover the quality risk; a formal A/B is a deferred AD).

### 3.y Validation (US-1..US-6)

Gates: mypy `src` (0 errors, +1 new src) · run_all 11/11 (incl. llm_sdk_leak + AP-8 with formation.py allowlisted) · pytest (+ new test_formation.py, updated 2 test files) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.4 / US-5 MANDATORY drive-through. (NO Vitest/mockup delta — backend-only.)

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/memory/formation.py` | NEW |
| 2 | `backend/src/agent_harness/memory/extraction.py` | EDIT (+ write_facts; refactor) |
| 3 | `backend/src/agent_harness/memory/session_summarizer.py` | EDIT (+ store_summary; refactor) |
| 4 | `backend/src/agent_harness/memory/__init__.py` | EDIT (export) |
| 5 | `backend/src/api/v1/chat/handler.py` | EDIT (ctx fields + build worker) |
| 6 | `backend/src/api/v1/chat/router.py` | EDIT (_maybe_auto_extract → former.form()) |
| 7 | `backend/src/core/config/__init__.py` | EDIT (flag) |
| 8 | `scripts/lint/check_promptbuilder_usage.py` | EDIT (allowlist) |
| 9 | `backend/tests/unit/agent_harness/memory/test_formation.py` | NEW |
| 10 | `backend/tests/unit/api/v1/chat/test_memory_auto_extract.py` | EDIT (ctx → former) |
| 11 | `backend/tests/unit/api/v1/chat/test_handler.py` | EDIT (ctx assertion) |
| — | `loop.py` / migrations / wire schema / `DBSessionSummaryStore` / `UserLayer` / `retrieval.py` / `builder.py` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `MemoryFormationWorker.form` (combined) makes EXACTLY ONE `chat()` call and writes BOTH a user fact (via `write_facts`) AND a session summary (via `store_summary`) — unit test with a spy ChatClient asserting call-count == 1 + both dispatch collaborators invoked.
2. `combined=False` → `form` delegates to the two single-call methods (2 calls) — unit test.
3. Only-extract / only-summary flag combos → worker forms only that section in ONE call — unit tests.
4. `extract_session_to_user` / `summarize_and_store` behavior unchanged — existing `test_extraction.py` / `test_session_summarizer.py` / `test_extraction_worker.py` / `test_tenant_isolation.py` stay green untouched.
5. All gates green (mypy / run_all 11/11 incl. AP-8 / pytest / flake8 / llm_sdk_leak).
6. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — one real chat-v2 send forms BOTH a `memory_user` (auto_extract) row AND a `memory_session_summary` row from the single combined call; a NEW session recalls both the user fact AND the prior conversation arc (57.151 behavior preserved). Screenshot + observed-vs-intended + DB inspector evidence in progress.md. (NOT gate-only.)
7. `AD-Memory-Formation-Combine-Extract-Summarize` CLOSED; CHANGE-119; design note 55; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `MemoryFormationWorker` (combined 1-call path)
- [ ] US-2 `write_facts` + `store_summary` dispatch extraction (behavior-preserving)
- [ ] US-3 `chat_memory_combined_formation` flag + `_form_separate` fallback
- [ ] US-4 ctx + `build_chat_memory_extractor` + `_maybe_auto_extract` rewiring
- [ ] US-5 drive-through (real chat-v2 + Azure)
- [ ] US-6 closeout (CHANGE-119 + design note 55 + navigators + calibration)

## 7. Workload Calibration

- Scope class **NEW `memory-formation-combine-spike` 0.60** (a memory-formation arc backend consolidation: 1 new worker + 2 behavior-preserving extractions + combined prompt/parse + flag + wiring swap + ~7 tests; reuses ALL of 57.149/151's stores/layers/prompts. Anchored to the arc's `memory-formation-identity-spike` 0.60 / `memory-session-recall-spike` 0.60 — same greenfield-Cat-3 + main-flow-wiring shape, but LIGHTER (no migration / no table / no new recall) — offset by the combined-prompt design + the BOTH-sections drive-through. The 57.137 lesson holds: a real-code core ≥~3 hr (worker + extractions + parse + tests) holds the 0.60, NOT a tiny-code 0.85. If a 2nd `memory-formation-combine-spike` diverges > 30% from 0.60, re-point).
- **Agent-delegated: no** (parent-direct, consistent with the entire 57.148→151 arc). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6 hr (worker ~1.5 · 2 extractions ~1 · wiring ~1 · tests ~1.5 · drive-through ~1) → class-calibrated commit ~3.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Combined prompt degrades fact/summary quality vs two focused calls | The `chat_memory_combined_formation=false` flag reverts to the proven two-call path instantly (no redeploy); the drive-through confirms both outputs are still correct before merge; gpt-5.2 handles a combined structured ask easily. |
| ctx field rename breaks 2 test files | D-ctx-field-rename: grep + update both to the worker shape (expected test maintenance, NOT deletion) — verified Day-0. |
| AP-8 lint flags formation.py `.chat()` | D-allowlist-formation: add to ALLOWLIST_PATTERNS Day-1 (same category + precedent as `session_summarizer.py`, 57.151). |
| Stale `--reload` backend masks the wiring swap at drive-through | Risk Class E: clean single-proc restart + verify the live serving PID (Win32_Process PID/PPID/StartTime sweep) before driving. |
| Orphaning `SessionSummarizer` | Compose-not-replace: worker reuses `store_summary`; the `combined=False` path calls `summarize_and_store` → both stay live on the chat path. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- A formal real-Azure A/B harness measuring combined-vs-separate formation quality — `AD-Memory-Combined-Formation-AB-Quality` (the flag + drive-through suffice for this sprint; a benchmark mirrors the 57.136/137/138 pattern if quality ever regresses).
- Incremental (non-full-ledger) summarization — `AD-Memory-Session-Summary-Incremental` (57.151 carryover, unchanged).
- `extracted_to_user_memory` coordination flag — `AD-Memory-Session-Summary-Extract-Coordination` (57.151 carryover, unchanged).
