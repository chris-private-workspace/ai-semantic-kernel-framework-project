# Sprint 57.159 Plan — compaction live drive-through + Inspector timeline marker (Cat 4 L2→L3)

**Summary**: Drives Cat 4 context compaction from **L2 (harness-verified only) → L3 (live drive-through)** — the reality-audit §3 gap (compaction 真壓縮過 9824→2679 但只在 harness 級證實,從未在真 chat-v2 上驅動,plain Q&A 無機會觸發). The `context_compacted` event is ALREADY fully wired (loop → sse → wire → store) but the chat-v2 store leaves it **rawEvents-only** (rich render deferred 57.66 "A-5c") → compaction's token reduction is INVISIBLE in the UI. This sprint (a) surfaces `context_compacted` as a persistent **timeline marker** in the chat-v2 turn flow (mirrors the 57.101 `message_injected` pseudo-turn), so compaction is observable; (b) drives a real long chat-v2 conversation (via the `CHAT_COMPACTION_TOKEN_BUDGET` lever) that triggers compaction, and verifies the agent STILL recalls earlier context/identity after compaction + the marker renders. FE-only surface (NO backend/wire/codegen — the event is already on the wire); a backend fix is a **contingency** only if the drive-through surfaces a real compaction-quality bug. MANDATORY drive-through (user-facing). CHANGE-126; NO design note (existing-field-surface + drive-through, not a new-domain spike — mirrors 57.120/131/133).

**Status**: Approved-to-execute (user AskUserQuestion 2026-07-07: engine-debt program → compaction range → "Option A compaction live drive-through (L2→L3)" + "Path B: drive-through + Inspector rich 面")
**Branch**: `feature/sprint-57-159-compaction-drivethrough-inspector`
**Base**: `main` HEAD `8eb3d261` (57.158 chore flip #373 merged; 57.158 feature #372 = `c709c3fe`)
**Slice**: standalone — Cat 4 L2→L3 drive-through + fills the deferred 57.66 "A-5c" for `context_compacted`. Engine-debt program, compaction range.
**Scope decisions**: (a) surface as a **persistent timeline marker** (mirrors `message_injected` pseudo-turn) NOT a transient Turn-tab KV row (57.131/133) — compaction is a session-flow event, and the drive-through payoff is SEEING the reduction in the main chat area, persistent in scrollback; (b) FE-only — the `context_compacted` event is already loop→sse→wire→store wired, so ZERO backend/wire/codegen/migration; (c) a backend compaction-quality fix is **contingency-only** (surfaced by the drive-through, like the memory drive-throughs); (d) parent-direct (the value is the drive-through I must drive), agent_factor 1.0.

---

## 0. Background

### The gap (Cat 4 L2 + `context_compacted` rawEvents-only)

- **Reality-audit §3**: Cat 4 Context compaction assessed **L2** (not L3) — "真壓縮過(9824→2679 tokens);但需多輪 corpus 才觸發,plain Q&A 無機會。harness 級證實,非 Potemkin". Compaction has NEVER been driven on a live chat-v2 conversation.
- **Observability gap**: `context_compacted` is fully wired to the chat-v2 store but the store case (`chatStore.ts:839-846`) leaves it **rawEvents-only** — "Rich Inspector render DEFERRED to A-5c (mirror guardrail_triggered)". So when compaction fires, the token reduction (`tokens_before→after`, strategy, `messages_compacted`) renders NOWHERE in the UI (only a bare `COMPACTION` span duration bar in the Trace tab via `InspectorTrace.tsx:70`).

### Why it matters (the missing capability)

A user driving a long conversation cannot SEE compaction happen — the platform silently drops ~73% of the context and the operator has no UI signal of what/when/how-much. Per the Drive-Through discipline ("結果真的渲染"), compacting an invisible thing is weak 落地. Raising Cat 4 to L3 = prove on a REAL conversation that (1) compaction fires + is visible, (2) the agent retains earlier context/identity post-compaction (compaction preserves meaning, not just cuts tokens).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `8eb3d261`) | Anchor |
|-------|-------------------------------------|--------|
| loop emits compaction | `yield ContextCompacted(tokens_before, tokens_after, compaction_strategy, messages_compacted, duration_ms, …)` after a triggered compact | `loop.py:2288-2301` |
| compaction fires pre-turn | compaction check is at the TOP of the while body, BEFORE `TurnStarted` | `loop.py:2221-2301` vs `2324` |
| serialized to wire | `context_compacted` `{tokens_before, tokens_after, compaction_strategy, messages_compacted, duration_ms}` (since 57.66) | `sse.py:397-407` |
| store: rawEvents-only | `case "context_compacted": … rawEvents` — rich render deferred A-5c | `chatStore.ts:839-846` |
| trigger lever | `CHAT_COMPACTION_TOKEN_BUDGET` env knob → `make_chat_compactor` | `_category_factories.py:123-131,183` |
| ≥3-turn gate | compaction only real-triggers ≥3 user turns + over budget | CLAUDE.md §Agent Loop 長運行邊界 |
| timeline pseudo-turn precedent | `message_injected` pushes a `{role:"user", injected:true}` marker turn | `chatStore.ts:558-577` |
| turn dispatch | `TurnList.tsx` dispatches by `turn.role` (user/agent/hitl) | `TurnList.tsx:76-78` |

