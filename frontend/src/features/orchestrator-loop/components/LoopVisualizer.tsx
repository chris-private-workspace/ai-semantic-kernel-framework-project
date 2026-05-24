/**
 * File: frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx
 * Purpose: TAO/ReAct state machine tree consuming the chat-v2 LoopEvent stream (Sprint 57.12 US-4).
 * Category: Frontend / orchestrator-loop / components
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-4; Sprint 57.36 verbatim re-point; Sprint 57.37 Day 1-2 fixture + playback + filter + inspector.
 *
 * Description:
 *   Renders a real-time tree of the agent loop, grouped per turn. Single
 *   component mounted in 2 contexts:
 *     - <LoopVisualizer mode="inline" />     — chat-v2 inline panel; compact;
 *       auto-collapses turns older than the last 5; max-height + scroll.
 *     - <LoopVisualizer mode="standalone" /> — /loop-debug page; full screen;
 *       all turns expanded; total-elapsed/tokens summary header; playback
 *       strip + filter pills + 2-column inspector pane.
 *
 *   Consumes `useChatStore` rawEvents (same source as chat-v2 SSE). When
 *   standalone mode has zero live events, a typed 18-event DEMO_LOOP_EVENTS
 *   fixture is rendered instead so the page is never empty (Sprint 57.37
 *   Day 1 US-A1 — closes Sprint 57.36 §Frontend Mockup-Fidelity Hard
 *   Constraint gap). Inline mode preserves the "render null when empty"
 *   contract (chat-v2 panel should not be populated by demo data).
 *
 *   Visual encoding (Sprint 57.36/57.37 verbatim re-point per page-governance.jsx:5-270):
 *     - Standalone wrapper = mockup `.loop-canvas` 2-col (left track + right
 *       `.loop-inspector` pane with selected-event detail per L214-263).
 *     - Per-turn block = `.loop-turn` + `.loop-turn-head` + `.loop-turn-body`
 *       with `data-status="running" / "done"` per mockup L76.
 *     - Per-event row = `.event-row` + `.ev-dot` + `.ev-type` + `.ev-detail`
 *       + `.ev-timing` per mockup L187-212; tone derived via `eventTone()`.
 *     - Playback strip per mockup L154-184: Pause/Resume + scrubber input +
 *       speed pills 1×/4×/8×/16×; operates on either fixture or live rawEvents.
 *     - Filter pills per mockup L132-150: 6 categories (thinking/tool/memory/
 *       hitl/verification/subagent) toggle via opacity + filter Record state.
 *     - LoopInspector right pane per mockup L214-263: selected-event detail
 *       (KvRow rows for ts / turn / audit_id / span_id / tenant / session_id /
 *       agent + HITL Policy section conditional + Raw payload JSON).
 *     - AP-2 BackendGapBanner now honestly discloses "DEMO DATA" only when
 *       fixture is active; otherwise discloses SSE event persistence Phase 58+.
 *     - Inline mode keeps the compact `.loop-track` (no canvas, no banner,
 *       no playback, no filter, no inspector) + collapsed-count nicety.
 *
 * Created: 2026-04-29 (Sprint 49.1 placeholder); 2026-05-10 (Sprint 57.12 real ship)
 * Last Modified: 2026-05-24
 *
 * Modification History (newest-first):
 *   - 2026-05-24: Sprint 57.37 Day 1-2 — fixture demo events + playback + filter + LoopInspector pane (closes Sprint 57.36 mockup-fidelity gap)
 *   - 2026-05-24: Sprint 57.36 Day 1-2 — verbatim CSS re-point per page-governance.jsx:33-212 (closes vintage HSL-translation drift; AP-2 banner Phase 58+ deferred features)
 *   - 2026-05-10: Sprint 57.12 US-4 Day 2 — dual-mount LoopVisualizer (real ship)
 *
 * Related:
 *   - frontend/src/features/chat_v2/store/chatStore.ts (rawEvents source)
 *   - frontend/src/features/chat_v2/types.ts (LoopEvent union)
 *   - frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts (Sprint 57.37 fixture)
 *   - frontend/src/pages/loop-debug/index.tsx (standalone mount)
 *   - reference/design-mockups/page-governance.jsx:5-270 (verbatim mockup truth)
 *   - frontend/src/styles-mockup.css L940-998 (.loop-canvas / .loop-turn / .event-row)
 *   - sprint-57-12-plan.md §US-4 / sprint-57-36-plan.md §3 / sprint-57-37-plan.md §3.1-3.4
 */

