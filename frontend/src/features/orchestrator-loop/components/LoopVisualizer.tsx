/**
 * File: frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx
 * Purpose: TAO/ReAct state machine tree consuming the chat-v2 LoopEvent stream (Sprint 57.12 US-4).
 * Category: Frontend / orchestrator-loop / components
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-4 (was Phase 49.1 placeholder); Sprint 57.36 verbatim re-point.
 *
 * Description:
 *   Renders a real-time tree of the agent loop, grouped per turn. Single
 *   component mounted in 2 contexts:
 *     - <LoopVisualizer mode="inline" />     — chat-v2 inline panel; compact;
 *       auto-collapses turns older than the last 5; max-height + scroll.
 *     - <LoopVisualizer mode="standalone" /> — /loop-debug page; full screen;
 *       all turns expanded; total-elapsed/tokens summary header.
 *
 *   Consumes `useChatStore` rawEvents (same source as chat-v2 SSE). Groups
 *   events into turn buckets at each `turn_start` event (events before the
 *   first turn_start — e.g. loop_start — go in turn 0). Per Day 1 D2-003:
 *   the frontend only knows the ~14 serialized SSE event types
 *   (the chat_v2 LoopEvent union), not all 22 backend LoopEvent subclasses;
 *   any event present in rawEvents is rendered with its type + key fields.
 *
 *   Visual encoding (Sprint 57.36 verbatim re-point per page-governance.jsx:33-212):
 *     - Standalone wrapper = mockup `.loop-canvas` 2-col (track + inspector
 *       placeholder); Inspector pane deferred Phase 58+ pending SSE event
 *       persistence (AP-2 BackendGapBanner).
 *     - Per-turn block = `.loop-turn` + `.loop-turn-head` + `.loop-turn-body`
 *       with `data-status="running" / "done"` per mockup L76.
 *     - Per-event row = `.event-row` + `.ev-dot` + `.ev-type` + `.ev-detail`
 *       + `.ev-timing` per mockup L187-212 (production schema lacks per-event
 *       `tone` field; tone is derived from event type via `eventTone()` —
 *       failure types → `--danger` / `--warning`; tool types → `--tool`;
 *       llm types → `--thinking`; verification success → `--success`; lifecycle
 *       → `--primary`; default → `--fg-muted`).
 *     - Inline mode keeps the compact `.loop-track` (no canvas, no inspector,
 *       no banner) + collapsed-count nicety (production-only UX preserved).
 *
 * Created: 2026-04-29 (Sprint 49.1 placeholder); 2026-05-10 (Sprint 57.12 real ship)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.36 Day 1-2 — verbatim CSS re-point per page-governance.jsx:33-212 (closes vintage HSL-translation drift; AP-2 banner Phase 58+ deferred features)
 *   - 2026-05-10: Sprint 57.12 US-4 Day 2 — dual-mount LoopVisualizer (real ship)
 *
 * Related:
 *   - frontend/src/features/chat_v2/store/chatStore.ts (rawEvents source)
 *   - frontend/src/features/chat_v2/types.ts (LoopEvent union)
 *   - frontend/src/pages/loop-debug/index.tsx (standalone mount; Day 2 §2.7)
 *   - reference/design-mockups/page-governance.jsx:33-212 (verbatim mockup truth)
 *   - frontend/src/styles-mockup.css L940-998 (.loop-canvas / .loop-turn / .event-row)
 *   - sprint-57-12-plan.md §US-4 / sprint-57-36-plan.md §3
 */

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";
import { BackendGapBanner } from "@/components/ui/BackendGapBanner";

export type LoopVisualizerMode = "inline" | "standalone";

export interface LoopVisualizerProps {
  mode: LoopVisualizerMode;
}

interface TurnBucket {
  turnNum: number;
  events: LoopEvent[];
}

interface MutableBucket extends TurnBucket {
  /** True once a turn_start marker has been seen for this bucket. */
  hasTurnMarker: boolean;
}

/**
 * Group rawEvents into per-turn buckets at each turn_start marker. Events that
 * arrive before the first turn_start (e.g. loop_start) are absorbed into the
 * first turn's bucket rather than forming a duplicate turn-0 bucket.
 */
