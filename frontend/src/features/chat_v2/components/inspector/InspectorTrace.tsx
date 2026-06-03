/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorTrace.tsx
 * Purpose: Inspector "Trace" tab — verbatim mockup re-point of page-chat.jsx L434-466 (OTel span waterfall).
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.75 (A-5 Inspector UI — Trace tab; consumes SpanStarted/SpanEnded SSE)
 *
 * Description:
 *   Mockup L434-466 (InspectorTrace): a section header ("Cat 12 · OTel spans")
 *   then one `.row` per span — a fixed-width name column (`paddingLeft` by indent
 *   depth + tree-glyph), a flex duration-bar track (`.bg-2` background) with a
 *   colored fill (width = duration / max), and a right-aligned `{d}s` label.
 *
 *   Reads the chatStore.spans slice (Sprint 57.75; populated by the span_started
 *   / span_ended SSE branches). orderSpans() flattens the spans into the mockup's
 *   parent-before-child waterfall order and computes each span's indent depth by
 *   walking the parentSpanId chain (a visited set guards cycles; depth capped for
 *   layout safety). Tree-glyphs (`├─` / `└─`) prefix nested rows.
 *
 *   Render-vs-placeholder: the bar fill is scaled by the max *completed* duration;
 *   a still-running span (durationMs == null) renders a subtle pending bar + an
 *   em-dash in place of the `{d}s` value (NOT a fabricated duration). AP-4: nothing
 *   is invented; an empty spans slice shows an honest empty state.
 *
 *   Pure read; no side effects.
 *
 * Key Components:
 *   - InspectorTrace: tab component reading useChatStore((s) => s.spans)
 *   - orderSpans(): flat SpanNode[] → ordered rows (depth + glyph) by parentSpanId
 *   - SPAN_COLOR: span_type → mockup color token
 *
 * Created: 2026-06-03 (Sprint 57.75)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.75) — A-5 Trace tab verbatim re-point
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L434-466 (InspectorTrace)
 *   - frontend/src/styles-mockup.css L194 (.mono) — colors via var(--*) tokens inline
 *   - ../../store/chatStore.ts (spans slice + SpanNode — Sprint 57.75)
 *   - ./InspectorTree.tsx (sibling wired tab — empty-state + verbatim-class pattern)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L436
   (section header inline font-size/color/text-transform/letter-spacing/font-family),
   L456-462 (waterfall row inline name width/paddingLeft/ellipsis + bar track/fill +
   right duration label). Colors via var(--*) tokens — not literals. */

import { useChatStore } from "../../store/chatStore";
import type { SpanNode } from "../../store/chatStore";

// Layout-safety cap: span nesting is bounded by the loop's fixed span hierarchy
// (LOOP→TURN→leaf), but a malformed parentSpanId chain could in theory recurse.
const MAX_DEPTH = 8;

// Minimum visible bar width (%) so a sub-millisecond span is still perceivable.
const MIN_BAR_PCT = 2;

/**
 * span_type → mockup color token. Mirrors the mockup's per-span-kind colors
 * (L438-451): loop=primary, tool=tool, llm=info, prompt-build=success,
 * compaction=warning, turn=memory(reuse). Unknown types fall back to fg-muted.
 */
const SPAN_COLOR: Record<string, string> = {
  LOOP: "var(--primary)",
  TURN: "var(--memory)",
  LLM_CALL: "var(--info)",
  TOOL_EXEC: "var(--tool)",
  PROMPT_BUILD: "var(--success)",
  COMPACTION: "var(--warning)",
};

interface OrderedSpan {
  span: SpanNode;
  depth: number;
  isLast: boolean;
}

/**
 * Flatten the span list into parent-before-child waterfall order with per-row
 * indent depth. Roots = spans whose parentSpanId is empty or not a known span;
 * children grouped by parentSpanId preserving arrival order. A visited set
 * guards cycles; depth is capped at MAX_DEPTH for layout safety.
 */
