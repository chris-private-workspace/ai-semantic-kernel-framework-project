# Sprint 57.37 — AD-LoopDebug-Full-Rebuild-And-StateInspector-Repoint

**File**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-37-plan.md`
**Purpose**: Plan for Sprint 57.37 — **2-domain batched sprint**. **Domain A**: `/loop-debug` full mockup-fidelity rebuild (closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint violation — fixture demo events + 4 NEW widgets shipped). **Domain B**: `/state-inspector` Phase-2 verbatim CSS re-point (8th `frontend-verbatim-css-repoint` app; 4th non-rich-dashboard shape data point — discriminates the multi-dimensional-variance hypothesis Sprint 57.36 NEW).
**Category**: Sprint planning / Phase 57+ Frontend SaaS — Phase-2 per-page re-point epic + mockup-fidelity gap closure
**Scope**: Phase 57+ Frontend SaaS — Phase-2 epic, 8th + 9th application; closes Sprint 57.36 carryover gap
**Created**: 2026-05-24
**Last Modified**: 2026-05-24
**Status**: Draft → awaiting user approval

> **Modification History**
> - 2026-05-24: Initial draft (Sprint 57.37 Day 0) — 2-domain batched after user-reported `/loop-debug` empty-state vs mockup gap (Sprint 57.36 closeout follow-up); Domain A closes the §Frontend Mockup-Fidelity Hard Constraint violation that Sprint 57.36 inadvertently introduced

---

## 0. Sprint Goal

Land **two distinct Phase-2 epic deliverables** in one batched sprint:

### Domain A — `/loop-debug` Full Mockup-Fidelity Rebuild (closes Sprint 57.36 gap)

After Sprint 57.36 shipped `/loop-debug` as "verbatim CSS re-point + AP-2 banner deferring playback/scrubber/filter/inspector pane to Phase 58+", **user reported the page is essentially empty** vs mockup which is rich with content (24 events / playback strip / filter pills / 2-col inspector pane). Root cause: Sprint 57.36's "Option A" choice (which I proposed and user approved) **conflicts with CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint**:

> 後端尚未支援的 widget → **仍依 mockup 視覺實作，data 用 fixture**；後續 sprint 加 backend API
> **不允許因後端沒有就改 mockup widget layout / 刪 widget**

Sprint 57.36's "AP-2 deferral" approach effectively **deleted mockup widgets** (playback strip + filter pills + inspector pane), violating the hard constraint. This sprint **corrects that** by:

1. Adding a 24-event fixture (`_fixtures/demoLoopEvents.ts`) in production `LoopEvent` shape that maps the mockup's `page-governance.jsx:5-31` `LoopEvents` array.
2. Empty-state branch (when `useChatStore.rawEvents.length === 0` AND `mode === "standalone"`) → render fixture so page is never empty.
3. Implementing the **4 NEW mockup widgets** with fixture data:
   - **Playback strip** (cursor + play/pause + scrubber + speed pills 1×/4×/8×/16×) — pure UI state, no backend
   - **Filter pills** (per-category toggle: thinking / tool / memory / hitl / verification / subagent) — pure UI state
   - **Inspector right pane** with selected-event detail (KvRow rows + HITL Policy section + Raw payload JSON)
   - **Updated AP-2 BackendGapBanner** copy: now disclosing "DEMO DATA when no live SSE events; full event-detail persistence Phase 58+" instead of the prior overly-aggressive "playback / inspector deferred Phase 58+" wording

4. **Inline mode (chat-v2 cascade) unchanged** — compact `.loop-track` without canvas / banner / inspector / playback (matches Sprint 57.30 ship state).

### Domain B — `/state-inspector` Phase-2 Verbatim CSS Re-Point (8th app)

`/state-inspector` is the **next clean 1-file non-rich Phase-2 re-point candidate** per Sprint 57.36 retro Q5 #1 recommendation. Production `StateInspectorPage.tsx` (366 lines, Sprint 57.19 ship) uses **Tailwind utility classes throughout** (`TONE_CLASS` Record + `bg-X/16 text-X` patterns) — classic Sprint 57.18-57.27 HSL-translation vintage. Re-point to mockup verbatim classes from `reference/design-mockups/page-platform.jsx:21+` (StateInspector + sub-components). No AP-2 banner / no dual-mount / no fixture work needed (the page already has mockup-shaped fixture data per Sprint 57.19 US-C4 ship — only the CSS layer needs swap).

**3rd "simple non-rich" data point** for the `frontend-verbatim-css-repoint` 0.50 class — discriminates the multi-dimensional-variance hypothesis (Sprint 57.36 NEW):
- 57.34 (1-file no AP-2 no dual-mount) = 1.0 in band → "simple" baseline candidate
- 57.36 (1-file + AP-2 + dual-mount) = 1.42 above band
- **57.37 Domain B (1-file no AP-2 no dual-mount)** = should land in [0.85, 1.20] band IF "simple" baseline hypothesis correct → strengthens proposal for class split `-simple` (0.50) vs `-with-ap2-or-dual-mount` (0.65) in Sprint 57.38 retro

---

## 1. Background

### 1.1 Why batched (2 domains in 1 sprint)

Per user selection at sprint kickoff:

1. **Domain A is high-priority user-reported gap** — `/loop-debug` empty state is operationally useless; needs immediate fix to honor CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint.
2. **Domain B is the natural next Phase-2 epic pickup** — Sprint 57.36 retro Q5 #1 recommendation. Bundling avoids a separate Sprint 57.38 just for `/state-inspector`.
3. **Batching produces 2 calibration data points in 1 sprint** — one for each class (`frontend-mockup-strict-rebuild` 5th app + `frontend-verbatim-css-repoint` 8th app). User noted "更完整的 calibration data point".
4. **Operational overhead amortizes** — single PR / closeout / 22-route sweep across both.

### 1.2 Mockup source mapping (Day 0 Prong 2 to confirm)

#### Domain A (`/loop-debug`) — `reference/design-mockups/page-governance.jsx`

| Mockup component | Mockup file:line | Production target | Disposition |
|------------------|------------------|-------------------|-------------|
| `LoopEvents` 24-event fixture | L5-31 | NEW `_fixtures/demoLoopEvents.ts` (production LoopEvent shape) | **NEW**: hand-craft 24 events in `LoopEvent` union (loop_start / turn_start / llm_request / tool_call_request/result / verification_passed/failed / approval_requested / hitl events) |
| `LoopDebug` main shell | L33-116 | `LoopVisualizer.tsx` standalone branch | re-point: `.loop-canvas` 2-col + `.loop-track` left + `.loop-inspector` right (with content, not placeholder) |
| `LoopDebugHeader` (controls) | L118-185 | NEW component inside `LoopVisualizer.tsx` or `_components/LoopPlaybackHeader.tsx` | **NEW**: title + filter pills + playback strip with cursor / play/pause / scrubber / speed |
| `EventRow` per-event | L187-212 | `LoopVisualizer.tsx` event render | re-point (Sprint 57.36 already did this; preserve) |
| `LoopInspector` right pane | L214-263 | NEW component inside `LoopVisualizer.tsx` or `_components/LoopInspector.tsx` | **NEW**: selected-event detail (KvRow rows + HITL Policy + Raw payload) |
| `KvRow` helper | L265-270 | NEW helper inside `LoopVisualizer.tsx` or `_components/KvRow.tsx` | **NEW**: shared helper |

#### Domain B (`/state-inspector`) — `reference/design-mockups/page-platform.jsx`

| Mockup component | Mockup file:line | Production target | Disposition |
|------------------|------------------|-------------------|-------------|
| `StateInspector` main page | L21+ (first major section; verify exact line range Day 0) | `StateInspectorPage.tsx` (366 lines) | re-point: Tailwind utility → mockup classes |
| `TONE_CLASS` Record (`bg-X/16 text-X`) | n/a (production-local) | StateInspectorPage.tsx L48-58 | **DROP**: replace with `eventTone()`-style direct `var(--token)` reference |

### 1.3 Scope boundaries

**IN scope**:

- Domain A:
  - `frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts` (NEW, ~50-80 lines fixture data)
  - `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` (modify; +200-300 lines for playback / filter / inspector / fixture loader logic)
  - Optionally split out: `_components/LoopPlaybackHeader.tsx`, `_components/LoopInspector.tsx`, `_components/KvRow.tsx` (agent decides per code complexity; if extracted, expect 3 NEW files; if inlined, all in LoopVisualizer.tsx)
- Domain B:
  - `frontend/src/pages/state-inspector/StateInspectorPage.tsx` (modify in place; ~+150/-100 lines for verbatim class swap)
- Both:
  - Vitest spec updates if class selectors change
  - 22-route regression sweep before / after
  - `frontend/scripts/route-sweep.mjs` OUT_DIR re-pointed

**OUT of scope** (Phase 58+ pending backend):

- Real SSE event persistence (`loop_event` table) — playback only operates on fixture or live in-memory rawEvents
- Real chat-v2 session integration for /loop-debug live-event playback (works on current rawEvents — same as Sprint 57.36)
- StateInspector live-data version-chain endpoint (Sprint 57.19 AD-State-VersionChain-Phase58)
- IAM Block B / WebAuthn UI / other Phase 58+ ADs

### 1.4 Class baselines — HYBRID blend across 2 domains

| Component | Class | Multiplier | Weight |
|-----------|-------|------------|--------|
| Day 0 三-prong + before-baseline + 2-domain mockup mapping | `audit-cycle` | 0.85 | ~10% |
| Domain A — fixture + playback + filter + inspector + AP-2 banner update | `frontend-mockup-strict-rebuild` | 0.60 | ~45% |
| Domain B — StateInspectorPage.tsx verbatim CSS swap | `frontend-verbatim-css-repoint` | 0.50 | ~25% |
| Day 3 — 22-route sweep + 2-domain fidelity verify | sweep | 0.50 | ~5% |
| Day 4 — Closeout (2-class matrix update) | `closeout` | 0.80 | ~15% |
| **HYBRID blended baseline** | | **≈ 0.58** | |

Bottom-up estimate:
- Day 0: ~1 hr (2-domain mockup mapping; more than 57.36's 1-domain 0.75 hr)
- Day 1 (Domain A fixture + playback state + filter): ~2 hr
- Day 2 (Domain A inspector pane + AP-2 banner correction + Vitest): ~2-2.5 hr
- Day 3 (Domain B verbatim CSS swap): ~2-2.5 hr
- Day 3.5 (22-route sweep + verify both domains): ~0.5 hr
- Day 4 (2-class closeout): ~1.5 hr
- **Total: ~9.5-10 hr**

Calibrated commit: **~5.5 hr** (multiplier 0.58 HYBRID; matches user's "~6-8 hr" estimate at sprint kickoff).

Day 1-3 will be agent-delegated per Sprint 57.34/57.35/57.36 model (4th consecutive code-implementer; pattern validated).

### 1.5 2-domain calibration evaluation criteria

#### Domain A — `frontend-mockup-strict-rebuild` 0.60 (5th application)

Prior data: 57.23 (0.59) / 57.24 v2 (1.19) / 57.25 (0.88) / 57.27 (≈0.95) — 4-pt mean 0.90 in band.

| 57.37 Domain A ratio | Interpretation |
|---------------------|----------------|
| 0.85-1.20 (in band) | KEEP 0.60 baseline; 5-pt mean stable; class healthy |
| <0.85 (below) | Possible lift candidate (would be 0.60 → 0.50 if 3-sprint window trips) |
| >1.20 (above) | Possible lift candidate (would be 0.60 → 0.70 if 3-sprint window trips) |

#### Domain B — `frontend-verbatim-css-repoint` 0.50 (8th application; 4th shape-validation data point)

Prior data: 57.29 (≈1.0) / 57.30 (≈0.40) / 57.31 (≈0.35) / 57.32 (~0.40-0.55) / 57.34 (≈1.0) / 57.35 (~1.7) / 57.36 (~1.42). 3 non-rich pts (57.34/57.35/57.36) = 1.0/1.7/1.42 mean 1.37.

| 57.37 Domain B ratio | Interpretation for multi-dimensional-variance-watch AD |
|---------------------|--------------------------------------------------------|
| **0.85-1.20 (in band)** | **STRONG signal for "simple" sub-class** (no AP-2 / no dual-mount = 57.34 + 57.37); proposes Sprint 57.38 class split `-simple` (0.50) vs `-with-ap2-or-dual-mount` (0.65) |
| <0.85 (below) | "simple" baseline IS 0.50 still healthy at low end |
| >1.20 (above) | Multi-D variance is class-wide; lift 0.50 → 0.60 proposal strengthens |

This is the **decisive 4th non-rich data point** — if "simple" landed in band twice (57.34 + 57.37), class split proposal becomes empirically supported.

---

## 2. User Stories

### Domain A — /loop-debug

#### US-A1 — Fixture demo data prevents empty-state UX
**As an operator** opening `/loop-debug` without first running a chat-v2 session,
**I want** to see a populated visualizer with 24 demo events (matching mockup) instead of empty state,
**so that** I understand the page's capabilities immediately + can interact with playback / filter / inspector pane.

**Acceptance**: When `useChatStore.rawEvents.length === 0` AND `mode === "standalone"`, render the `demoLoopEvents` fixture; when real events present, real events take precedence; banner says "DEMO DATA" only when fixture is active.

#### US-A2 — Playback strip operates on visible events (fixture or live)
**As an operator** browsing /loop-debug,
**I want** play / pause / scrubber / speed controls (1× / 4× / 8× / 16×) like the mockup,
**so that** I can step through events at my chosen pace.

**Acceptance**: `cursor` state (0..events.length); `playing` boolean; `speed` enum; React `useEffect` interval at `1000/speed` ms advances cursor; visible events = events.slice(0, cursor); strip rendered per mockup L154-184 with mockup classes + verbatim styling.

#### US-A3 — Filter pills per category toggleable
**As an operator** browsing /loop-debug,
**I want** filter pills (thinking / tool / memory / hitl / verification / subagent) like the mockup,
**so that** I can focus on event categories of interest.

**Acceptance**: 6 pills rendered per mockup L132-150; each pill has `opacity: 1 | 0.35` based on filter state; click toggles; visible events filter applied after cursor filter.

#### US-A4 — Inspector right pane shows selected-event detail
**As an operator** clicking an event row,
**I want** the right inspector pane to show detail (KvRow rows: ts / turn / audit_id / span_id / tenant / session_id / agent + HITL Policy section if HITL event + Raw payload JSON),
**so that** I can investigate event context without leaving the page.

**Acceptance**: `selected` index state; click event row updates selected; inspector pane renders detail per mockup L214-263; gracefully handles non-HITL events (hide HITL Policy section).

#### US-A5 — AP-2 BackendGapBanner copy corrected
**As an auditor** reading the AP-2 banner,
**I want** the banner to honestly disclose what IS fixture data vs what's deferred,
**so that** the page transparency matches actual scope.

**Acceptance**: Banner reason updated to "DEMO DATA — these events are fixture data from the mockup; live SSE events populate when chat-v2 session runs; per-event detail persistence + cross-session lookup require backend SSE event persistence (Phase 58+ per Sprint 57.12 AP-6)." Banner shows in standalone only; absent in inline (chat-v2 cascade).

### Domain B — /state-inspector

#### US-B1 — Verbatim mockup CSS classes adopted
**As an operator** browsing `/state-inspector`,
**I want** the page to look pixel-faithful to `reference/design-mockups/page-platform.jsx` StateInspector,
**so that** production matches design QA.

**Acceptance**: `StateInspectorPage.tsx` uses mockup classes verbatim (where mockup classes exist in `styles-mockup.css`); drops `TONE_CLASS` Record + `bg-X/16 text-X` Tailwind patterns; tone derivation uses `var(--token)` direct refs.

#### US-B2 — Sprint 57.19 carryover behavior preserved
**As a dev** running the page with `?session_id=<uuid>` URL param,
**I want** the live backend `useStateSnapshot` call + carryover banner to continue working,
**so that** Sprint 57.19 US-B3 behavior is preserved.

**Acceptance**: `useStateSnapshot(session_id)` hook call preserved; carryover banner copy preserved; only CSS layer changes.

### Cross-domain

#### US-C1 — Vitest baseline preserved
**As a dev** running `npm run test`,
**I want** all Vitest specs to pass against both domain edits,
**so that** test contract is preserved.

**Acceptance**: `npm run test -- --run` → 456 passing or +N for new specs (loop-debug fixture demo / state-inspector class selector updates).

#### US-C2 — 22-route sweep clean
**As a maintainer**,
**I want** the 22-route sweep to show 0 catastrophic / 0 structural regression on the 20 untouched routes,
**so that** the batched 2-domain sprint doesn't accidentally break other routes.

**Acceptance**: 22-route sweep before/after diff: 19+ IDENTICAL + ≤3 CHANGED (loop-debug expected major change; state-inspector expected major change; chat-v2 inline LoopVisualizer mount preserved within ε).

---

## 3. Technical Specifications

### 3.1 Domain A: Fixture file shape

NEW file: `frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts`

Hand-craft 24 events in production `LoopEvent` discriminated union shape (NOT mockup's flat `{turn, type, text, tone, at}`). Map mockup `LoopEvents` L5-31 semantics:

```ts
// example (agent finalizes per LoopEvent union schema)
import type { LoopEvent } from "@/features/chat_v2/types";