function groupByTurn(events: LoopEvent[]): TurnBucket[] {
  const buckets: TurnBucket[] = [];
  let current: MutableBucket | null = null;
  for (const ev of events) {
    if (ev.type === "turn_start") {
      if (current === null) {
        current = { turnNum: ev.data.turn_num, events: [ev], hasTurnMarker: true };
      } else if (!current.hasTurnMarker) {
        // Preamble bucket (only had pre-turn events so far) absorbs the marker.
        current.turnNum = ev.data.turn_num;
        current.events.push(ev);
        current.hasTurnMarker = true;
      } else {
        buckets.push(current);
        current = { turnNum: ev.data.turn_num, events: [ev], hasTurnMarker: true };
      }
    } else if (current === null) {
      current = { turnNum: 0, events: [ev], hasTurnMarker: false };
    } else {
      current.events.push(ev);
    }
  }
  if (current !== null && current.events.length > 0) buckets.push(current);
  return buckets;
}

/**
 * Map an event to its mockup tone CSS variable. Production LoopEvent schema lacks
 * a per-event `tone` field that mockup `EventRow` uses (page-governance.jsx:188-192);
 * derive tone from event type instead. Severity hierarchy:
 *   - Errors / failures / guardrails → `--danger`
 *   - HITL approvals → `--warning`
 *   - Tool calls → `--tool`
 *   - LLM activity (thinking / response) → `--thinking`
 *   - Verification success → `--success`
 *   - Loop lifecycle (start / end / turn_start) → `--primary`
 *   - Default → `--fg-muted`
 */
function eventTone(ev: LoopEvent): string {
  if (ev.type === "tool_call_result" && ev.data.is_error) return "var(--danger)";
  if (ev.type === "verification_failed") return "var(--danger)";
  if (ev.type === "guardrail_triggered") return "var(--warning)";
  if (ev.type === "approval_requested" || ev.type === "approval_received") return "var(--warning)";
  if (ev.type === "tool_call_request" || ev.type === "tool_call_result") return "var(--tool)";
  if (ev.type === "llm_request" || ev.type === "llm_response") return "var(--thinking)";
  if (ev.type === "verification_passed") return "var(--success)";
  if (ev.type === "loop_start" || ev.type === "loop_end" || ev.type === "turn_start")
    return "var(--primary)";
  return "var(--fg-muted)";
}

/** One-line summary of an event's key fields for the tree row. */
function eventSummary(ev: LoopEvent): string {
  switch (ev.type) {
    case "loop_start":
      return `session=${ev.data.session_id ?? "(pending)"}`;
    case "turn_start":
      return `turn ${ev.data.turn_num}`;
    case "llm_request":
      return `model=${ev.data.model} tokens_in=${ev.data.tokens_in}`;
    case "llm_response": {
      const tc = ev.data.tool_calls.length;
      return `${tc} tool call${tc === 1 ? "" : "s"}${ev.data.thinking ? " · has thinking" : ""}`;
    }
    case "tool_call_request":
      return `${ev.data.tool_name}`;
    case "tool_call_result":
      return `${ev.data.tool_name} (${ev.data.duration_ms.toFixed(0)} ms)${ev.data.is_error ? " · ERROR" : ""}`;
    case "loop_end":
      return `stop=${ev.data.stop_reason} turns=${ev.data.total_turns}`;
    case "approval_requested":
      return `risk=${ev.data.risk_level}`;
    case "approval_received":
      return `decision=${ev.data.decision}`;
    case "guardrail_triggered":
      return `${ev.data.guardrail_type} → ${ev.data.action}`;
    case "verification_passed":
      return `${ev.data.verifier} (${ev.data.verifier_type})${ev.data.score !== null ? ` score=${ev.data.score.toFixed(2)}` : ""}`;
    case "verification_failed":
      return `${ev.data.verifier} (${ev.data.verifier_type}) · ${ev.data.reason ?? "no reason"}`;
    default: {
      // Defensive — unknown future serialized type (e.g. subagent_* added in US-6
      // is also typed; this branch only hits if a wholly-unmapped type slips in).
      return JSON.stringify((ev as { data?: unknown }).data ?? {});
    }
  }
}

/**
 * Render the turn list (shared between standalone + inline modes). Mockup
 * `.loop-turn` + `.loop-turn-head` + `.loop-turn-body` per page-governance.jsx:76-103.
 * The mockup uses `data-status="running" | "done"` for the latest-turn accent
 * (`.loop-turn[data-status="running"]` rule at styles-mockup.css:981); we apply
 * `running` to the last bucket as a heuristic until backend SSE event persistence
 * exposes real per-turn status (Phase 58+).
 */