function orderSpans(spans: SpanNode[]): OrderedSpan[] {
  const byId = new Map(spans.map((sp) => [sp.spanId, sp]));
  const childrenOf = new Map<string, SpanNode[]>();
  const roots: SpanNode[] = [];
  for (const sp of spans) {
    const parentIsKnown = sp.parentSpanId !== "" && byId.has(sp.parentSpanId);
    if (parentIsKnown) {
      const arr = childrenOf.get(sp.parentSpanId) ?? [];
      arr.push(sp);
      childrenOf.set(sp.parentSpanId, arr);
    } else {
      roots.push(sp);
    }
  }
  const visited = new Set<string>();
  const out: OrderedSpan[] = [];
  const walk = (sp: SpanNode, depth: number, isLast: boolean): void => {
    if (visited.has(sp.spanId)) return;
    visited.add(sp.spanId);
    out.push({ span: sp, depth, isLast });
    if (depth >= MAX_DEPTH) return;
    const kids = (childrenOf.get(sp.spanId) ?? []).filter((c) => !visited.has(c.spanId));
    kids.forEach((c, i) => walk(c, depth + 1, i === kids.length - 1));
  };
  roots.forEach((r, i) => walk(r, 0, i === roots.length - 1));
  return out;
}

/** Tree-glyph prefix for nested rows (root rows get no glyph, matching mockup). */
function glyph(depth: number, isLast: boolean): string {
  if (depth === 0) return "";
  return isLast ? "└─ " : "├─ ";
}

export function InspectorTrace(): JSX.Element {
  const spans = useChatStore((s) => s.spans);

  if (spans.length === 0) {
    return (
      <div
        data-testid="inspector-trace-empty"
        style={{ padding: "12px 16px", fontSize: 12, color: "var(--fg-muted)" }}
      >
        <div
          style={{
            fontSize: 11.5,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontFamily: "var(--font-mono)",
          }}
        >
          Cat 12 · OTel spans
        </div>
        <p style={{ marginTop: 8, lineHeight: 1.55 }}>no spans yet</p>
      </div>
    );
  }

  const ordered = orderSpans(spans);
  const completed = spans
    .map((sp) => sp.durationMs)
    .filter((d): d is number => d != null);
  const max = completed.length > 0 ? Math.max(...completed) : 1;

  return (
    <div data-testid="inspector-trace" style={{ padding: "12px 16px" }}>
      <div
        style={{
          fontSize: 11.5,
          color: "var(--fg-subtle)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 8,
          fontFamily: "var(--font-mono)",
        }}
      >
        Cat 12 · OTel spans · {spans.length} span{spans.length === 1 ? "" : "s"}
      </div>

      {ordered.map(({ span, depth, isLast }) => {
        const color = SPAN_COLOR[span.spanType] ?? "var(--fg-muted)";
        const ms = span.durationMs;
        const running = ms == null;
        const seconds = ms == null ? null : ms / 1000;
        const widthPct = ms == null ? MIN_BAR_PCT : Math.max(MIN_BAR_PCT, (ms / max) * 100);
        return (
          <div
            key={span.spanId}
            data-testid={`inspector-trace-span-${span.spanId}`}
            className="row"
            style={{ gap: 8, padding: "2px 0", fontSize: 10.5, fontFamily: "var(--font-mono)" }}
          >
            <span
              style={{
                width: 200,
                color: "var(--fg-muted)",
                paddingLeft: depth * 10,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {glyph(depth, isLast)}
              {span.spanName}
            </span>
            <span
              style={{
                flex: 1,
                height: 8,
                background: "var(--bg-2)",
                borderRadius: 2,
                overflow: "hidden",
                position: "relative",
              }}
            >
              <span
                style={{
                  display: "block",
                  width: `${widthPct}%`,
                  height: "100%",
                  background: color,
                  borderRadius: 2,
                  opacity: running ? 0.4 : 1,
                }}
              />
            </span>
            <span style={{ width: 50, textAlign: "right", color: "var(--fg-subtle)" }}>
              {seconds == null ? "—" : `${seconds.toFixed(2)}s`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default InspectorTrace;