import { useEffect, useMemo, useState } from "react";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";
import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { DEMO_LOOP_EVENTS } from "../_fixtures/demoLoopEvents";

export type LoopVisualizerMode = "inline" | "standalone";

export interface LoopVisualizerProps {
  mode: LoopVisualizerMode;
}

interface TurnBucket {
  turnNum: number;
  events: LoopEvent[];
  /** Index into the source event array of the first event in this bucket; lets
   *  the row click handler resolve back to a stable global index for selection. */
  startIndex: number;
}

interface MutableBucket extends TurnBucket {
  /** True once a turn_start marker has been seen for this bucket. */
  hasTurnMarker: boolean;
}

/**
 * Group events into per-turn buckets at each turn_start marker. Events that
 * arrive before the first turn_start (e.g. loop_start) are absorbed into the
 * first turn's bucket rather than forming a duplicate turn-0 bucket.
 */
function groupByTurn(events: LoopEvent[]): TurnBucket[] {
  const buckets: TurnBucket[] = [];
  let current: MutableBucket | null = null;
  for (let i = 0; i < events.length; i++) {
    const ev = events[i];
    if (ev.type === "turn_start") {
      if (current === null) {
        current = {
          turnNum: ev.data.turn_num,
          events: [ev],
          startIndex: i,
          hasTurnMarker: true,
        };
      } else if (!current.hasTurnMarker) {
        current.turnNum = ev.data.turn_num;
        current.events.push(ev);
        current.hasTurnMarker = true;
      } else {
        buckets.push(current);
        current = {
          turnNum: ev.data.turn_num,
          events: [ev],
          startIndex: i,
          hasTurnMarker: true,
        };
      }
    } else if (current === null) {
      current = { turnNum: 0, events: [ev], startIndex: i, hasTurnMarker: false };
    } else {
      current.events.push(ev);
    }
  }
  if (current !== null && (current as MutableBucket).events.length > 0) {
    buckets.push(current);
  }
  return buckets;
}

/**
 * Map an event to its mockup tone CSS variable. Production LoopEvent schema
 * lacks a per-event `tone` field that mockup `EventRow` uses (page-governance.jsx:188-192);
 * derive tone from event type. Severity hierarchy:
 *   - Errors / failures / guardrails → `--danger`
 *   - HITL approvals → `--warning`
 *   - Tool calls → `--tool`
 *   - LLM activity (thinking / response) → `--thinking`
 *   - Verification success → `--success`
 *   - Subagent events → `--info`
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
  if (ev.type === "subagent_spawned" || ev.type === "subagent_completed") return "var(--info)";
  if (ev.type === "loop_start" || ev.type === "loop_end" || ev.type === "turn_start")
    return "var(--primary)";
  return "var(--fg-muted)";
}

/** Six filter categories the LoopDebugHeader pills control (mockup L132-150). */
type FilterCategory = "thinking" | "tool" | "memory" | "hitl" | "verification" | "subagent";

const FILTER_CATEGORIES: ReadonlyArray<{ key: FilterCategory; color: string }> = [
  { key: "thinking", color: "var(--thinking)" },
  { key: "tool", color: "var(--tool)" },
  { key: "memory", color: "var(--memory)" },
  { key: "hitl", color: "var(--warning)" },
  { key: "verification", color: "var(--success)" },
  { key: "subagent", color: "var(--info)" },
];