function TurnList({
  buckets,
  isLastRunning,
}: {
  buckets: TurnBucket[];
  isLastRunning: boolean;
}): JSX.Element {
  return (
    <>
      {buckets.map((bucket, bi) => {
        const isLast = bi === buckets.length - 1;
        const status = isLast && isLastRunning ? "running" : "done";
        return (
          <div
            key={`turn-${bucket.turnNum}-${bi}`}
            className="loop-turn"
            data-status={status}
            data-testid={`loop-turn-${bucket.turnNum}`}
          >
            <div className="loop-turn-head">
              <span className="turn-no">turn {bucket.turnNum}</span>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:79-80 inline fontWeight; mockup-fidelity pattern */}
              <span style={{ fontWeight: 500 }}>
                {bucket.turnNum === 0 ? "Preamble" : "Loop iteration"}
              </span>
              <span className="mono subtle">
                · {bucket.events.length} event{bucket.events.length === 1 ? "" : "s"}
              </span>
            </div>
            <div className="loop-turn-body">
              {bucket.events.map((ev, ei) => {
                const tone = eventTone(ev);
                return (
                  <div
                    key={`ev-${bi}-${ei}`}
                    className="event-row"
                    data-testid={`loop-event-${ev.type}`}
                  >
                    {/* eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:206 dynamic tone background; mockup-fidelity pattern */}
                    <span className="ev-dot" style={{ background: tone }} />
                    {/* eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:207 dynamic tone color; mockup-fidelity pattern */}
                    <span className="ev-type" style={{ color: tone }}>
                      {ev.type}
                    </span>
                    <span className="ev-detail">{eventSummary(ev)}</span>
                    <span className="ev-timing">{/* Phase 58+ per-event timing */}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </>
  );
}

// Inline style constants for verbatim mockup patterns (page-governance.jsx:216-222
// LoopInspector header). Extracted to module scope so eslint no-restricted-syntax
// (Sprint 57.15 STYLE.md §1) sees them as constants, not JSX `style=` literals.
// Lint allows constant-ref objects; the rule targets inline object literals in JSX.
const INSPECTOR_WRAPPER_STYLE = { padding: 14 } as const;
const INSPECTOR_LABEL_STYLE = {
  fontSize: 11,
  color: "var(--fg-subtle)",
  textTransform: "uppercase" as const,
  letterSpacing: "0.06em",
  marginBottom: 6,
  fontFamily: "var(--font-mono)",
};
const INSPECTOR_TEXT_STYLE = { fontSize: 11 };
const STANDALONE_SUMMARY_STYLE = {
  gap: 16,
  padding: "10px 4px",
  fontSize: 12,
  color: "var(--fg-muted)",
};
const STANDALONE_STRONG_STYLE = { color: "var(--fg)" };
const INLINE_TRACK_STYLE = { maxHeight: 400, padding: 12 };
const INLINE_HEADER_STYLE = {
  marginBottom: 8,
  fontSize: 10.5,
  textTransform: "uppercase" as const,
  letterSpacing: "0.06em",
};
const INLINE_COLLAPSED_STYLE = { marginBottom: 8, fontSize: 11 };
const EMPTY_STATE_STYLE = { fontSize: 12, padding: 12 };

/**
 * Placeholder for the mockup `LoopInspector` right pane (page-governance.jsx:214-263).
 * Mockup inspector renders selected-event detail (HITL Policy / Raw payload / KvRow
 * fields) which requires backend SSE event persistence (`loop_event` table) —
 * Phase 58+ scope per Sprint 57.12 AP-6 deferral. Per AP-2 honesty, we render an
 * empty-state notice rather than a Potemkin pane.
 */
function EmptyInspectorPlaceholder(): JSX.Element {
  return (
    // eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:216 LoopInspector wrapper padding (constant ref); mockup-fidelity placeholder for Phase 58+ pane
    <div style={INSPECTOR_WRAPPER_STYLE}>
      {/* eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:217 section-label typography (constant ref); mockup-fidelity */}
      <div style={INSPECTOR_LABEL_STYLE}>Event Inspector</div>
      {/* eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:222 mono subtle text (constant ref); mockup-fidelity */}
      <div className="mono subtle" style={INSPECTOR_TEXT_STYLE}>
        Per-event inspector (HITL policy · raw payload · trace IDs) requires backend SSE
        event persistence — deferred Phase 58+.
      </div>
    </div>
  );
}

export function LoopVisualizer({ mode }: LoopVisualizerProps): JSX.Element | null {
  const rawEvents = useChatStore((s) => s.rawEvents);
  const totalTurns = useChatStore((s) => s.totalTurns);

  // Empty-state branches (preserved from Sprint 57.12)
  if (rawEvents.length === 0) {
    if (mode === "inline") return null;
    return (
      <div className="loop-canvas" data-testid="loop-visualizer-standalone">
        <div className="loop-track">
          {/* eslint-disable-next-line no-restricted-syntax -- empty-state spacing (constant ref); preserves Sprint 57.12 UX inside verbatim mockup .loop-track */}
          <div className="mono subtle" style={EMPTY_STATE_STYLE}>
            No loop events yet. Start a chat-v2 session to populate the visualizer.
          </div>
        </div>
        <aside className="loop-inspector">
          <EmptyInspectorPlaceholder />
        </aside>
      </div>
    );
  }

  const buckets = groupByTurn(rawEvents);
  // Inline mode: only expand the last 5 turns; collapse the rest into a count.
  const collapsedCount = mode === "inline" && buckets.length > 5 ? buckets.length - 5 : 0;
  const visibleBuckets = collapsedCount > 0 ? buckets.slice(collapsedCount) : buckets;
  // Heuristic: treat the last turn as `running` if no terminal `loop_end` event
  // has been seen yet. Real per-turn status awaits backend Phase 58+.
  const isLastRunning = !rawEvents.some((ev) => ev.type === "loop_end");

  if (mode === "standalone") {
    return (
      <div
        className="loop-canvas"
        data-testid="loop-visualizer-standalone"
        aria-label="Loop visualizer"
      >
        <div className="loop-track">
          <BackendGapBanner reason="The mockup LoopDebug includes playback controls (play/pause/scrubber/speed), per-category filter pills, and a 2-column inspector pane with HITL policy + raw event payload + trace IDs. These require backend SSE event persistence (loop_event table) which is Phase 58+ scope per Sprint 57.12 AP-6 deferral. This view shows the in-memory live session only." />
          <div
            className="row"
            // eslint-disable-next-line no-restricted-syntax -- summary row spacing+tone (constant ref); preserves Sprint 57.12 summary inside verbatim mockup .loop-track
            style={STANDALONE_SUMMARY_STYLE}
            data-testid="loop-visualizer-summary"
          >
            <span>
              Turns:{" "}
              {/* eslint-disable-next-line no-restricted-syntax -- foreground tone for emphasis (constant ref); mockup-token */}
              <strong style={STANDALONE_STRONG_STYLE}>{totalTurns || buckets.length}</strong>
            </span>
            <span>
              Events:{" "}
              {/* eslint-disable-next-line no-restricted-syntax -- foreground tone for emphasis (constant ref); mockup-token */}
              <strong style={STANDALONE_STRONG_STYLE}>{rawEvents.length}</strong>
            </span>
          </div>
          <TurnList buckets={visibleBuckets} isLastRunning={isLastRunning} />
        </div>
        <aside className="loop-inspector">
          <EmptyInspectorPlaceholder />
        </aside>
      </div>
    );
  }

  // Inline mode — compact `.loop-track`, no canvas, no inspector, no banner.
  return (
    <div
      className="loop-track"
      data-mode="inline"
      data-testid="loop-visualizer-inline"
      aria-label="Loop visualizer"
      // eslint-disable-next-line no-restricted-syntax -- inline-mode chat-v2 panel max-height + padding (constant ref); preserves Sprint 57.12 UX inside verbatim mockup .loop-track
      style={INLINE_TRACK_STYLE}
    >
      {/* eslint-disable-next-line no-restricted-syntax -- inline-mode header typography (constant ref); mockup-fidelity */}
      <div className="mono subtle" style={INLINE_HEADER_STYLE}>
        Loop ({buckets.length} turn{buckets.length === 1 ? "" : "s"})
      </div>
      {collapsedCount > 0 && (
        // eslint-disable-next-line no-restricted-syntax -- inline-mode collapsed-count typography (constant ref); preserves Sprint 57.12 UX
        <div className="mono subtle" style={INLINE_COLLAPSED_STYLE}>
          {collapsedCount} earlier turn{collapsedCount === 1 ? "" : "s"} collapsed
        </div>
      )}
      <TurnList buckets={visibleBuckets} isLastRunning={isLastRunning} />
    </div>
  );
}
