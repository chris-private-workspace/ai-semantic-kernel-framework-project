# Sprint 57.164 Plan — Tool-error taxonomy surfaced in chat-v2 UI

**Summary**: Closes the Tool-range carryover **③3 `AD-Tool-Error-Taxonomy-UI`** (57.144) — surface the `error_taxonomy` a failed tool already carries (`ToolResult.error_taxonomy`, Sprint 57.144) all the way to the chat-v2 transcript so a human can SEE the typed diagnosis (parameter / wrong-tool / failed-api / invocation) on any tool failure. **Key scope decision (user AskUserQuestion 2026-07-10, Option B)**: DECOUPLE the pure classification from the `CHAT_TOOL_ERROR_REFLECTION` lever — `classify_tool_error` runs on EVERY tool failure (so the taxonomy is visible by default), while the lever keeps gating only the LLM-visible `content` reflection. Agent behavior stays byte-identical (no LLM reads the display taxonomy). Cross-stack additive field on the EXISTING `tool_call_result` wire type (count stays 26): backend decouple → events.py field → loop 2 emit sites → sse 2 branches → wire schema → codegen regen → FE store + ToolBlock chip. **Drive-through MANDATORY** (user-facing surface). NO design note (feature sprint, not a spike). NO migration.

**Status**: Approved-to-execute (user selected ③3 first via AskUserQuestion 2026-07-10; Option B "decouple — always classify" via a 2nd AskUserQuestion same day)
**Branch**: `feature/sprint-57-164-tool-taxonomy-ui`
**Base**: `main` HEAD `2614303c` (chore(docs): flip Sprint 57.163 PR-pending → MERGED)
**Slice**: standalone — closes ③3 `AD-Tool-Error-Taxonomy-UI` (2 of ~4 Tool-range ADs now done; ③2 autofix rolls to 57.165)
**Scope decisions**: (a) Option B decouple — always classify, lever gates only the LLM `content`; (b) additive field on the existing `tool_call_result` wire type (count 26 unchanged), NOT a new event type; (c) surface on the transcript **ToolBlock** head via the existing `.badge` mockup primitive (there is no per-tool Inspector pane; the ToolBlock is the tool's render home + most visible), render only when `errorTaxonomy` present; (d) decouple BOTH the dominant `_build_failure` and the rare `loop.py:3068` path for consistency.

---

## 0. Background

### The gap (③3 `AD-Tool-Error-Taxonomy-UI`)

Sprint 57.144 added a 5-value error taxonomy (`ErrorTaxonomy`: parameter / wrong_tool / failed_api / invocation / unknown) + set `ToolResult.error_taxonomy` on tool failures. 57.163 verified the wiring + found reflection is tier-dependent. But the taxonomy has **no UI surface**: it stops at the backend `ToolResult`, never reaches the SSE wire, and 0 frontend files reference it. A human debugging a failed tool in chat-v2 sees only the raw error string + a red "error" badge — not the typed diagnosis.

### Why it matters (the missing capability)

The taxonomy is a deterministic, free, actionable diagnostic ("this failed because of a PARAMETER error" vs "an external API failed"). Surfacing it lets an operator instantly categorise a tool failure in the transcript instead of parsing a raw traceback — the reality-audit "落地" (make the wired capability actually usable), not just "引擎接好".

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `2614303c`) | Anchor |
|-------|--------------------------------------|--------|
| taxonomy only set under lever | `error_taxonomy` computed ONLY inside `if tool_error_reflection_enabled()` | `tools/executor.py:406-414` |
| rare path same gating | rare executor-self-raise path also lever-gates the taxonomy | `orchestrator_loop/loop.py:3068-3086` |
| taxonomy lives on `ToolResult`, not the loop event | `ToolResult.error_taxonomy: str \| None` | `_contracts/tools.py:155` |
| loop event has no taxonomy | `ToolCallFailed{tool_call_id, tool_name, error}` — no taxonomy field | `_contracts/events.py:207-210` |
| loop drops it at emit | 2 `ToolCallFailed(...)` emits don't pass `result.error_taxonomy` | `loop.py:3173` (_run_turns) + `loop.py:3560` (resume) |
| SSE has no taxonomy | `tool_call_result` data = `{tool_call_id, tool_name, duration_ms, result, is_error}` | `api/v1/chat/sse.py:210-232` |
| wire schema has no taxonomy | `tool_call_result` entry has 5 fields | `event_wire_schema.py:117-123` |
| FE has no taxonomy | 0 `.ts/.tsx` reference `error_taxonomy`/`errorTaxonomy`; `ToolBlock` type has no field | `types.ts:108-117` |