/** Classify an event into a filter category. Returns null for events with no
 *  category (loop_start / turn_start / loop_end — always visible). */
function eventCategory(ev: LoopEvent): FilterCategory | null {
  if (ev.type === "llm_request" || ev.type === "llm_response") return "thinking";
  if (ev.type === "tool_call_request" || ev.type === "tool_call_result") return "tool";
  if (ev.type === "approval_requested" || ev.type === "approval_received") return "hitl";
  if (ev.type === "guardrail_triggered") return "hitl";
  if (ev.type === "verification_passed" || ev.type === "verification_failed") return "verification";
  if (ev.type === "subagent_spawned" || ev.type === "subagent_completed") return "subagent";
  // memory category has no LoopEvent type yet (Phase 58+ AD-Memory-Event-Wire-Up)
  return null;
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
    case "subagent_spawned":
      return `mode=${ev.data.mode} parent=${ev.data.parent_session_id ?? "—"}`;
    case "subagent_completed":
      return `${ev.data.summary} · ${ev.data.tokens_used} tokens`;
    default: {
      return JSON.stringify((ev as { data?: unknown }).data ?? {});
    }
  }
}

/** Compute which turn an event belongs to by scanning preceding events for the
 *  most recent turn_start marker. Used by inspector header KvRow. */
function deriveTurnNum(allEvents: LoopEvent[], target: LoopEvent): number {
  const idx = allEvents.indexOf(target);
  if (idx < 0) return 0;
  for (let i = idx; i >= 0; i--) {
    const ev = allEvents[i];
    if (ev.type === "turn_start") return ev.data.turn_num;
  }
  return 0;
}

// === Module-scope constant style refs (eslint no-restricted-syntax compliance) ===
// Inline mockup-fidelity patterns referenced from JSX. Constant-ref objects are
// permitted by the rule; only inline JSX object literals are flagged.

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

const HEADER_COL_STYLE = { marginBottom: 14, gap: 12, padding: "0 4px" };
const HEADER_TITLE_ROW_STYLE = { gap: 10 };
const HEADER_TITLE_STYLE = { fontSize: 18, fontWeight: 600 as const };
const HEADER_SUB_STYLE = {
  fontSize: 12.5,
  color: "var(--fg-muted)",
  marginTop: 4,
  display: "flex",
  gap: 8,
  alignItems: "center" as const,
};
const FILTER_PILLS_ROW_STYLE = { gap: 4 };
const PILL_DOT_STYLE = { width: 6, height: 6, borderRadius: "50%", display: "inline-block" as const };
const PLAYBACK_ROW_STYLE = {
  gap: 8,
  padding: "8px 12px",
  background: "var(--bg-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
};
const PLAYBACK_CURSOR_LABEL_STYLE = {
  fontSize: 11,
  minWidth: 70,
};
const PLAYBACK_CURSOR_LABEL_RIGHT_STYLE = {
  fontSize: 11,
  minWidth: 70,
  textAlign: "right" as const,
};
const SCRUBBER_FLEX_STYLE = {
  display: "flex",
  alignItems: "center" as const,
  gap: 10,
  minWidth: 0,
  flex: 1,
};
const SCRUBBER_INPUT_STYLE = { flex: 1, accentColor: "var(--primary)" };

const INSPECTOR_HEAD_STYLE = { padding: 14, borderBottom: "1px solid var(--border)" };
const INSPECTOR_LABEL_STYLE = {
  fontSize: 11,
  color: "var(--fg-subtle)",
  textTransform: "uppercase" as const,
  letterSpacing: "0.06em",
  marginBottom: 6,
  fontFamily: "var(--font-mono)",
};
const INSPECTOR_HEAD_ROW_STYLE = { gap: 8, marginBottom: 4 };
const INSPECTOR_HEAD_DOT_STYLE = { width: 8, height: 8, borderRadius: "50%" as const };
const INSPECTOR_HEAD_TYPE_STYLE = { fontSize: 13, fontWeight: 600 as const };
const INSPECTOR_HEAD_DETAIL_STYLE = { fontSize: 11, color: "var(--fg-muted)" };
const INSPECTOR_BODY_STYLE = { padding: 14 };
const INSPECTOR_KV_COL_STYLE = { gap: 7, fontSize: 12 };
const INSPECTOR_PRE_STYLE = {
  margin: 0,
  padding: 10,
  background: "var(--bg-2)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  fontFamily: "var(--font-mono)",
  fontSize: 10.5,
  lineHeight: 1.55,
  color: "var(--fg-muted)",
  overflowX: "auto" as const,
};