→ The fix must (1) split the `context_compacted` store case out of the rawEvents-only bucket → push a `CompactionMarkerTurn` into `turns`; (2) add a `turns/CompactionMarker.tsx` role component + a `TurnList.tsx` dispatch branch; (3) drive a real long conversation past the lowered budget to trigger + verify.

### The design (FE-only: 1 store turn-variant + 1 mergeEvent case + 1 marker component + TurnList dispatch + i18n + tests)

```
chatStore.ts
  + interface CompactionMarkerTurn { role:"compaction"; id; at; tokensBefore; tokensAfter; strategy; messagesCompacted }
  + add to the Turn union
  case "context_compacted":            # was: rawEvents-only (:839-846)
    push CompactionMarkerTurn into turns  (still also rawEvents)  # fires BEFORE turn_started → marker precedes the turn it enabled

turns/CompactionMarker.tsx  (NEW)      # slim centered divider/chip, reuse existing mockup classes (NO new CSS/oklch/HEX)
  "⚡ Context compacted · 9,824 → 2,679 tokens (hybrid · 12 msgs)"
TurnList.tsx  + if (turn.role === "compaction") return <CompactionMarker .../>
i18n en + zh-TW  (reuse existing common.json "compaction" key + add reduction label)
```

WHY a timeline marker over a Turn-tab KV row (57.131/133): the Turn tab shows only the LAST AgentTurn → a compaction KV would vanish as the conversation continues. Compaction is a session-flow event; a persistent scrollback marker is both more observable AND semantically truer (it marks WHERE in the flow the context was compressed). It mirrors the proven `message_injected` pseudo-turn shape.

### Ground truth (recon head-start — code read on `main` HEAD `8eb3d261`; ALL re-verified §checklist 0.1)

- `chatStore.ts:839-846` — `context_compacted` currently `rawEvents` only (the surface gap).
- `chatStore.ts:558-577` — `message_injected` pseudo-turn precedent (push a `{role,…}` marker into `turns`).
- `TurnList.tsx:76-78` — role dispatch (add a 4th branch).
- `loop.py:2288-2301` — the `ContextCompacted` fields; `sse.py:397-407` — the wire shape.
- `_category_factories.py:123-131` — `CHAT_COMPACTION_TOKEN_BUDGET` (the drive-through trigger lever).
- `frontend/src/i18n/locales/{en,zh-TW}/common.json:24` — existing `"compaction"` key.

