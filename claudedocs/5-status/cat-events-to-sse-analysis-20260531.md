# A-5 Deep Analysis: LoopEvent → SSE → Frontend — the Event Visibility Pipeline

**Purpose**: Single-point deep analysis of the 4-stage event pipeline (defined → yielded → serialized → rendered), consolidating the visibility slivers from A-1 (MemoryAccessed), A-2 (PromptBuilt), A-4 (Span* / Cat 12), Cat 4 (ContextCompacted), Cat 7 (StateCheckpointed). Analysis only.
**Category / Scope**: Cross-cutting (Cat 1 events + SSE + frontend) / Phase 57+ (post Sprint 57.63)
**Created**: 2026-05-31
**Last Modified**: 2026-05-31
**Status**: Active (analysis input for a future sprint)

> **Modification History**
> - 2026-05-31: **Correction pass — RETRACTED a fabricated claim.** The first draft asserted sse.py has a `_SAFE_SKIP_EVENTS` set added in Sprint 57.63 and that `TripwireTriggered` "likely crashes". Both were WRONG (the first draft was written while the session's read tools were truncating output; I confabulated the `_SAFE_SKIP_EVENTS` mechanism). Verified against clean full reads of `sse.py` (1-324) + `router.py` `_stream_loop_events`: there is NO `_SAFE_SKIP_EVENTS`; the skip is the **router's `try/except NotImplementedError`**; **no event crashes** the stream.
> - 2026-05-31: Initial creation — A-5 of the Area-A series; 2-agent parallel audit

> **Related**: `integration-progress-20260531.md` (Area A item 5); `cat3-/cat5-/cat12-…-analysis-20260531.md` (the slivers this consolidates); `17-cross-category-interfaces.md §4.1` (LoopEvent taxonomy) / `16-frontend-design.md §SSE Stream Handling` / `02-architecture-design.md §SSE Event Spec`.

---

## 0. Headline

A-5 is a **4-stage pipeline** (`_contracts/events.py` defines → `loop.py` yields → `sse.py` serializes → frontend renders) where ~26 events are defined but only **14** complete the journey. **There is NO crash anywhere** — every event without a serializer branch hits `sse.py`'s `raise NotImplementedError` (sse.py:298), which the router's stream loop **catches and skips with a debug log** (router.py:351-354). So the findings are all *visibility* gaps, not correctness bugs: **(1) four events are yielded-then-silently-skipped** — `ContextCompacted` / `StateCheckpointed` (yielded on the real_llm path since 57.63), `PromptBuilt` (only once A-2 injects the builder), and `TripwireTriggered` (when a tripwire fires); **(2) six events are never emitted at all** — `MemoryAccessed` / `ErrorRetried` / `LoopTerminated` / `SpanStarted` / `SpanEnded` / `MetricRecorded`; **(3) one event is serialized but not rendered** — `GuardrailTriggered`. Plus the structural root cause: the frontend's 14-type list is **hand-maintained with no codegen / CI parity** — the exact anti-pattern `16.md` warns against.

---

## 1. The actual serialize-and-skip mechanism (verified from clean reads)

`sse.py` `_serialize_inner()` has **16 `isinstance` branches** (lines 119-296). 15 return a payload; `Thinking` returns `None` (intentional skip). Mapping to **14 distinct wire-type strings** (`ToolCallExecuted` + `ToolCallFailed` both → `tool_call_result`):

`loop_start · turn_start · llm_request · llm_response · tool_call_request · tool_call_result · loop_end · approval_requested · approval_received · guardrail_triggered · verification_passed · verification_failed · subagent_spawned · subagent_completed`

Everything else → `raise NotImplementedError("…not in Sprint 50.2 scope…")` (sse.py:298-301).

**The skip is in the router, not sse.py** (router.py:349-354, verified):
```python
try:
    payload = serialize_loop_event(event)
except NotImplementedError:
    logger.debug("sse: skip unserialized event %s", type(event).__name__)
    continue        # ← silently dropped; stream continues
if payload is None:  # Thinking → skip
    continue
yield format_sse_message(payload["type"], payload["data"])
```
So **no unserialized event crashes the SSE stream** — it is debug-logged and skipped. (My earlier integration-snapshot phrasing "silently skipped by router logger.debug" was correct; the A-5 audit agent's "hard crash" and the first draft's `_SAFE_SKIP_EVENTS` were both wrong.)

---

## 2. The 4-stage matrix

Defined ≈ **26** concrete LoopEvent subclasses (`_contracts/events.py`; per audit agent — not re-enumerated this pass). Serialized = **14** wire types. Frontend `KNOWN_LOOP_EVENT_TYPES` = **14** (hand-maintained, matches).

| Event | Defined | Yielded by loop (guard) | sse.py serializes? | Frontend | Net status |
|-------|:---:|---|---|---|---|
| LoopStarted / TurnStarted / LLMRequested / LLMResponded / LoopCompleted | ✅ | ✅ always | ✅ | ✅ render | full pipeline |
| ToolCallRequested / ToolCallExecuted / ToolCallFailed | ✅ | ✅ | ✅ | ✅ render | full |
| ApprovalRequested / ApprovalReceived | ✅ | ✅ (HITL path) | ✅ (sse.py:209/220) | ✅ render | full |
| VerificationPassed / VerificationFailed | ✅ | (via `run_with_verification` wrapper) | ✅ (sse.py:251/261) | ✅ render | full |
| SubagentSpawned / SubagentCompleted | ✅ | (via dispatcher) | ✅ (sse.py:276/288) | ✅ render | full |
| `Thinking` | ✅ | ✅ always | ⏭️ →`None` (sse.py:158) | n/a | intentional drop |
| `GuardrailTriggered` | ✅ | ✅ (7 sites) | ✅ (sse.py:237) | ⚠️ **rawEvents only, not rendered** | reaches FE, no UI |
| **`ContextCompacted`** | ✅ | ✅ `loop.py:861` (compactor injected — 57.63) | ❌ → NotImplementedError → **router skips** | ❌ | silent skip (no crash) |
| **`StateCheckpointed`** | ✅ | ✅ `loop.py:1003` (Cat 7 deps — 57.63) | ❌ → router skips | ❌ | silent skip |
| **`PromptBuilt`** | ✅ | ⏸️ `loop.py:915` only if prompt_builder injected (A-2, not yet) | ❌ → router skips (if ever yielded) | ❌ | not yielded today + no serializer |
| **`TripwireTriggered`** | ✅ | ✅ when a tripwire fires | ❌ → router skips | ❌ | silent skip — user sees `loop_end` but **not the tripwire reason** (UX gap, not a crash) |
| `MemoryAccessed` | ✅ | ❌ never yielded | ❌ | ❌ | break at loop.py (A-1/A-3) |
| `ErrorRetried` / `LoopTerminated` | ✅ | ❌ never yielded | ❌ | ❌ | break at loop.py (Cat 8) |
| `SpanStarted` / `SpanEnded` / `MetricRecorded` | ✅ | ❌ never yielded | ❌ | ❌ | break at loop.py (A-4) |

Two buckets for the gap events:
- **Yielded-but-no-serializer (skipped)**: `ContextCompacted`, `StateCheckpointed`, `TripwireTriggered` (and `PromptBuilt` once A-2 lands). Fix = add serializer branch + frontend consumer.
- **Never-yielded**: `MemoryAccessed`, `ErrorRetried`, `LoopTerminated`, `SpanStarted/SpanEnded/MetricRecorded`. Fix = make the loop yield them (depends on A-1/A-4/Cat 8) AND add serializer + consumer.

---

## 3. Target design recap (from `17.md §4.1`, `16.md §SSE`, `02.md`)

- **Canonical LoopEvent set** (~22-26) — every category emits its observable signal (Cat 3 MemoryAccessed, Cat 4 ContextCompacted, Cat 5 PromptBuilt, Cat 7 StateCheckpointed, Cat 8 ErrorRetried, Cat 9 Guardrail/Tripwire, Cat 10 Verification*, Cat 11 Subagent*, Cat 12 Span*/Metric*, HITL Approval*).
- **Two audiences**: **core conversation flow** (MessageList / ThinkingBlock / ToolCallCard / HITLApprovalCard / VerificationStatus / LoopProgressIndicator / **Tripwire alert**) vs **diagnostic / Inspector / DevUI** (StateCheckpointed→CheckpointTimeline, ContextCompacted→ContextUsageGauge, PromptBuilt→PromptInspector, MemoryAccessed→MemoryLayerViewer, Span*/Metric→TraceViewer + MetricDashboard).
- **The plan explicitly streams the diagnostic + Span events over SSE** (in addition to OTel): `17.md §7.2` "所有 LoopEvent 都附 trace_id / span_id — SSE / OTel collector 端 reconstruction". So Span events are dual-routed (SSE→DevUI TraceViewer + OTel→Jaeger). (This is the A-4 sliver that lives here.)
- **Mandated schema-sync pipeline** (`16.md §TypeScript Type System`): `_contracts/events.py` (Pydantic) → `scripts/export_event_schemas.py` → `backend/schemas/events.json` → `npm run generate-event-types` → `frontend/src/api/generated/events.ts`, enforced by CI `event-schema-sync.yml` (`git diff --exit-code`). **None of these files exist today** — hand-writing the frontend event union is the explicitly-named anti-pattern ("will drift out of sync with backend schema").
- **Frontend hook** (`useLoopEvents`): named-event routing (all 22), reconnect with `last_event_id`, `requestAnimationFrame` backpressure batching.
- **SSE frame** (verified, `format_sse_message` sse.py:304): `event: {type}\ndata: {json}\n\n`. (Note: the current `format_sse_message` does **not** emit an `id:` line — the plan's `id: {streaming_seq}` for `last_event_id` resume is not implemented; resume is a separate gap.)

---

## 4. The gap, grouped (severity-corrected)

1. **`TripwireTriggered` UX gap (no crash)**: a tripwire halt is yielded but skipped, so the user sees `loop_end` with a stop_reason but no explanatory tripwire event. Not a 500. Fix = add a `tripwire_triggered` serializer + a frontend alert (it's core-flow — a blocked run should say why). Low cost, decent UX value.
2. **Diagnostic events skipped (visibility gap)**: `ContextCompacted` / `StateCheckpointed` yielded since 57.63 but skipped; `PromptBuilt` will be once A-2 lands. To surface: design SSE wire format + serializer branch + frontend Inspector consumers (CheckpointTimeline / ContextUsageGauge / PromptInspector). This is where the A-2/A-4 visibility slivers land.
3. **Events never emitted (break at loop.py)**: `MemoryAccessed` (needs A-1/A-3), `SpanStarted/SpanEnded/MetricRecorded` (needs A-4 Tier 1 to open spans + yield the event form), `ErrorRetried` / `LoopTerminated` (Cat 8 — loop never yields them despite being defined).
4. **Frontend not rendering `GuardrailTriggered`**: serialized + received but accumulated in `rawEvents` only, no UI consumer (Phase-2 deferred).
5. **No schema-sync pipeline + no `id:`/resume**: the 14-type frontend list is hand-maintained across 3 files (the `CONVENTION.md §7` 3-edit checklist is the only guard); and `format_sse_message` omits the `id:` line the plan's `last_event_id` resume needs. These are the structural roots that let everything above drift silently.

---

## 5. Key findings / distinctions

1. **No crash anywhere** — the router's `except NotImplementedError: continue` is a catch-all skip. Every gap event degrades to "invisible", never to "500". (This corrects the first draft.)
2. **A-5 is the consolidation layer**: it surfaces the observability slivers of A-1 (MemoryAccessed), A-2 (PromptBuilt), A-4 (Span*/Metric), Cat 4 (ContextCompacted), Cat 7 (StateCheckpointed). The diagnostic half only has *value* once those producers actually emit — so A-5's diagnostic visibility is **downstream** of A-1/A-2/A-4.
3. **The catch-all skip is double-edged**: it prevents crashes but also means a new event silently never reaches the frontend with zero signal — exactly why the codegen + CI parity gate (A-5b) is the high-leverage durable fix. A serializer that *exhaustively* handles every defined event (no reachable `NotImplementedError`) + a CI diff gate would convert silent drift into a loud CI failure.
4. **`GuardrailTriggered` precedent**: it was added to the serializer in Sprint 53.6 *after* a Day-0 探勘 found it was yielded 7× but unserialized (sse.py docstring line 41-45) — the same shape as today's ContextCompacted/StateCheckpointed gap. That's the proven fix pattern: add the isinstance branch + frontend handler.

---

## 6. Risks / open research questions

1. **Diagnostic event wire format**: `ContextCompacted` / `StateCheckpointed` / `PromptBuilt` / `MemoryAccessed` need designed payloads (the `17.md §4.1` fields are the spec) + Inspector UI — non-trivial frontend work, not just a serializer line.
2. **Span events over SSE vs OTel** (the A-4 overlap): the plan dual-routes; high-volume Span/Metric events over SSE have cost — consider sampling or an Inspector-only opt-in channel rather than streaming every span.
3. **Schema codegen toolchain**: Pydantic → JSON Schema → TS (`json-schema-to-typescript` or similar) + the CI `git diff --exit-code` gate — a small but real infra addition.
4. **Resume / `id:` line**: `format_sse_message` omits `id:`; implementing `last_event_id` resume (replay from `streaming_seq`) is a separate, larger piece if reconnection matters.
5. **Backpressure**: once diagnostic + Span events stream, per-turn event volume rises sharply; the hook's `requestAnimationFrame` batching (currently sized for 14 events) must be validated under the larger set.

---

## 7. Recommendation

- **Split A-5 into three pieces of different cost/urgency**:
  - **A-5a (small, decent UX)**: serialize `TripwireTriggered` (+ frontend alert) so a halted run says why. No crash exists, so this is a UX improvement, not an emergency — but cheap.
  - **A-5b (durable infra, high-leverage)**: build `export_event_schemas.py` → `events.json` → `events.ts` codegen + `event-schema-sync.yml` CI parity gate, and make the serializer exhaustive (no reachable `NotImplementedError` for a defined event). This converts all future silent drift into CI failures — the single highest-leverage A-5 item.
  - **A-5c (visibility, downstream of A-1/A-2/A-4)**: SSE wire format + Inspector UI for the diagnostic events (`ContextCompacted` / `StateCheckpointed` / `PromptBuilt` / `MemoryAccessed` / `Span*`). Sequence after the producers actually emit them.
- **Bundle note**: A-5c lands with/after A-2 (PromptBuilt) + A-4 (Span*); A-5a is standalone-cheap; A-5b can go anytime and pays for itself immediately.

**Updated Area-A picture**: A-5a (Tripwire UX) cheap & independent · A-5b (schema-sync CI) independent & high-leverage · A-5c (diagnostic visibility) downstream of A-1/A-2/A-4.

---

## 8. Definition-of-done signals (for the eventual sprint)

- **A-5a**: a tripwire violation produces a `tripwire_triggered` SSE frame (+ frontend alert) alongside `loop_end`; a test drives a tripwire and asserts both frames appear.
- **A-5b**: `export_event_schemas.py` emits all defined events to `events.json`; `events.ts` is codegen'd (no hand-written union); `event-schema-sync.yml` fails a PR that adds a backend event without regenerating; the serializer has a branch (or explicit, intentional skip) for **every** defined event so no `NotImplementedError` is reachable for a real event.
- **A-5c**: each diagnostic event has an SSE serializer + a frontend Inspector consumer; the Inspector sidebar shows checkpoint/compaction/prompt/memory/trace diagnostics for a live run.

---

## 9. Method note

Synthesized from a 2-agent parallel read-only audit, then **corrected against clean full reads** of `backend/src/api/v1/chat/sse.py` (lines 1-324) and `router.py` `_stream_loop_events` (300-360) on main `526be549` (Sprint 57.63 merged). The first draft was written during a window where the session's read tools truncated output, and it contained a fabricated `_SAFE_SKIP_EVENTS` mechanism + a wrong "Tripwire crash" claim; both are retracted above. Files were confirmed to exist via `git ls-files`. Effort/tier framing are judgement estimates, not commitments.
