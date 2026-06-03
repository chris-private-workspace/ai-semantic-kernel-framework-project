/**
 * File: frontend/tests/unit/chat_v2/components/inspector/InspectorTrace.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.75 InspectorTrace (span waterfall).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.75 (A-5 Inspector Trace tab)
 *
 * Created: 2026-06-03 (Sprint 57.75)
 *
 * Modification History:
 *   - 2026-06-03: Initial creation (Sprint 57.75) — empty / waterfall nesting / running vs done / color
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { InspectorTrace } from "@/features/chat_v2/components/inspector/InspectorTrace";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { SpanNode } from "@/features/chat_v2/store/chatStore";

function makeSpan(overrides: Partial<SpanNode> = {}): SpanNode {
  return {
    spanId: "sp-1",
    parentSpanId: "",
    spanType: "LOOP",
    spanName: "agent_loop",
    durationMs: 1420,
    status: "done",
    ...overrides,
  };
}

describe("InspectorTrace (Sprint 57.75)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("empty state when no spans", () => {
    render(<InspectorTrace />);
    expect(screen.getByTestId("inspector-trace-empty")).toBeInTheDocument();
    expect(screen.getByText("no spans yet")).toBeInTheDocument();
  });

  test("renders one row per span with span_name + duration label", () => {
    useChatStore.setState({
      spans: [makeSpan({ spanId: "loop", spanName: "agent_loop", durationMs: 1420 })],
    });
    render(<InspectorTrace />);
    expect(screen.getByTestId("inspector-trace")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-trace-span-loop")).toBeInTheDocument();
    expect(screen.getByText("agent_loop")).toBeInTheDocument();
    expect(screen.getByText("1.42s")).toBeInTheDocument();
  });

  test("waterfall nesting: child rows get tree-glyph prefix + indent (parent_span_id)", () => {
    useChatStore.setState({
      spans: [
        makeSpan({ spanId: "loop", spanType: "LOOP", spanName: "agent_loop", parentSpanId: "" }),
        makeSpan({
          spanId: "turn",
          spanType: "TURN",
          spanName: "agent_loop.turn",
          parentSpanId: "loop",
        }),
        makeSpan({
          spanId: "llm",
          spanType: "LLM_CALL",
          spanName: "agent_loop.llm_call",
          parentSpanId: "turn",
        }),
      ],
    });
    render(<InspectorTrace />);
    // Child rows carry the └─ / ├─ glyph (last-child = └─).
    const turnRow = screen.getByTestId("inspector-trace-span-turn");
    expect(turnRow.textContent).toContain("└─");
    expect(turnRow.textContent).toContain("agent_loop.turn");
    const llmRow = screen.getByTestId("inspector-trace-span-llm");
    expect(llmRow.textContent).toContain("agent_loop.llm_call");
    // Root row has no glyph.
    const loopRow = screen.getByTestId("inspector-trace-span-loop");
    expect(loopRow.textContent).not.toContain("└─");
    expect(loopRow.textContent).not.toContain("├─");
  });

  test("running span (durationMs null) shows em-dash, not a fabricated duration", () => {
    useChatStore.setState({
      spans: [makeSpan({ spanId: "open", status: "running", durationMs: null })],
    });
    render(<InspectorTrace />);
    const row = screen.getByTestId("inspector-trace-span-open");
    expect(row.textContent).toContain("—");
    expect(row.textContent).not.toContain("s");
  });

  test("color by span_type maps to mockup token (TOOL_EXEC → var(--tool))", () => {
    useChatStore.setState({
      spans: [makeSpan({ spanId: "tool", spanType: "TOOL_EXEC", durationMs: 80 })],
    });
    render(<InspectorTrace />);
    const row = screen.getByTestId("inspector-trace-span-tool");
    // The fill bar carries the span-type color inline.
    expect(row.innerHTML).toContain("var(--tool)");
  });

  test("header reflects span count", () => {
    useChatStore.setState({
      spans: [makeSpan({ spanId: "a" }), makeSpan({ spanId: "b", parentSpanId: "a" })],
    });
    render(<InspectorTrace />);
    expect(screen.getByText(/2 spans/)).toBeInTheDocument();
  });
});
