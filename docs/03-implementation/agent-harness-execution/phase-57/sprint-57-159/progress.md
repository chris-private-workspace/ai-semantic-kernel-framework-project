# Sprint 57.159 Progress — compaction live drive-through + Inspector timeline marker

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-159-plan.md`
**Base**: `main` HEAD `8eb3d261` (57.158 chore #373 merged; 57.158 feature #372 = `c709c3fe`)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — 2026-07-07

### Prong 1 — path verify ✅
- EDIT targets EXIST: `chatStore.ts` (`:839-846` context_compacted case), `types.ts` (`:215` Turn union), `TurnList.tsx` (`:76-78` dispatch), `common.json` en+zh-TW (`:24` compaction key).
- NEW free (Glob 0): `turns/CompactionMarker.tsx`.
- `CHANGE-126` free (highest 125); NO design note (feature-continuation existing-field-surface, not a new-domain spike — mirrors 57.120/131/133).
- Backend UNTOUCHED-verify: `loop.py:2288` `ContextCompacted` + `sse.py:397` serializer + `event_wire_schema.py` all already carry `context_compacted` — ZERO backend/wire/codegen edit needed.

### Prong 2 — content verify (drift findings)

| D | Finding | Implication |
|---|---------|-------------|
| **D-context-compacted-rawevents** ✅ | `chatStore.ts:839-846` — `case "context_compacted": … return { ...s, rawEvents }` (grouped with prompt_built/state_checkpointed/tripwire_triggered), comment "Rich Inspector render DEFERRED to A-5c". | The surface gap is confirmed: the event is store-recognized but rendered NOWHERE. Split it out → push a marker into `turns`. |
| **D-turn-union-shape** ⚠️ DRIFT | `Turn = UserTurn \| AgentTurn \| HITLTurn` is defined in **`types.ts:215`** (each a `role`-discriminated object type), NOT in `chatStore.ts`. Plan §3.1 said "chatStore.ts" for the type. | Add `CompactionMarkerTurn { role:"compaction"; … }` to **`types.ts`** + extend the `Turn` union there; the `context_compacted` case edit stays in `chatStore.ts`. §File Change List +1 file (`types.ts`). <5% scope shift → PROCEED. |
| **D-marker-mockup-class** ✅ | `styles-mockup.css:1166` `.thin-rule` (slim 1px divider) + `.badge` / `.route-pill` exist; `message_injected` uses a full `.turn` shell (`UserTurn.tsx:46`, `.turn-marker` dot :753-761). | Compose the compaction marker from existing classes (a `.thin-rule` divider + a centered `.badge`-style label) → NO new CSS/oklch/HEX (mockup-fidelity 鐵律). Day-1 picks slim-divider vs mini-turn-shell; both reuse existing classes. |
| **D-compaction-trigger-live** ✅ | `_category_factories.py:123-131` `CHAT_COMPACTION_TOKEN_BUDGET` env knob → `make_chat_compactor` (:183); CLAUDE.md: compaction real-triggers ≥3 user turns + over budget (75k default → normal chat never fires). | Drive-through Day 3: set the knob low (pin exact value at setup, ~2000-4000) + a ≥3-turn padded conversation exceeds it → compaction fires. Risk Class E: verify the LIVE worker picked up the startup-loaded knob. |
| **D-vitest-render-path** ✅ | `frontend/tests/unit/chat_v2/chatStore.mergeEvent.test.ts` (mergeEvent case tests) + `frontend/tests/unit/chat_v2/components/*.test.tsx` (component render). | Extend mergeEvent.test.ts for the `context_compacted`→marker case + a CompactionMarker render test under components/. |

### Prong 3 — schema verify
- **N/A** — ZERO DB/wire/codegen change. The `context_compacted` event is already in `event_wire_schema.py` + `generated/loopEvents.generated.ts` (wire 26 unchanged). No migration/column.

### D-baselines (re-verify at branch `8eb3d261`)
- Backend unchanged (FE-only): mypy `src` 400 / run_all 11/11 / pytest — cite last-known, unaffected (no py edit). Wire 26.
- FE gates to move: Vitest 925 (57.156) +N · mockup 51 (`diff` empty). (Full Vitest + mockup re-run at Day-2 full gate.)

### Go/no-go
- **PROCEED.** 1 minor drift (D-turn-union-shape: type lives in `types.ts` not `chatStore.ts` → +1 file to §Change List, <5% shift). All 5 D-items confirmed the plan against real code; the `context_compacted` event is fully wired (backend→sse→wire→store) so this is a pure FE-surface + drive-through sprint (ZERO backend unless the drive-through forces a contingency compaction-quality fix). Reusable mockup classes confirmed (`.thin-rule` + `.badge`) → no CSS drift risk.

---

## Day 1-2 — FE compaction-marker surface (US-1) — 2026-07-07

**Done** (FE-only; the `context_compacted` event is already loop→sse→wire→store wired):
- `types.ts` (EDIT) — `+CompactionMarkerTurn { role:"compaction"; id; at; tokensBefore; tokensAfter; strategy; messagesCompacted }` + extended the `Turn` union (`:215`; the D-turn-union-shape drift finding — type lives in types.ts not chatStore.ts).
- `chatStore.ts` (EDIT) — split `case "context_compacted"` out of the rawEvents-only bucket → pushes a `CompactionMarkerTurn` into `s.turns` (mirrors `message_injected` :558-577); rawEvents audit trail retained (dual-emit). Fires before `turn_started` → marker precedes the turn it enabled.
- `turns/CompactionMarker.tsx` (NEW) — slim centered marker "⚡ Context compacted · 9,824 → 2,679 tokens (hybrid · 12 msgs)"; reuses the mockup `.badge.warning` chip (compaction == warning, matching `InspectorTrace.tsx:70` COMPACTION span color) → NO new CSS/HEX/oklch; layout-only inline styles via the established `turns/` escape pattern (`AgentTurn.tsx:47`).
- `TurnList.tsx` (EDIT) — `+import CompactionMarker` + `if (turn.role === "compaction") return <CompactionMarker .../>` dispatch branch.
- **i18n common.json DROPPED** (scope reduction) — the surrounding turn components (`UserTurn`/`AgentTurn`) use English literals, NOT i18n (`UserTurn.tsx:56` "injected mid-run"); matching the surrounding-code convention → the marker uses an English literal, no `common.json` edit. YAGNI + match-surrounding-code.
- Tests: `chatStore.mergeEvent.test.ts` (+1 — context_compacted → marker in `turns` + rawEvents retained) + `components/CompactionMarker.test.tsx` (NEW — renders token reduction/strategy/msgs).

**Full FE gate**: Vitest **927 passed** (baseline 925 **+2**; 149 files) · Lint `LINT_EXIT=0` (clean) · Build (tsc+vite) ✅ · mockup-fidelity **51 baseline byte-identical** (no new HEX/oklch). Backend UNTOUCHED → mypy `src` 400 / run_all 11/11 unchanged (Day-4 pre-commit re-confirm).

**Next (Day 3)**: the MANDATORY live compaction drive-through (real UI + backend + Azure LLM, `CHAT_COMPACTION_TOKEN_BUDGET` lowered) — the L2→L3 core. Verify (a) compaction fires + the marker renders the real reduction, (b) the agent retains earlier context/identity post-compaction.

## Day 3 — Live compaction drive-through (US-2, MANDATORY) — L2→L3 — 2026-07-07

**Setup**: real chat-v2 (existing vite dev `:3007`, HMR'd my source) + real backend (fresh single-process uvicorn `:8000`, NO `--reload` → Risk Class E clean) + real Azure gpt-5.2 + Qdrant/Postgres/Redis (docker up). Backend launched with `CHAT_COMPACTION_TOKEN_BUDGET=3000` (trigger at 3000×0.75=2250). Two drives (keep_recent env varied to expose the reduction cutoff). Playwright MCP drove dev-login (jamie/priya) → chat-v2.

### Verdict: US-1 ✅ + US-2 ✅ + a genuine L2→L3 finding

**US-1 — the CompactionMarker renders LIVE on the real chat path** ✅
- Drive 1 (`keep_recent=2`): 8 markers rendered as the agent ran a long tool-using send (`memory_write` + `write_todos`), e.g. `⚡ Context compacted · 4,086 → 4,086 tokens (hybrid · 0 msgs)` … growing to `35,144 → 35,144`. The `.badge.warning` chip surfaced in the timeline, persistent in scrollback (artifact `leg1`).
- Drive 2 (`keep_recent=1`): captured a **REAL reduction** — `⚡ Context compacted · 4,604 → 1,770 tokens (hybrid · 8 msgs)` (−62%, 8 messages compacted) — the marker renders `before → after` distinctly (artifact `leg3`).
- **Before this sprint the token reduction was INVISIBLE** (`context_compacted` was rawEvents-only) — the marker is the observability surface that makes compaction driveable. Confirmed: the event was already loop→sse→wire→store wired; only the render was missing.

**US-2 — the agent retains earlier context/identity AFTER compaction** ✅
- Drive 1: after 8 compaction events + context grown to 35k, a recap query recalled ALL send-1 facts — "Project Aurora, **Oracle (source) → PostgreSQL (target)**, Q3 cutover; single top risk = invoice precision, **Oracle NUMBER(38,4) vs PostgreSQL NUMERIC**" — Verification **0.99** (artifact `leg2`).
- Drive 2: after the real 4,604→1,770 reduction, the agent's answer recalled "**Beacon Assurance** auditor, **October** window, **Project Lodestar**" — Verification **0.99**. Compaction preserved meaning, not just cut tokens.

### 🔴 L2→L3 FINDING (the drive-through discovery — "引擎接好但落地無效")

Compaction **triggers every over-budget turn** (correctly: `token_usage > budget×0.75`) BUT **reduces 0 messages** on the chat path unless `len(user_indices) > keep_recent_turns` (`structural.py:126` cutoff). Because the chat main flow runs ONE user message per send (a multi-turn tool run shares ONE user turn), `user_indices` stays ≤ keep_recent → structural keeps everything → **context grows unbounded** (Drive 1: 4k → 35k across a single 20-turn send, 8 no-op compactions). Only a cross-user-turn boundary with `keep_recent < user_turns` actually reduces (Drive 2 `keep_recent=1`, 2 user turns → the one 4,604→1,770 reduction; subsequent same-send turns re-grow to 29k and no-op again).

- **Not a "context lost" bug** — retention passed 0.99 on both drives → NOT a same-sprint contingency fix per plan §8. It is a compaction-**effectiveness** gap (reduction keyed on USER turns, not loop turns; a long agentic run is unprotected).
- The 57.109 `_category_factories.py:136-141` comment already acknowledges the single-user-message limitation; the drive-through makes its RUNTIME impact visible (8 no-op compactions previously silent) and shows the ACON preclear layer (57.139, `CHAT_COMPACTION_PRECLEAR_RATIO`, default OFF) is the intended tool-result-clearing answer for single-user-turn growth.
- **Registered carryover**: `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (make compaction reduce within a long single-user-turn tool run — e.g. loop-turn-based masking / auto-tune keep_recent / default-on preclear) + `AD-Compaction-Marker-Inspector-Trace-Correlate` (link the marker to its Trace-tab COMPACTION span).

### Observed vs intended + honesty
- Intended: drive compaction live + verify the marker + context retention. **Observed**: exactly that + the no-op-reduction finding (a bonus L2→L3 discovery, same value as the memory drive-throughs' bug finds).
- Honest scope note: the real-reduction leg used `keep_recent=1` (a non-default env lever) to FORCE the reduction cutoff — this proves the marker's `before>after` display + confirms the root cause is the user-turn cutoff, NOT that default deployments reduce. The default behavior IS the no-op finding.
- Artifacts: `artifacts/sprint-57-159-leg{1,2,3}-*.png`.

## Day 4 — <pending: CHANGE-126 + closeout>