→ The fix (a) decouples classification from the lever at the 2 failure-construction sites so the taxonomy is always present, then (b) threads it through the existing `ToolCallFailed`→`tool_call_result` wire path (additive field, count unchanged) to a conditional ToolBlock chip.

### The design (cross-stack additive field + backend decouple; NO new event type, NO migration)

```
# BACKEND — decouple (always classify; lever gates only LLM content)
executor.py _build_failure:  classify_tool_error() ALWAYS → taxonomy_value;
                             render_reflection() → content ONLY if lever ON (else content="")
loop.py:3068 rare path:      _err_taxonomy ALWAYS classified; _err_content gated (mirror)

# BACKEND — thread taxonomy to the wire (additive field on tool_call_result; count stays 26)
events.py ToolCallFailed  += error_taxonomy: str | None = None
loop.py:3173 + :3560       ToolCallFailed(..., error_taxonomy=result.error_taxonomy)
sse.py ToolCallExecuted    data += "error_taxonomy": None          # success branch (parity: same field set)
sse.py ToolCallFailed      data += "error_taxonomy": event.error_taxonomy
event_wire_schema.py       tool_call_result += "error_taxonomy": "string | null"
scripts/codegen/...        REGEN loopEvents.generated.ts + events.json

# FRONTEND — capture + conditional render
types.ts ToolBlock         += errorTaxonomy?: string | null
chatStore.ts tool_call_result case  set errorTaxonomy: ev.data.error_taxonomy
ToolBlock.tsx head row     {block.errorTaxonomy && <span className="badge dot danger">{...}</span>}
```

Why Option B over pure-surface: a lever-gated (default-OFF) taxonomy surface would be empty in normal operation (near-Potemkin). Classification is a pure, free function; the `CHAT_TOOL_ERROR_REFLECTION` lever's evidence-first purpose is the LLM-visible `content` reflection (the thing 57.144/57.163 A/B-measured), NOT the display metadata. Decoupling makes the taxonomy visible by default with byte-identical agent behavior (no LLM reads it).

### Ground truth (recon head-start — code read on `main` HEAD `2614303c`; ALL re-verified §checklist 0.1)

- `tools/executor.py:404-422` — `_build_failure` is the single failure-result builder for BOTH the handler-exception path and `_fail` (schema / unknown-tool); it already has `error_class`/`is_schema_error`/`is_unknown_tool` signals for `classify_tool_error`.
- `loop.py:3080-3088` — the rare path builds its own `ToolResult` then falls through to the common `loop.py:3152` success/fail branch → the same `3173` `ToolCallFailed` emit. So adding `error_taxonomy=` at `3173` + `3560` covers BOTH dominant and rare results.
- `event_wire_schema.py:82` — `WIRE_SCHEMA` is the codegen + parity single-source; `tool_call_result` is emitted by 2 events (`ToolCallExecuted` success / `ToolCallFailed` fail) so BOTH sse branches must carry the same field set or `test_event_wire_schema_parity.py` fails.
- `types.ts:51-53` — the FE event interfaces are GENERATED from `event_wire_schema.py`; the `tool_call_result` TS type gains `error_taxonomy` via codegen (no hand-edit of the generated file).
- `ToolBlock.tsx:66-94` — verbatim mockup re-point (57.30); `.badge dot danger` (`STATUS_BADGE_TONE.error`) is an existing mockup primitive already used for the status badge.