export const DEMO_LOOP_EVENTS: LoopEvent[] = [
  { type: "loop_start", data: { session_id: "sess_4tk2p_demo", ...} } as LoopEvent,
  { type: "turn_start", data: { turn_num: 1 } } as LoopEvent,
  { type: "llm_request", data: { model: "gpt-4o", tokens_in: 1240 } } as LoopEvent,
  { type: "llm_response", data: { tool_calls: [{...}], thinking: "User flagged P1..." } } as LoopEvent,
  { type: "tool_call_request", data: { tool_name: "incidents.list" } } as LoopEvent,
  { type: "approval_requested", data: { risk_level: "low" } } as LoopEvent,  // hitl.policy_check
  { type: "tool_call_result", data: { tool_name: "incidents.list", duration_ms: 82, is_error: false } } as LoopEvent,
  { type: "verification_passed", data: { verifier: "claim_evidence", verifier_type: "auto", score: 0.92 } } as LoopEvent,
  // ... 24 total
];
```

Agent uses production `LoopEvent` union in `frontend/src/features/chat_v2/types.ts` for type validation. Mockup `LoopEvents` 24 entries roughly map to ~16-22 typed production events (some mockup entries like `thinking.start`/`thinking.delta`/`thinking.end` collapse into `llm_request` + `llm_response` thinking field).

### 3.2 Domain A: Playback state machine

Inside `LoopVisualizer` (or extracted `LoopPlaybackHeader` component):

```tsx
const [cursor, setCursor] = useState(events.length); // start at "live" end
const [playing, setPlaying] = useState(false);
const [speed, setSpeed] = useState(8); // 1 | 4 | 8 | 16