const REPLAY_FOOTER_STYLE = {
  padding: "10px 12px",
  display: "flex",
  alignItems: "center" as const,
  gap: 8,
  color: "var(--fg-subtle)",
  fontSize: 11,
  fontFamily: "var(--font-mono)",
};
const REPLAY_DOT_STYLE = { width: 6, height: 6, background: "var(--primary)", borderRadius: "50%" as const };

/**
 * Inspector right-pane content. Renders selected event detail. Mockup
 * page-governance.jsx:214-263 — Event header + Context KvRows + (HITL Policy
 * section when applicable) + Raw payload pre.
 */
function LoopInspector({
  event,
  allEvents,
}: {
  event: LoopEvent | undefined;
  allEvents: LoopEvent[];
}): JSX.Element {
  if (event === undefined) {
    return (
      /* eslint-disable-next-line no-restricted-syntax -- empty-state spacing (constant ref); mockup-fidelity */
      <div style={INSPECTOR_BODY_STYLE} data-testid="loop-inspector-empty">
        {/* eslint-disable-next-line no-restricted-syntax -- section-label typography (constant ref) */}
        <div style={INSPECTOR_LABEL_STYLE}>Event Inspector</div>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup head-detail typography (constant ref); mockup-fidelity */}
        <div className="mono subtle" style={INSPECTOR_HEAD_DETAIL_STYLE}>
          Select an event row to inspect detail.
        </div>
      </div>
    );
  }

  const tone = eventTone(event);
  const isHITL =
    event.type === "approval_requested" ||
    event.type === "approval_received" ||
    event.type === "guardrail_triggered";
  // Per-event timestamp not on production wire (Phase 58+); use demo placeholder.
  const tsLabel = "2026-05-24 demo";
  const turnNum = deriveTurnNum(allEvents, event);

  return (
    <div data-testid="loop-inspector-detail">
      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:216 head wrapper (constant ref); mockup-fidelity */}
      <div style={INSPECTOR_HEAD_STYLE}>
        {/* eslint-disable-next-line no-restricted-syntax -- section-label typography (constant ref); mockup-fidelity */}
        <div style={INSPECTOR_LABEL_STYLE}>Event</div>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:218 head row (constant ref); mockup-fidelity */}
        <div className="row" style={INSPECTOR_HEAD_ROW_STYLE}>
          {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:219 dot tone (dynamic); mockup-fidelity */}
          <span className="ev-dot" style={{ ...INSPECTOR_HEAD_DOT_STYLE, background: tone }} />
          {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:220 type sizing (constant ref); mockup-fidelity */}
          <span className="mono" style={INSPECTOR_HEAD_TYPE_STYLE}>
            {event.type}
          </span>
        </div>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:222 detail typography (constant ref); mockup-fidelity */}
        <div className="mono" style={INSPECTOR_HEAD_DETAIL_STYLE}>
          {eventSummary(event)}
        </div>
      </div>
      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:224 body padding (constant ref); mockup-fidelity */}
      <div style={INSPECTOR_BODY_STYLE}>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:225 kv col gap (constant ref); mockup-fidelity */}
        <div className="col" style={INSPECTOR_KV_COL_STYLE}>
          <KvRow k="ts" v={tsLabel} mono />
          <KvRow k="turn" v={String(turnNum)} mono />
          <KvRow k="audit_id" v="demo.a8f3" mono />
          <KvRow k="span_id" v="demo.zp2" mono />
          <KvRow k="tenant" v="tenant_demo_01h9a2" mono />
          <KvRow k="session_id" v="sess_4tk2p_demo" mono />
          <KvRow k="agent" v="incident-responder" mono />
        </div>
        {isHITL && (
          <>
            <div className="thin-rule" />
            {/* eslint-disable-next-line no-restricted-syntax -- section-label typography (constant ref); mockup-fidelity */}
            <div style={INSPECTOR_LABEL_STYLE}>HITL Policy</div>
            {/* eslint-disable-next-line no-restricted-syntax -- kv col gap (constant ref); mockup-fidelity */}
            <div className="col" style={INSPECTOR_KV_COL_STYLE}>
              {event.type === "approval_requested" && (
                <>
                  <KvRow k="risk" v={event.data.risk_level} />
                  <KvRow k="policy" v="always_ask" />
                  <KvRow
                    k="approval_request_id"
                    v={event.data.approval_request_id ?? "(pending)"}
                    mono
                  />
                </>
              )}
              {event.type === "guardrail_triggered" && (
                <>
                  <KvRow k="guardrail" v={event.data.guardrail_type} />
                  <KvRow k="action" v={event.data.action} />
                </>
              )}
            </div>
          </>
        )}
        <div className="thin-rule" />
        {/* eslint-disable-next-line no-restricted-syntax -- section-label typography (constant ref); mockup-fidelity */}
        <div style={INSPECTOR_LABEL_STYLE}>Raw payload</div>
        {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:245-260 pre payload (constant ref); mockup-fidelity */}
        <pre style={INSPECTOR_PRE_STYLE}>
          {JSON.stringify({ type: event.type, data: event.data }, null, 2)}
        </pre>
      </div>
    </div>
  );
}