**Baselines (57.158 closeout)**: pytest ~3160+ · wire 26 · Vitest 925 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-context-compacted-rawevents** — grep `chatStore.ts` `case "context_compacted"` → confirm still rawEvents-only (not already surfaced by an intervening sprint).
- **D-turn-union-shape** — read the `Turn` union type def → confirm role literal union + where to add `"compaction"`.
- **D-marker-mockup-class** — grep the mockup / styles-mockup.css for an existing centered-divider/system-marker class to reuse (NO new CSS); fall back to the `message_injected` marker styling if none.
- **D-compaction-trigger-live** — confirm `CHAT_COMPACTION_TOKEN_BUDGET` low value + ≥3 user turns actually fires `compact_if_needed` on the chat path (the drive-through's core precondition); confirm the ≥3-turn gate wording in `context_mgmt`.
- **D-vitest-render-path** — confirm the chat-v2 Vitest test dir + the TurnList/mergeEvent test pattern to mirror.

## 1. Sprint Goal

Raise Cat 4 context compaction from L2 → L3: surface `context_compacted` as a persistent, observable timeline marker in chat-v2 (filling the deferred 57.66 A-5c), then PROVE on a real long chat-v2 conversation (real UI + real backend + real Azure LLM, `CHAT_COMPACTION_TOKEN_BUDGET` lowered) that compaction fires, the marker renders the token reduction, AND the agent still recalls earlier context/identity after compaction. Gates green (Vitest +N · mypy · run_all · lint/build) + a MANDATORY drive-through with screenshots + observed-vs-intended. CHANGE-126; NO design note. If the drive-through surfaces a real compaction-quality bug (context/identity lost), fix it (contingency, same-sprint) — that IS the L2→L3 value.

## 2. User Stories

- **US-1** (observability): 作為 operator，我希望在 chat-v2 對話流中看到「上下文在此被壓縮:9,824 → 2,679 tokens」的持久標記，以便我知道平台何時、壓縮了多少 context，而不是靜默丟棄。
- **US-2** (drive-through, MANDATORY): 作為 QA/開發者，我希望在真 UI + 真後端 + 真 LLM 上驅動一段夠長的對話觸發 compaction，並確認壓縮後 agent 仍記得對話早期建立的 context/identity，以便把 Cat 4 從 L2 提到 L3(非 harness-only)。
- **US-3** (closeout): 作為維護者，我希望 CHANGE-126 + calibration + navigators 更新，把 L2→L3 的證據與任何 contingency fix 記錄下來。

## 3. Technical Specifications

### 3.0 Architecture (FE-only; NO backend/wire/codegen/migration — the event is already loop→sse→wire→store wired)

```
EDIT   frontend/src/features/chat_v2/store/chatStore.ts       # +CompactionMarkerTurn type + Turn union + context_compacted case pushes marker
NEW    frontend/src/features/chat_v2/components/turns/CompactionMarker.tsx   # slim centered marker, reuse mockup classes
EDIT   frontend/src/features/chat_v2/components/TurnList.tsx   # +role==="compaction" dispatch branch
EDIT   frontend/src/i18n/locales/en/common.json               # +compaction reduction label
EDIT   frontend/src/i18n/locales/zh-TW/common.json            # +compaction reduction label (繁中)
NEW/EDIT frontend/src/features/chat_v2/**/*.test.ts(x)         # store case + marker render Vitest
UNTOUCHED  loop.py / sse.py / event_wire_schema.py / generated/* / any backend  # already wired; ZERO change
```

### 3.1 Store — `chatStore.ts` (US-1)

- Add `CompactionMarkerTurn { role: "compaction"; id: string; at: string; tokensBefore: number; tokensAfter: number; strategy: string; messagesCompacted: number }` to the `Turn` union.
- `case "context_compacted"`: currently pushes to rawEvents only (:839-846). Change to ALSO push a `CompactionMarkerTurn` into `s.turns` (mirrors `message_injected` :558-577). Keep rawEvents (audit trail). The marker naturally precedes the turn it enabled (compaction fires before `turn_started`).

### 3.2 Render — `turns/CompactionMarker.tsx` (NEW) + `TurnList.tsx` (US-1)

- A slim centered divider/chip showing `⚡ Context compacted · {tokensBefore} → {tokensAfter} tokens ({strategy} · {messagesCompacted} msgs)` with locale label. Reuse an EXISTING mockup class (Day-0 D-marker-mockup-class) — NO new CSS / oklch / HEX literal (mockup-fidelity 鐵律).
- `TurnList.tsx`: add `if (turn.role === "compaction") return <CompactionMarker key={turn.id} turn={turn} />;`.

### 3.3 i18n (US-1) — `common.json` en + zh-TW

- Reuse the existing `"compaction"` key (en "Compaction" / zh-TW "上下文壓縮"); add a reduction-label string if the marker needs interpolation copy. Follow codebase i18n convention (mirror mockup `reference/design-mockups/i18n.jsx` if it has one; else concise English key + 繁中 value).

### 3.4 Drive-through (US-2, MANDATORY) — real UI + backend + Azure LLM

- Clean-restart backend with `CHAT_COMPACTION_TOKEN_BUDGET` lowered (Day-0-determined value, e.g. ~2000-4000) so a realistic ≥3-user-turn conversation exceeds it. (Risk Class E: verify the LIVE serving worker picked up the env — startup-loaded knob.)
- On chat-v2: Leg 1 establish early context/identity ("my name is X; project Aurora uses Oracle→Postgres") + pad turns until compaction fires → confirm the **CompactionMarker renders** with real `tokens_before→after`. Leg 2 (post-compaction) ask something requiring the EARLY context ("what DB migration were we discussing?") → confirm the agent STILL recalls it (compaction preserved meaning). Screenshot both + observed-vs-intended into progress.md.
- If the agent LOSES early context/identity post-compaction → a real bug → root-cause + contingency fix (same sprint); that is the L2→L3 payoff, not a failure of the sprint.

### 3.x What is explicitly NOT done

- No backend/wire/codegen/migration change (event already wired) — unless the drive-through forces a contingency compaction-quality fix.
- No Turn-tab KV row (transient) — the timeline marker supersedes it for this event.
- No per-tenant compaction config (`AD-Compaction-Preclear-PerTenant-Phase58`) / no tool-anchored preclear (`AD-Compaction-ToolAnchored-Preclear-Phase58`) — separate slices.
- No compaction strategy/threshold change — measure + surface what exists.

### 3.y Validation (US-1..US-3)

Gates: mypy `src` 400 (no backend change) · run_all 11/11 · pytest (unchanged, FE-only) · Vitest 925 +N · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 N/A (no py) but re-run clean · LLM-SDK-leak N/A. Plus the §3.4 drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 0 | `frontend/src/features/chat_v2/types.ts` | EDIT (Day-0 drift D-turn-union-shape: `+CompactionMarkerTurn` + `Turn` union — the type lives here, not chatStore.ts) |
| 1 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT (context_compacted case → push marker) |
| 2 | `frontend/src/features/chat_v2/components/turns/CompactionMarker.tsx` | NEW |
| 3 | `frontend/src/features/chat_v2/components/TurnList.tsx` | EDIT (+dispatch branch) |
| 4 | `frontend/src/i18n/locales/en/common.json` | ~~EDIT~~ **DROPPED** (surrounding turn components use English literals not i18n — match-surrounding-code) |
| 5 | `frontend/src/i18n/locales/zh-TW/common.json` | ~~EDIT~~ **DROPPED** (same) |
| 6 | `frontend/src/features/chat_v2/**/*.test.ts(x)` | NEW/EDIT (store case + marker render) |
| — | `loop.py` / `sse.py` / `event_wire_schema.py` / `generated/*` / backend | **UNTOUCHED** (already wired) |
| — | `docs/.../sprint-57-159/{progress,retrospective}.md` + `claudedocs/4-changes/feature-changes/CHANGE-126-*.md` | NEW (docs) |

## 5. Acceptance Criteria

1. `context_compacted` renders a persistent `CompactionMarker` in the chat-v2 timeline showing real `tokens_before → tokens_after (strategy · N msgs)`; rawEvents audit trail retained.
2. Vitest covers the store case (marker pushed into `turns`) + the marker render; mockup `diff` empty; `npm run build` clean (NO `--silent`).
3. **Drive-through PASS (MANDATORY, real UI + backend + Azure LLM)** — a live ≥3-turn conversation (budget lowered) triggers compaction, the marker renders the real reduction, AND the agent recalls earlier context/identity after compaction; screenshot + observed-vs-intended in progress.md. (NOT gate-only.) Cat 4 L2→L3.
4. Cat 4 L2→L3 documented; CHANGE-126; calibration recorded (`chatv2-compaction-drivethrough-surface` 0.85); navigators + next-phase-candidates updated; any contingency backend fix recorded.

## 6. Deliverables

- [ ] US-1 `CompactionMarker` timeline surface (store + component + dispatch + i18n)
- [ ] US-2 live compaction drive-through (marker renders + context-retention verified) — MANDATORY
- [ ] US-3 closeout (CHANGE-126 + calibration + navigators)

## 7. Workload Calibration

- Scope class **NEW `chatv2-compaction-drivethrough-surface` 0.85** — anchored to `chatv2-inspector-existing-field-surface` 0.85 (57.120/131/133: surface an already-store-captured wire field in a NEW render location, tiny FE code + full ceremony + parent-direct + MANDATORY drive-through). Set 0.85 not the 0.45-0.55 pure-repoint band per the 57.120 generalizable insight (tiny-code + full-ceremony + mandatory-drive-through is ceremony-dominated, not code-accelerated). Slightly heavier than the KV-row surfaces (a new turn variant + component + a long-conversation drive-through setup) but that's offset by the FE-only ZERO-backend surface. NEW class → KEEP 0.85 as 1st data point; if it lands > 1.20 (the long-conversation drive-through staging + a contingency backend fix are the variance drivers) re-point toward 1.0.
- **Agent-delegated: no** (parent-direct; the sprint's value is the drive-through I must drive + a possible contingency backend fix). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5.5 hr (FE surface ~2 hr: store type + case + component + TurnList + i18n + Vitest; drive-through ~2.5 hr: budget-lower + long conversation + trigger + context-retention verify + screenshots + clean-restart; closeout ~1 hr) → class-calibrated commit **~4.7 hr** (mult 0.85). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Compaction won't trigger live** (budget too high / <3 turns) | Day-0 D-compaction-trigger-live: confirm `CHAT_COMPACTION_TOKEN_BUDGET` low value + the ≥3-turn gate; pad the conversation with long turns until `tokens_used` exceeds budget. |
| **Stale `--reload` worker masks the lowered budget** (Risk Class E) | Clean-restart the backend + verify the LIVE serving worker (Win32_Process PID/PPID/StartTime sweep, 57.97 lesson) picked up the env BEFORE driving. |
| **Drive-through finds compaction drops context/identity** | That IS the L2→L3 value — root-cause + contingency backend fix same-sprint (like the memory drive-throughs); re-scope §Acceptance if the fix is large. |
| **Marker attaches to wrong turn** (fires before turn_started) | Semantically the marker PRECEDES the turn it enabled — a scrollback marker between turns is correct; verify ordering in the drive-through. |
| **New CSS drift** (mockup-fidelity 鐵律) | Reuse an existing mockup marker/divider class (Day-0 D-marker-mockup-class); NO new oklch/HEX; mockup `diff` empty gate. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Tool-anchored preclear single-send fix — `AD-Compaction-ToolAnchored-Preclear-Phase58`.
- Per-tenant compaction config — `AD-Compaction-Preclear-PerTenant-Phase58`.
- Compaction strategy/threshold tuning or a new A/B — this sprint surfaces + drives what exists.
- Turn-tab KV compaction row — superseded by the timeline marker.