useEffect(() => {
  if (!playing) return;
  const id = setInterval(() => {
    setCursor(c => {
      if (c >= events.length) { setPlaying(false); return c; }
      return c + 1;
    });
  }, 1000 / speed);
  return () => clearInterval(id);
}, [playing, speed, events.length]);

const visibleEvents = events.slice(0, cursor);
```

Pure UI state — no backend. Works on either fixture or rawEvents.

### 3.3 Domain A: Filter state

```tsx
type FilterCategory = "thinking" | "tool" | "memory" | "hitl" | "verification" | "subagent";
const [filter, setFilter] = useState<Record<FilterCategory, boolean>>({
  thinking: true, tool: true, memory: true, hitl: true, verification: true, subagent: true,
});

// classify event type to category (similar to eventTone() mapping)
function eventCategory(ev: LoopEvent): FilterCategory | null {
  if (ev.type === "llm_request" || ev.type === "llm_response") return "thinking";
  if (ev.type === "tool_call_request" || ev.type === "tool_call_result") return "tool";
  // memory events not yet in LoopEvent union → returns null (always visible)
  if (ev.type === "approval_requested" || ev.type === "approval_received" || ev.type === "guardrail_triggered") return "hitl";
  if (ev.type === "verification_passed" || ev.type === "verification_failed") return "verification";
  // subagent events not yet in LoopEvent union → returns null
  return null;
}