const KV_LABEL_STYLE = { fontFamily: "var(--font-mono)", fontSize: 11 };
const KV_VALUE_STYLE = { fontSize: 12 };

function KvRow({
  k,
  v,
  mono,
}: {
  k: string;
  v: React.ReactNode;
  mono?: boolean;
}): JSX.Element {
  return (
    <div className="spread">
      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:267 KvRow label typography (constant ref); mockup-fidelity */}
      <span className="muted" style={KV_LABEL_STYLE}>
        {k}
      </span>
      {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:268 KvRow value typography (constant ref); mockup-fidelity */}
      <span className={mono ? "mono tnum" : ""} style={KV_VALUE_STYLE}>
        {v}
      </span>
    </div>
  );
}

/**
 * Render the turn list (shared between standalone + inline modes). Each event
 * row has a click handler wiring into the standalone inspector selection state.
 */
function TurnList({
  buckets,
  isLastRunning,
  selectedIndex,
  onSelect,
}: {
  buckets: TurnBucket[];
  isLastRunning: boolean;
  selectedIndex: number | null;
  onSelect: ((index: number) => void) | null;
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
                const globalIndex = bucket.startIndex + ei;
                const isSelected = selectedIndex === globalIndex;
                const clickHandler = onSelect ? () => onSelect(globalIndex) : undefined;
                return (
                  <div
                    key={`ev-${bi}-${ei}`}
                    className="event-row"
                    data-testid={`loop-event-${ev.type}`}
                    data-selected={isSelected || undefined}
                    role={onSelect ? "button" : undefined}
                    tabIndex={onSelect ? 0 : undefined}
                    onClick={clickHandler}
                    onKeyDown={
                      onSelect
                        ? (e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              onSelect(globalIndex);
                            }
                          }
                        : undefined
                    }
                    // eslint-disable-next-line no-restricted-syntax -- verbatim mockup page-governance.jsx:198-204 selected-state highlight; mockup-fidelity pattern
                    style={
                      isSelected
                        ? {
                            background: "oklch(from var(--primary) l c h / 0.10)",
                            border: "1px solid var(--primary-soft-2)",
                            cursor: onSelect ? "pointer" : "default",
                          }
                        : { cursor: onSelect ? "pointer" : "default" }
                    }
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

export function LoopVisualizer({ mode }: LoopVisualizerProps): JSX.Element | null {
  const rawEvents = useChatStore((s) => s.rawEvents);
  const totalTurns = useChatStore((s) => s.totalTurns);

  // === Source-of-events resolution ===
  // Standalone mode with no live events → render DEMO_LOOP_EVENTS fixture so
  // the page is never empty (Sprint 57.37 US-A1). Inline mode preserves the
  // "render null when no live events" contract (chat-v2 inline panel).
  const isFixtureMode = mode === "standalone" && rawEvents.length === 0;
  const events = isFixtureMode ? DEMO_LOOP_EVENTS : rawEvents;

  // === Playback state machine (Sprint 57.37 US-A2; standalone only) ===
  // Cursor starts at events.length so live mode shows everything by default.
  // When events arrive (rawEvents grows), the cursor auto-advances unless the
  // operator has paused (cursor < events.length).
  const [cursor, setCursor] = useState(events.length);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<1 | 4 | 8 | 16>(8);

  // Auto-advance cursor to events.length when live events grow & we're not
  // mid-replay (cursor was at-or-beyond previous length).
  const [prevLength, setPrevLength] = useState(events.length);
  useEffect(() => {
    if (events.length !== prevLength) {
      if (cursor >= prevLength) setCursor(events.length);
      setPrevLength(events.length);
    }
  }, [events.length, prevLength, cursor]);

  // Playback timer
  useEffect(() => {
    if (!playing) return undefined;
    const id = setInterval(() => {
      setCursor((c) => {
        if (c >= events.length) {
          setPlaying(false);
          return c;
        }
        return c + 1;
      });
    }, 1000 / speed);
    return () => clearInterval(id);
  }, [playing, speed, events.length]);

  // === Filter state (Sprint 57.37 US-A3; standalone only) ===
  const [filter, setFilter] = useState<Record<FilterCategory, boolean>>({
    thinking: true,
    tool: true,
    memory: true,
    hitl: true,
    verification: true,
    subagent: true,
  });

  // === Inspector selection (Sprint 57.37 US-A4; standalone only) ===
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Visible events = up-to-cursor, with category filter applied.
  const visibleEvents = useMemo(() => events.slice(0, cursor), [events, cursor]);
  const filteredEvents = useMemo(
    () =>
      visibleEvents.filter((ev) => {
        const cat = eventCategory(ev);
        return cat === null || filter[cat];
      }),
    [visibleEvents, filter]
  );

  // The selected event is resolved from the ORIGINAL events array (not the
  // filtered one), so selection survives filter toggling. Returns undefined
  // when selectedIndex points to a filtered-out event or no selection.
  const selectedEvent = useMemo(() => {
    if (selectedIndex === null) return undefined;
    return events[selectedIndex];
  }, [events, selectedIndex]);

  // === Empty-state branches ===
  if (mode === "inline" && rawEvents.length === 0) return null;

  const buckets = groupByTurn(mode === "standalone" ? filteredEvents : rawEvents);
  // Inline mode: only expand the last 5 turns; collapse the rest into a count.
  const collapsedCount = mode === "inline" && buckets.length > 5 ? buckets.length - 5 : 0;
  const visibleBuckets = collapsedCount > 0 ? buckets.slice(collapsedCount) : buckets;
  const isLastRunning = !events.some((ev) => ev.type === "loop_end");
  const isLive = cursor >= events.length;

  if (mode === "standalone") {
    return (
      <div
        className="loop-canvas"
        data-testid="loop-visualizer-standalone"
        data-fixture-mode={isFixtureMode || undefined}
        aria-label="Loop visualizer"
      >
        <div className="loop-track">
          {/* === LoopDebugHeader: title + filter pills + playback strip === */}
          {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:119 wrapper margin/gap (constant ref); mockup-fidelity */}
          <div className="col" style={HEADER_COL_STYLE}>
            {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:120 title row gap (constant ref); mockup-fidelity */}
            <div className="row" style={HEADER_TITLE_ROW_STYLE}>
              <div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:122 title sizing (constant ref); mockup-fidelity */}
                <div className="page-title" style={HEADER_TITLE_STYLE}>
                  Loop Visualizer
                </div>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:123-129 page-sub layout (constant ref); mockup-fidelity */}
                <div style={HEADER_SUB_STYLE}>
                  Session <span className="mono">sess_4tk2p_demo</span>
                  <span className="route-pill">/loop-debug</span>
                </div>
              </div>
              <span className="grow" />
              {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:132 filter-pills row (constant ref); mockup-fidelity */}
              <div className="row" style={FILTER_PILLS_ROW_STYLE} data-testid="loop-filter-pills">
                {FILTER_CATEGORIES.map(({ key, color }) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setFilter((f) => ({ ...f, [key]: !f[key] }))}
                    className="badge"
                    data-testid={`loop-filter-${key}`}
                    data-active={filter[key] || undefined}
                    // eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:138-145 pill opacity+tint (dynamic per filter state); mockup-fidelity
                    style={{
                      opacity: filter[key] ? 1 : 0.35,
                      color,
                      background: `oklch(from ${color} l c h / 0.14)`,
                      borderColor: `oklch(from ${color} l c h / 0.32)`,
                      cursor: "pointer",
                      fontSize: 11,
                    }}
                  >
                    {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:147 pill dot (dynamic background); mockup-fidelity */}
                    <span style={{ ...PILL_DOT_STYLE, background: color }} />
                    {key}
                  </button>
                ))}
              </div>
            </div>

            {/* === Playback strip === */}
            {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:154 playback row (constant ref); mockup-fidelity */}
            <div className="row" style={PLAYBACK_ROW_STYLE} data-testid="loop-playback-strip">
              <button
                type="button"
                className={`btn ${playing ? "warning" : "primary"}`}
                data-size="sm"
                data-testid="loop-playback-play"
                onClick={() => {
                  if (cursor >= events.length) setCursor(1);
                  setPlaying((p) => !p);
                }}
              >
                {playing ? "Pause" : cursor >= events.length ? "Replay" : "Resume"}
              </button>
              <button
                type="button"
                className="btn ghost"
                data-size="sm"
                data-testid="loop-playback-reset"
                onClick={() => {
                  setCursor(events.length);
                  setPlaying(false);
                }}
                title="Skip to live"
              >
                Live
              </button>
              {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:159 scrubber wrapper (constant ref); mockup-fidelity */}
              <div style={SCRUBBER_FLEX_STYLE}>
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:160 cursor label sizing (constant ref); mockup-fidelity */}
                <span className="mono subtle" style={PLAYBACK_CURSOR_LABEL_STYLE}>
                  {String(cursor).padStart(2, "0")} / {events.length}
                </span>
                <input
                  type="range"
                  min={0}
                  max={events.length}
                  value={cursor}
                  data-testid="loop-playback-scrubber"
                  onChange={(e) => {
                    setCursor(Number(e.target.value));
                    setPlaying(false);
                  }}
                  // eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:166 scrubber accent (constant ref); mockup-fidelity
                  style={SCRUBBER_INPUT_STYLE}
                  aria-label="Playback cursor"
                />
                {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:168 right label sizing (constant ref); mockup-fidelity */}
                <span className="mono subtle" style={PLAYBACK_CURSOR_LABEL_RIGHT_STYLE}>
                  {filteredEvents.length} shown
                </span>
              </div>
              <div className="btn-group">
                {([1, 4, 8, 16] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="btn"
                    data-size="sm"
                    data-testid={`loop-playback-speed-${s}`}
                    data-active={s === speed || undefined}
                    onClick={() => setSpeed(s)}
                    // eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:176-179 speed pill active state (dynamic); mockup-fidelity
                    style={{
                      background: s === speed ? "var(--primary-soft)" : "var(--bg-1)",
                      color: s === speed ? "var(--primary)" : "var(--fg-muted)",
                      borderColor: s === speed ? "var(--primary-soft-2)" : "var(--border)",
                    }}
                  >
                    {s}×
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* AP-2 BackendGapBanner (Sprint 57.37 US-A5: honest disclosure) */}
          <BackendGapBanner
            reason={
              isFixtureMode
                ? "DEMO DATA — these events are fixture data from the mockup; live SSE events populate when a chat-v2 session runs. Per-event detail persistence + cross-session lookup require backend SSE event persistence (Phase 58+ per Sprint 57.12 AP-6)."
                : "Per-event detail persistence + cross-session lookup require backend SSE event persistence (Phase 58+ per Sprint 57.12 AP-6)."
            }
          />

          <div
            className="row"
            // eslint-disable-next-line no-restricted-syntax -- summary row spacing+tone (constant ref); preserves Sprint 57.12 summary inside verbatim mockup .loop-track
            style={STANDALONE_SUMMARY_STYLE}
            data-testid="loop-visualizer-summary"
          >
            <span>
              Turns:{" "}
              {/* eslint-disable-next-line no-restricted-syntax -- foreground tone for emphasis (constant ref); mockup-token */}
              <strong style={STANDALONE_STRONG_STYLE}>
                {totalTurns || buckets.length}
              </strong>
            </span>
            <span>
              Events:{" "}
              {/* eslint-disable-next-line no-restricted-syntax -- foreground tone for emphasis (constant ref); mockup-token */}
              <strong style={STANDALONE_STRONG_STYLE}>{events.length}</strong>
            </span>
          </div>

          <TurnList
            buckets={visibleBuckets}
            isLastRunning={isLastRunning && isLive}
            selectedIndex={selectedIndex}
            onSelect={setSelectedIndex}
          />

          {!isLive && (
            // eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:107 replay footer (constant ref); mockup-fidelity
            <div style={REPLAY_FOOTER_STYLE} data-testid="loop-replay-footer">
              {/* eslint-disable-next-line no-restricted-syntax -- mockup page-governance.jsx:108 replay dot (constant ref); mockup-fidelity */}
              <span className="pulse" style={REPLAY_DOT_STYLE} />
              replaying at {speed}× · {cursor}/{events.length} events
            </div>
          )}
        </div>
        <aside className="loop-inspector">
          <LoopInspector event={selectedEvent} allEvents={events} />
        </aside>
      </div>
    );
  }

  // === Inline mode (chat-v2 cascade) — preserved Sprint 57.30 ship ===
  // No canvas, no banner, no playback, no filter, no inspector pane.
  // Render the original rawEvents stream (NOT fixture) — already empty-checked above.
  const inlineBuckets = groupByTurn(rawEvents);
  const inlineCollapsed = inlineBuckets.length > 5 ? inlineBuckets.length - 5 : 0;
  const inlineVisible = inlineCollapsed > 0 ? inlineBuckets.slice(inlineCollapsed) : inlineBuckets;
  const inlineLastRunning = !rawEvents.some((ev) => ev.type === "loop_end");

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
        Loop ({inlineBuckets.length} turn{inlineBuckets.length === 1 ? "" : "s"})
      </div>
      {inlineCollapsed > 0 && (
        // eslint-disable-next-line no-restricted-syntax -- inline-mode collapsed-count typography (constant ref); preserves Sprint 57.12 UX
        <div className="mono subtle" style={INLINE_COLLAPSED_STYLE}>
          {inlineCollapsed} earlier turn{inlineCollapsed === 1 ? "" : "s"} collapsed
        </div>
      )}
      <TurnList
        buckets={inlineVisible}
        isLastRunning={inlineLastRunning}
        selectedIndex={null}
        onSelect={null}
      />
    </div>
  );
}

// Re-export empty-state style constant so external tests / future consumers can
// reference; not used internally beyond the (now-removed) Sprint 57.36 stub.
export { EMPTY_STATE_STYLE };