**Baselines (57.163 closeout)**: pytest 3230 · wire 26 · Vitest 930 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-parity-two-events-one-type** — confirm how `test_event_wire_schema_parity.py` handles `tool_call_result` (2 producing events) → both sse branches must emit `error_taxonomy` (success=None, fail=value) → §Risks.
- **D-wire-count-tests** — grep for hardcoded `26` wire-count asserts + `eventSchema.generated.test.ts`; a FIELD add keeps count 26 (unlike 57.130's type add) so count asserts should stay green — verify no field-set snapshot breaks silently.
- **D-drivethrough-trigger** — identify a chat-executor tool that fails via `_build_failure`/rare-path (LLM_RECOVERABLE → `tool_call_result`), NOT a Cat-8 FATAL terminate (→ `loop_terminated`, 57.130). Candidate triggers to test Day-3 → §Risks.
- **D-off-test-flips** — grep the 57.144 (`test_executor.py`) + 57.163 (`test_loop_error_handling.py`) OFF-asserts (`error_taxonomy is None`) that Option B flips to expect a classified value (content still `""`).

## 1. Sprint Goal

Make any tool failure's typed taxonomy visible in the chat-v2 transcript, by default, with byte-identical agent behavior. PROVEN by: full gate (mypy · run_all · pytest · Vitest · mockup byte-identical · build · lint · LLM-SDK-leak) + a **MANDATORY drive-through** (real chat-v2 UI + real backend + real LLM: trigger a real tool failure → the ToolBlock shows the typed taxonomy chip, lever OFF). Produces **CHANGE-131**; NO design note (feature sprint).

## 2. User Stories

- **US-1** (Cat 2 decouple): 作為 平台維運者，我希望 tool 失敗的 taxonomy 永遠被分類（不受 reflection lever 管），以便 Inspector/transcript 預設就能看到 typed 診斷。
- **US-2** (Cat 2→12 wire): 作為 前端，我希望 `error_taxonomy` 隨 `tool_call_result` 事件上 SSE wire（既有事件加欄位、count 不變），以便 chat-v2 能消費。
- **US-3** (frontend): 作為 使用者，我希望 chat-v2 的失敗 ToolBlock 顯示 typed taxonomy chip，以便一眼分類失敗原因。
- **US-4** (drive-through, MANDATORY): 作為 品質守門，我希望 真 UI + 真後端 + 真 LLM 觸發一次真實 tool 失敗，看到 taxonomy chip 真的渲染，以便證明「人能真的用」（非 gate-only）。
- **US-5** (closeout): 作為 專案維護者，我希望 CHANGE-131 + retro + 導航檔更新 + ③3 AD closed，以便 Tool 範疇進度可溯。

## 3. Technical Specifications

### 3.0 Architecture (cross-stack; NO migration / NO new event type / NO new CSS)

```
EDIT   backend/src/agent_harness/tools/executor.py            _build_failure: always classify (decouple)
EDIT   backend/src/agent_harness/orchestrator_loop/loop.py    rare path decouple + 2 ToolCallFailed emit +error_taxonomy
EDIT   backend/src/agent_harness/_contracts/events.py         ToolCallFailed += error_taxonomy field
EDIT   backend/src/api/v1/chat/sse.py                         2 branches (Executed=None / Failed=value)
EDIT   backend/src/api/v1/chat/event_wire_schema.py           tool_call_result += error_taxonomy (count 26)
REGEN  frontend/src/features/chat_v2/generated/loopEvents.generated.ts + events.json   codegen
EDIT   frontend/src/features/chat_v2/types.ts                 ToolBlock += errorTaxonomy?
EDIT   frontend/src/features/chat_v2/store/chatStore.ts       tool_call_result → set errorTaxonomy
EDIT   frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx   conditional taxonomy chip
EDIT   tests: executor / loop-error-handling / sse / wire-parity (backend) + chatStore.mergeEvent / generated / blocks (FE)
UNTOUCHED  _error_taxonomy.py (classify/render pure fns reused as-is) · migrations · other wire types
```

### 3.1 Backend decouple (US-1) — `executor.py` + `loop.py`

- `executor.py:_build_failure`: move `classify_tool_error(...)` + `taxonomy_value = taxonomy.value` OUT of the `if tool_error_reflection_enabled()` block (always run); keep `content = render_reflection(...)` INSIDE the gate (else `content=""`). Result: `error_taxonomy` always set on failure; `content` behavior byte-identical (empty when OFF).
- `loop.py:3068-3086` rare path: mirror — always compute `_tax`/`_err_taxonomy`; gate only `_err_content` (`render_reflection` vs `"Error: {exc!r}. Please adjust your approach."`).
- Update docstrings (executor `_build_failure` + `_error_taxonomy.py` "gated by the lever" wording → "classification always; the lever gates the LLM content").

### 3.2 Wire the taxonomy (US-2) — `events.py` + `loop.py` + `sse.py` + `event_wire_schema.py`

- `events.py`: `ToolCallFailed` += `error_taxonomy: str | None = None` (frozen dataclass, default None → backward compatible).
- `loop.py:3173` + `:3560`: `ToolCallFailed(..., error_taxonomy=result.error_taxonomy)`.
- `sse.py`: `ToolCallExecuted` branch data += `"error_taxonomy": None`; `ToolCallFailed` branch data += `"error_taxonomy": event.error_taxonomy` (BOTH — same field set for the shared `tool_call_result` type; parity guard).
- `event_wire_schema.py`: `tool_call_result` entry += `"error_taxonomy": "string | null"` (recognised TS type; wire-TYPE count stays 26). MHist +1 line.
- Codegen: `python scripts/codegen/generate_event_schemas.py` → regen `loopEvents.generated.ts` + `events.json`.

### 3.3 Frontend surface (US-3) — `types.ts` + `chatStore.ts` + `ToolBlock.tsx`

- `types.ts`: `ToolBlock` += `errorTaxonomy?: string | null`.
- `chatStore.ts` `tool_call_result` case: set `errorTaxonomy: ev.data.error_taxonomy` on the matched ToolBlock (the codegen'd event type now has the field). Optionally set `errorTaxonomy: null` at the 2 ToolBlock creation sites (`llm_response`/`tool_call_request`) — optional field, not required for tsc.
- `ToolBlock.tsx`: in the head row, after the status badge, `{block.errorTaxonomy && <span className="badge dot danger" title="tool error taxonomy">{block.errorTaxonomy}</span>}`. Reuses the existing `.badge dot danger` mockup primitive (no new CSS). Render only when present → success/pending tools unchanged, mockup byte-identical (`styles-mockup.css` untouched).

### 3.x What is explicitly NOT done

- NOT flipping the `CHAT_TOOL_ERROR_REFLECTION` default (still OFF — that gates the LLM `content`, an evidence-first decision 57.144/57.163 owns).
- NOT adding a new Inspector tab/pane for tool errors (③3 = surface the taxonomy; the transcript ToolBlock is the tool's render home — a new pane is scope creep).
- NOT the ③2 autofix (rolls to 57.165) and NOT a `human-readable label` map on the FE (the raw taxonomy value — "parameter" etc. — is the chip text; a prettier label is a follow-on if desired).
- NOT touching `_error_taxonomy.py` logic (`classify_tool_error`/`render_reflection` reused verbatim).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 400 · run_all 11/11 · pytest ≥3230+new · Vitest 930+new · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3 US-4 drive-through (MANDATORY — real UI).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/tools/executor.py` | EDIT (decouple `_build_failure`) |
| 2 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT (rare-path decouple + 2 emit sites +error_taxonomy) |
| 3 | `backend/src/agent_harness/_contracts/events.py` | EDIT (`ToolCallFailed` += field) |
| 4 | `backend/src/api/v1/chat/sse.py` | EDIT (2 branches) |
| 5 | `backend/src/api/v1/chat/event_wire_schema.py` | EDIT (`tool_call_result` += field) |
| 6 | `backend/src/agent_harness/tools/_error_taxonomy.py` | EDIT (docstring wording only) |
| 7 | `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | REGEN (codegen) |
| 8 | `frontend/src/features/chat_v2/generated/events.json` | REGEN (codegen) |
| 9 | `frontend/src/features/chat_v2/types.ts` | EDIT (`ToolBlock` += `errorTaxonomy?`) |
| 10 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT (`tool_call_result` set) |
| 11 | `frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx` | EDIT (conditional chip) |
| 12 | `backend/tests/unit/agent_harness/tools/test_executor.py` | EDIT (OFF-assert flips) |
| 13 | `backend/tests/integration/agent_harness/orchestrator_loop/test_loop_error_handling.py` | EDIT (57.163 OFF-assert flip) |
| 14 | `backend/tests/unit/api/v1/chat/test_sse.py` | EDIT (tool_call_result +error_taxonomy) |
| 15 | `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` | EDIT if needed (parity) |
| 16 | `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` | EDIT (errorTaxonomy capture) |
| 17 | `frontend/tests/unit/chat_v2/eventSchema.generated.test.ts` | EDIT/REGEN (generated snapshot) |
| 18 | `frontend/tests/unit/chat_v2/components/blocks.test.tsx` | EDIT (chip render) |
| — | `backend/src/agent_harness/tools/_error_taxonomy.py` logic | **UNTOUCHED** (pure fns reused) |
| — | `frontend/src/styles-mockup.css` | **UNTOUCHED** (reuse `.badge`, byte-identical) |
| — | any Alembic migration | **UNTOUCHED** (no DB) |

## 5. Acceptance Criteria

1. `error_taxonomy` is set on EVERY tool failure regardless of `CHAT_TOOL_ERROR_REFLECTION` (executor + rare path); `content` stays byte-identical (empty when OFF).
2. `error_taxonomy` reaches the `tool_call_result` SSE frame (fail=classified value, success=null); wire-TYPE count stays 26; parity test green.
3. chat-v2 renders a taxonomy chip on a failed ToolBlock only when present; `styles-mockup.css` byte-identical; successful/pending tools unchanged.
4. Agent behavior unchanged (no LLM reads the display field); all backend + FE tests green (57.144/57.163 OFF-asserts updated to the new intended behavior, NOT weakened).
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — a real tool failure in chat-v2 renders the correct typed taxonomy chip (lever OFF); screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. ③3 `AD-Tool-Error-Taxonomy-UI` CLOSED; CHANGE-131; calibration recorded; navigators + next-phase-candidates updated (③2 remains open).

## 6. Deliverables

- [ ] US-1 backend decouple (executor `_build_failure` + loop rare path) — taxonomy always classified
- [ ] US-2 wire the taxonomy (events + loop 2 emits + sse 2 branches + wire schema + codegen regen)
- [ ] US-3 FE surface (types + chatStore + ToolBlock chip)
- [ ] US-4 drive-through PASS (real UI, real failure, chip renders)
- [ ] US-5 CHANGE-131 + closeout + ③3 AD closed

## 7. Workload Calibration

- Scope class **`frontend-feature-with-event-wire-addition` 0.55** (3-pt validated ~1.07: 57.100/108/116 — additive field on an EXISTING event, count unchanged + codegen regen + chat-v2 FE store-capture + render + cross-stack parity). This sprint matches that shape PLUS a small backend decouple (2 sites) + 57.144/57.163 OFF-test flips + a MANDATORY drive-through with a trigger hunt — the same variance drivers that put 57.130 `chatv2-fatal-terminate-wire-surface` (0.55) at ~1.29. Expect the UPPER edge; if it lands > 1.20, note a `-with-backend-decouple-and-drivethrough` sub-class or re-point toward 0.65.
- **Agent-delegated: no** (parent-direct — the Option B decouple decision, the 57.144/57.163 test-flip judgement, and the drive-through trigger hunt all need the parent in the loop). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~8.25 hr (decouple ~0.75 · wire chain ~1.0 · codegen ~0.5 · FE ~1.0 · tests ~2.0 · drive-through ~2.0 · docs/closeout ~1.0) → class-calibrated commit ~4.5 hr (mult 0.55). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Drive-through deterministic trigger** (AD-DriveThrough-Deterministic-Tool-Trigger, recurring 57.122/130/131) — must fail via `_build_failure`/rare-path (→ `tool_call_result`), NOT a Cat-8 FATAL terminate (→ `loop_terminated`, cf. web_search 57.130) | Day-0 D-drivethrough-trigger: read chat-executor toolset + classify. Day-3 candidates in order: (a) prompt agent to call a tool with a wrong-typed arg → schema PARAMETER via `_fail`; (b) a handler that raises a non-fatal exc → INVOCATION; (c) an env-unavailable tool that fails LLM-recoverably. Pick the first reliable one; record the trigger. |
| **Parity: `tool_call_result` emitted by 2 events** — divergent field sets break `test_event_wire_schema_parity.py` | Add `error_taxonomy` to BOTH sse branches (success=None / fail=value); Day-0 D-parity-two-events-one-type confirms the parity mechanism. |
| **57.144/57.163 OFF-tests assert `error_taxonomy is None`** — Option B flips them | Update the OFF-asserts to expect the classified value (keep the `content==""` assertion) — an HONEST behavior-change update, not a weakening (Deep-Error / Never-Delete-Tests respected: assertion reflects the new intended behavior). |
| **Mockup drift** — a new chip on ToolBlock (verbatim 57.30 re-point) | Reuse the existing `.badge dot danger` mockup primitive, render ONLY when `errorTaxonomy` present, NO new CSS → `styles-mockup.css` byte-identical; `check:mockup-fidelity` green; documented as a design-system-primitive addition (57.120/131/133 precedent). |
| **Stale `--reload` masks the FE/wire change** (Risk Class E) | Day-3 clean restart: rebuild Vite; if backend touched, kill stale/orphan uvicorn workers + confirm sole port owner + startup log before drive-through. |
| **Agent behavior regression** (setting taxonomy when OFF) | The display field is never read by the loop (renders `content`, not `error_taxonomy`) → assert `content` byte-identical when OFF in the executor test; agent path unchanged. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **③2 `AD-Tool-Description-AutoFix`** — the lint `--fix` mode → Sprint 57.165 (user-confirmed order 2026-07-10).
- **Human-readable taxonomy labels on the FE** (e.g. "Parameter error" vs raw "parameter") — follow-on polish AD if desired.
- **Flipping `CHAT_TOOL_ERROR_REFLECTION` default / per-tier reflection policy** — `AD-Tool-Reflection-PerTier-Default` (57.163 carryover), needs a larger multi-run corpus first.
- **A dedicated Inspector tool-error pane / per-tool detail view** — the transcript ToolBlock is sufficient; a pane is a separate UX AD.