const filteredEvents = visibleEvents.filter(ev => {
  const cat = eventCategory(ev);
  return cat === null || filter[cat];
});
```

### 3.4 Domain A: LoopInspector right pane

Renders selected event detail per mockup L214-263:

```tsx
function LoopInspector({ event, allEvents }: { event: LoopEvent | undefined, allEvents: LoopEvent[] }) {
  if (!event) return <div className="loop-inspector"><EmptyInspectorPlaceholder /></div>;

  return (
    <div className="loop-inspector">
      <div className="event-header">
        <Icon name="dot" tone={eventTone(event)} />
        <span className="mono">{event.type}</span>
        <div className="mono subtle">{eventSummary(event)}</div>
      </div>
      <Section title="Context">
        <KvRow k="ts" v={event.timestamp ?? "2026-05-24 demo"} mono />
        <KvRow k="turn" v={currentTurnNum(allEvents, event)} mono />
        <KvRow k="audit_id" v={event.audit_id ?? "demo.a8f3"} mono />
        ...
      </Section>
      {event.type === "approval_requested" && (
        <Section title="HITL Policy">
          <KvRow k="tool" v={...} />
          ...
        </Section>
      )}
      <Section title="Raw payload">
        <pre>{JSON.stringify({ type: event.type, data: event.data }, null, 2)}</pre>
      </Section>
    </div>
  );
}
```

### 3.5 Domain B: StateInspectorPage CSS swap

Replace Tailwind utility patterns in `StateInspectorPage.tsx`:

| Current (Sprint 57.19 vintage) | Replace with (mockup verbatim) |
|--------------------------------|--------------------------------|
| `TONE_CLASS: Record<Tone, string>` Record | Drop; use direct `style={{ background: 'var(--X)' }}` per Sprint 57.36 `eventTone()` precedent |
| `bg-success/16 text-success` | `style={{ background: 'oklch(from var(--success) l c h / 0.16)', color: 'var(--success)' }}` (verbatim mockup token-vocabulary pattern; may bump HEX_OKLCH_BASELINE) |
| `grid-cols-[320px_1fr]` Tailwind grid | Mockup class `.version-grid` or inline grid template per mockup verbatim |
| `bg-muted text-muted-foreground` shadcn token | `var(--bg-2)` / `var(--fg-muted)` |
| Lucide icons (`Clock` / `Download` etc.) | Keep or swap to mockup `<Icon name="..." />` pattern per mockup `Icon` component usage |

Agent decides extent of icon swap based on cost-benefit. Lucide icons may stay if no mockup-class equivalent.

### 3.6 Inline mode (chat-v2 cascade) preservation (Domain A)

`mode="inline"` in chat-v2 mount MUST continue to:
- Not wrap in `.loop-canvas` 2-col
- Not show banner
- Not show playback strip / filter / inspector pane
- Continue compact `.loop-track` with last-5-turn collapsed-count UX

Branch in JSX based on `mode` prop (same pattern as Sprint 57.36).

---

## 4. File Change List

**NEW** (1-4 files; agent decides extraction extent):
- `frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts` (NEW, ~50-80 lines, 14-22 typed events)
- Optional: `frontend/src/features/orchestrator-loop/_components/LoopPlaybackHeader.tsx` (extracted if LoopVisualizer.tsx exceeds ~500 lines)
- Optional: `frontend/src/features/orchestrator-loop/_components/LoopInspector.tsx` (same threshold)
- Optional: `frontend/src/features/orchestrator-loop/_components/KvRow.tsx` (same threshold)

**Modified** (2 production files):
- `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` (~+200-300 lines for fixture loader + playback state + filter state + inspector render + corrected AP-2 banner; some lines split to extracted components)
- `frontend/src/pages/state-inspector/StateInspectorPage.tsx` (~+150/-100 lines for verbatim class swap; behavior preserved)

**Modified** (1 spec file likely):
- `frontend/tests/unit/orchestrator-loop/LoopVisualizer.test.tsx` (update for new fixture-mode behavior + new playback / filter / inspector specs if added)
- `frontend/tests/**/StateInspector*.test.tsx` (if exists; verify Day 0 Prong 1 with extended `src/**` AND `tests/**` glob per Sprint 57.36 D-DAY1-1 lesson)

**Updated** (1 CI guard config):
- `frontend/scripts/check-mockup-fidelity.mjs` — `HEX_OKLCH_BASELINE` re-evaluate (Domain B verbatim swap may introduce new `oklch(from var(--X) l c h / X)` patterns)

**Re-pointed** (1 OUT_DIR):
- `frontend/scripts/route-sweep.mjs` — OUT_DIR re-pointed to `sprint-57-37-loop-debug-state-inspector`

---

## 5. Acceptance Criteria

| # | Criterion | Verify | Domain |
|---|-----------|--------|--------|
| AC-1 | `/loop-debug` standalone with no live events renders 24 demo events from fixture | Visual at `localhost:3007/loop-debug`; matches mockup `localhost:8080/#loop-debug` | A |
| AC-2 | `/loop-debug` standalone with live `rawEvents` renders real events (fixture not used) | Visual + manual chat-v2 session test | A |
| AC-3 | Playback strip operates (play/pause/scrubber/speed pills change cursor) | Manual interaction at /loop-debug | A |
| AC-4 | Filter pills toggle category visibility | Manual interaction; click thinking pill → llm events hide | A |
| AC-5 | Inspector right pane shows selected-event detail | Click event row → inspector populates | A |
| AC-6 | AP-2 BackendGapBanner copy honest (DEMO DATA + backend Phase 58+) | Read banner text in /loop-debug standalone | A |
| AC-7 | Inline mode (chat-v2) unchanged (no canvas / banner / playback / inspector) | 22-route sweep `/chat-v2` diff ≤ ε | A |
| AC-8 | `/state-inspector` uses mockup verbatim classes; zero Tailwind tone-utility patterns | DOM inspect + `check-mockup-fidelity.mjs` Guard 2 baseline | B |
| AC-9 | `/state-inspector` `?session_id=...` live backend behavior preserved | Manual test with URL param | B |
| AC-10 | Vitest baseline preserved or +N | `npm run test -- --run` exit 0 ≥ 456 | Both |
| AC-11 | 22-route sweep: 0 catastrophic / 0 structural regression on untouched 20 routes | Before/after PowerShell SHA256 diff | Both |
| AC-12 | `check-mockup-fidelity.mjs` exit 0 | npm run check:mockup-fidelity | Both |

---

## 6. Deliverables

- [ ] sprint-57-37-plan.md (this file)
- [ ] sprint-57-37-checklist.md
- [ ] frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts (NEW)
- [ ] frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx (modified; or split across extracted components)
- [ ] frontend/src/pages/state-inspector/StateInspectorPage.tsx (modified)
- [ ] frontend/scripts/route-sweep.mjs (OUT_DIR re-pointed)
- [ ] frontend/scripts/check-mockup-fidelity.mjs (HEX_OKLCH_BASELINE updated)
- [ ] Vitest specs updated for both domains
- [ ] 22-route before sweep + after sweep + diff report
- [ ] docs/03-implementation/agent-harness-execution/phase-57/sprint-57-37/progress.md
- [ ] docs/03-implementation/agent-harness-execution/phase-57/sprint-57-37/retrospective.md
- [ ] memory/project_phase57_37_loop_debug_fixture_state_inspector.md + 1-line MEMORY.md pointer
- [ ] Calibration matrix: 2 data points (Domain A → `frontend-mockup-strict-rebuild` 5th app; Domain B → `frontend-verbatim-css-repoint` 8th app)
- [ ] next-phase-candidates.md updated
- [ ] CLAUDE.md Current Sprint + Last Updated
- [ ] PR opened against main

---

## 7. Risks & Mitigations

| # | Risk | Likelihood | Mitigation |
|---|------|------------|------------|
| R-1 | Production `LoopEvent` union doesn't have semantic equivalents for all 24 mockup event types (e.g. mockup `subagent.spawn` / `memory.read` / `loop.iter_start`) | High | Map best-effort to closest production type + fill gaps with `eventSummary()` text; agent uses `LoopEvent` types from `chat_v2/types.ts`; document mapping in fixture file header |
| R-2 | Playback `useEffect` interval cleanup may leak across remounts | Low | Standard React pattern with `return () => clearInterval(id)`; agent reviews Day 1 |
| R-3 | Inspector pane KvRow rendering for HITL events needs `audit_id` / `tenant_id` / `span_id` which fixture must supply | Medium | Fixture events include synthetic `audit_id` / `span_id` / `tenant_id` strings (clearly demo-prefixed like `demo.a8f3` / `demo_t01h9a2`) |
| R-4 | StateInspector mockup may use classes NOT in `styles-mockup.css` (verify Day 0 Prong 1) | Medium | Day 0 Prong 1: grep `styles-mockup.css` for any `.version-X` / `.diff-X` / similar StateInspector-specific classes mockup uses |
| R-5 | check-mockup-fidelity HEX_OKLCH_BASELINE may rise significantly (both domains add inline `oklch(from var(--X) l c h / X)` patterns) | High | Bump baseline with rationale per Sprint 57.30/57.35 precedent; documented in MHist entry |
| R-6 | Dual-mount cascade (inline mode regression) — bigger Domain A change makes risk higher | Medium | Day 1 agent explicit `mode="inline"` branch test; Day 3 sweep `/chat-v2` diff |
| R-7 | Sprint 57.36 D-DAY1-1 lesson (test glob coverage) — extend Prong 1 to BOTH `src/**` AND `tests/**` | Low | Codified in checklist §0.2 Prong 1 |
| R-8 | 2-domain batched sprint may have scope creep — Domain A is significantly larger than Sprint 57.36 single-domain | Medium | Plan §4 explicit file change list + agent task brief enforces scope; Day 4 retro evaluates whether batched approach worth it vs splitting |
| R-9 | Recurring Risk Class A — paths-filter CI infra | Low | Touch `.github/workflows/backend-ci.yml` header comment if needed |

---

## 8. Workload

**Bottom-up est** ~9.5-10 hr → **calibrated commit** ~5.5 hr (multiplier 0.58 HYBRID)

### Day-by-day allocation

| Day | Theme | Bottom-up | Calibrated | Notes |
|-----|-------|-----------|------------|-------|
| Day 0 | Plan + Checklist + 三-prong (2 domains) + before baseline | ~1 hr | ~0.85 hr | larger than 57.36 due to 2-domain mapping |
| Day 1 | Domain A — fixture file + playback state + filter state | ~2 hr | ~1.2 hr | Agent-delegated |
| Day 2 | Domain A — inspector pane + AP-2 banner update + Vitest | ~2-2.5 hr | ~1.4 hr | Agent-delegated |
| Day 3 | Domain B — StateInspectorPage verbatim CSS swap + Vitest | ~2-2.5 hr | ~1.2 hr | Agent-delegated |
| Day 3.5 | 22-route sweep + 2-domain fidelity verify | ~0.5 hr | ~0.25 hr | Manual sweep |
| Day 4 | Closeout (2-class matrix + retro + memory + push + PR) | ~1.5 hr | ~1.2 hr | Self |
| **Total** | | **~9.5-10 hr** | **~5.5 hr** | |

---

## 9. Dependencies

**Hard dependencies (must be true before Day 1)**:
- ✅ Sprint 57.28 verbatim-CSS foundation (Layer 2 `styles-mockup.css` byte-identical)
- ✅ Sprint 57.30 `/chat-v2` Phase-2 (inline LoopVisualizer mount preserved)
- ✅ Sprint 57.36 Day 1-2 (LoopVisualizer mockup classes + eventTone adapter — Domain A extends these)
- ✅ Sprint 57.19 US-B3 (`/state-inspector` ship state — Domain B re-points this)
- ✅ `BackendGapBanner` component + `useStateSnapshot` hook (both Sprint 57.19+/57.24+ ships)

**Soft dependencies (nice but not blocking)**:
- Sprint 57.36 AP-2 banner precedent for honest Phase 58+ disclosure
- Sprint 57.35 D-DAY1-1 lesson — Prong 1 glob should cover `tests/**`

**Unblocks (downstream)**:
- Sprint 57.38+ class split proposal (`-simple` vs `-with-ap2-or-dual-mount`) if Domain B lands in band
- Sprint 57.39+ remaining Phase-2 routes (/governance / /admin-tenants / /memory etc.)
- Phase 58+ SSE event persistence backend (will remove DEMO DATA banner + connect playback to real persisted events)

---

**End of plan**
