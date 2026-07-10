/**
 * File: frontend/tests/unit/orchestrator-loop/LoopVisualizer.test.tsx
 * Purpose: Vitest tests for LoopVisualizer component — dual-mode rendering + turn grouping + event severity + Sprint 57.37 fixture/playback/filter/inspector.
 * Category: Frontend / tests / unit / orchestrator-loop
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-4; Sprint 57.37 Day 1-2 fixture + playback + filter + inspector.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2 / US-4)
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.37 Day 1-2 — fixture mode + playback + filter + inspector specs; empty-state spec updated to reflect fixture renders by default in standalone
 *   - 2026-05-24: Sprint 57.36 Day 1-2 — adapt to verbatim CSS re-point (border-red-500 → ev-type color var(--danger))
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 2 / US-4)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";
import { LoopVisualizer } from "@/features/orchestrator-loop/components/LoopVisualizer";
import { DEMO_LOOP_EVENTS } from "@/features/orchestrator-loop/_fixtures/demoLoopEvents";

function feed(events: LoopEvent[]): void {
  const merge = useChatStore.getState().mergeEvent;
  for (const ev of events) merge(ev);
}

describe("LoopVisualizer (Sprint 57.12 US-4 + Sprint 57.37 fixture/playback/filter/inspector)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("inline mode renders null when no events (contract preserved)", () => {
    const { container } = render(<LoopVisualizer mode="inline" />);
    expect(container.firstChild).toBeNull();
  });

  test("standalone mode renders DEMO_LOOP_EVENTS fixture when no live events (Sprint 57.37 US-A1)", () => {
    render(<LoopVisualizer mode="standalone" />);
    const root = screen.getByTestId("loop-visualizer-standalone");
    expect(root).toBeInTheDocument();
    // data-fixture-mode flag should be set
    expect(root.getAttribute("data-fixture-mode")).toBe("true");
    // banner copy should mention DEMO DATA
    expect(screen.getByTestId("backend-gap-banner").textContent).toMatch(/DEMO DATA/i);
    // Fixture has 18 events; events label in summary should reflect
    const summary = screen.getByTestId("loop-visualizer-summary");
    expect(summary).toHaveTextContent(`Events: ${DEMO_LOOP_EVENTS.length}`);
  });

  test("standalone mode with live events uses rawEvents (fixture suppressed)", () => {
    feed([
      { type: "loop_start", data: { session_id: "s_live", request_id: "r1" } },
      { type: "turn_start", data: { turn_num: 0 } },
      { type: "loop_end", data: { stop_reason: "end_turn", total_turns: 1 } },
    ]);
    render(<LoopVisualizer mode="standalone" />);
    const root = screen.getByTestId("loop-visualizer-standalone");
    // Fixture flag NOT set when live events present
    expect(root.getAttribute("data-fixture-mode")).toBeNull();
    // Banner copy should NOT mention DEMO DATA
    expect(screen.getByTestId("backend-gap-banner").textContent).not.toMatch(/DEMO DATA/i);
    // Summary should show 3 (live events)
    expect(screen.getByTestId("loop-visualizer-summary")).toHaveTextContent("Events: 3");
  });

  test("renders mixed event types grouped per turn (inline)", () => {
    feed([
      { type: "loop_start", data: { session_id: "s1", request_id: "r1" } },
      { type: "turn_start", data: { turn_num: 0 } },
      { type: "llm_request", data: { model: "gpt-x", tokens_in: 100 } },
      {
        type: "llm_response",
        data: { content: "hello", tool_calls: [], thinking: null },
      },
      { type: "turn_start", data: { turn_num: 1 } },
      {
        type: "tool_call_result",
        data: {
          tool_call_id: "tc1",
          tool_name: "search",
          duration_ms: 42,
          result: "ok",
          is_error: false,
          error_taxonomy: null, // Sprint 57.164
        },
      },
      { type: "loop_end", data: { stop_reason: "end_turn", total_turns: 2 } },
    ]);
    render(<LoopVisualizer mode="inline" />);
    expect(screen.getByTestId("loop-visualizer-inline")).toBeInTheDocument();
    expect(screen.getByTestId("loop-turn-0")).toBeInTheDocument();
    expect(screen.getByTestId("loop-turn-1")).toBeInTheDocument();
    expect(screen.getByTestId("loop-event-llm_request")).toBeInTheDocument();
    expect(screen.getByTestId("loop-event-tool_call_result")).toBeInTheDocument();
  });

  test("standalone mode renders summary header with turn + event counts (live)", () => {
    feed([
      { type: "loop_start", data: { session_id: "s1", request_id: "r1" } },
      { type: "turn_start", data: { turn_num: 0 } },
      { type: "loop_end", data: { stop_reason: "end_turn", total_turns: 1 } },
    ]);
    render(<LoopVisualizer mode="standalone" />);
    const summary = screen.getByTestId("loop-visualizer-summary");
    expect(summary).toHaveTextContent("Events:");
    expect(summary).toHaveTextContent("3");
  });

  test("failed events get danger tone (verification_failed)", () => {
    feed([
      { type: "turn_start", data: { turn_num: 0 } },
      {
        type: "verification_failed",
        data: {
          verifier: "topic_check",
          verifier_type: "llm_judge",
          reason: "off-topic",
          suggested_correction: null,
        },
      },
    ]);
    render(<LoopVisualizer mode="standalone" />);
    const evRow = screen.getByTestId("loop-event-verification_failed");
    expect(evRow.className).toContain("event-row");
    const evType = evRow.querySelector(".ev-type") as HTMLElement | null;
    expect(evType).not.toBeNull();
    expect(evType?.getAttribute("style")).toContain("var(--danger)");
    const evDot = evRow.querySelector(".ev-dot") as HTMLElement | null;
    expect(evDot).not.toBeNull();
    expect(evDot?.getAttribute("style")).toContain("var(--danger)");
  });

  test("inline mode collapses turns older than the last 5", () => {
    const events: LoopEvent[] = [];
    for (let i = 0; i < 8; i++) {
      events.push({ type: "turn_start", data: { turn_num: i } });
      events.push({ type: "llm_request", data: { model: "gpt-x", tokens_in: 1 } });
    }
    feed(events);
    render(<LoopVisualizer mode="inline" />);
    expect(screen.getByText(/3 earlier turns collapsed/i)).toBeInTheDocument();
    expect(screen.queryByTestId("loop-turn-0")).toBeNull();
    expect(screen.getByTestId("loop-turn-7")).toBeInTheDocument();
  });

  // === Sprint 57.37 NEW: playback + filter + inspector specs ===

  test("playback strip renders 4 speed pills + play/reset buttons (Sprint 57.37 US-A2)", () => {
    render(<LoopVisualizer mode="standalone" />);
    expect(screen.getByTestId("loop-playback-strip")).toBeInTheDocument();
    expect(screen.getByTestId("loop-playback-play")).toBeInTheDocument();
    expect(screen.getByTestId("loop-playback-reset")).toBeInTheDocument();
    expect(screen.getByTestId("loop-playback-scrubber")).toBeInTheDocument();
    for (const s of [1, 4, 8, 16]) {
      expect(screen.getByTestId(`loop-playback-speed-${s}`)).toBeInTheDocument();
    }
    // 8× is the default — should have data-active
    expect(screen.getByTestId("loop-playback-speed-8").getAttribute("data-active")).toBe("true");
  });

  test("clicking a speed pill updates active speed (Sprint 57.37 US-A2)", async () => {
    const user = userEvent.setup();
    render(<LoopVisualizer mode="standalone" />);
    await user.click(screen.getByTestId("loop-playback-speed-4"));
    expect(screen.getByTestId("loop-playback-speed-4").getAttribute("data-active")).toBe("true");
    expect(screen.getByTestId("loop-playback-speed-8").getAttribute("data-active")).toBeNull();
  });

  test("filter pills render 6 categories all active by default (Sprint 57.37 US-A3)", () => {
    render(<LoopVisualizer mode="standalone" />);
    expect(screen.getByTestId("loop-filter-pills")).toBeInTheDocument();
    for (const cat of ["thinking", "tool", "memory", "hitl", "verification", "subagent"]) {
      const pill = screen.getByTestId(`loop-filter-${cat}`);
      expect(pill).toBeInTheDocument();
      expect(pill.getAttribute("data-active")).toBe("true");
    }
  });

  test("clicking a filter pill toggles category & hides matching events (Sprint 57.37 US-A3)", async () => {
    const user = userEvent.setup();
    render(<LoopVisualizer mode="standalone" />);
    // Default fixture includes llm_request + llm_response (thinking category)
    expect(screen.queryAllByTestId("loop-event-llm_request").length).toBeGreaterThan(0);
    // Toggle thinking off
    await user.click(screen.getByTestId("loop-filter-thinking"));
    expect(screen.getByTestId("loop-filter-thinking").getAttribute("data-active")).toBeNull();
    // llm_request rows should be hidden
    expect(screen.queryAllByTestId("loop-event-llm_request").length).toBe(0);
    // tool_call_result rows should still be present (tool category still active)
    expect(screen.queryAllByTestId("loop-event-tool_call_result").length).toBeGreaterThan(0);
  });

  test("inspector pane shows empty-state by default (Sprint 57.37 US-A4)", () => {
    render(<LoopVisualizer mode="standalone" />);
    expect(screen.getByTestId("loop-inspector-empty")).toBeInTheDocument();
    expect(screen.queryByTestId("loop-inspector-detail")).toBeNull();
  });

  test("clicking an event row populates inspector with event detail (Sprint 57.37 US-A4)", async () => {
    const user = userEvent.setup();
    render(<LoopVisualizer mode="standalone" />);
    // Click the first llm_request row
    const rows = screen.getAllByTestId("loop-event-llm_request");
    await user.click(rows[0]);
    expect(screen.getByTestId("loop-inspector-detail")).toBeInTheDocument();
    expect(screen.queryByTestId("loop-inspector-empty")).toBeNull();
    // Detail should include the type
    expect(screen.getByTestId("loop-inspector-detail").textContent).toMatch(/llm_request/);
  });

  test("inspector renders HITL Policy section for approval_requested (Sprint 57.37 US-A4)", async () => {
    const user = userEvent.setup();
    render(<LoopVisualizer mode="standalone" />);
    const approvalRows = screen.getAllByTestId("loop-event-approval_requested");
    expect(approvalRows.length).toBeGreaterThan(0);
    await user.click(approvalRows[0]);
    expect(screen.getByTestId("loop-inspector-detail")).toBeInTheDocument();
    // HITL Policy section should be visible
    expect(screen.getByText("HITL Policy")).toBeInTheDocument();
    // risk field should be present (fixture has risk_level=high)
    expect(screen.getByText("risk")).toBeInTheDocument();
  });
});
