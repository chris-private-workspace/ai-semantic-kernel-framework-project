/**
 * File: frontend/tests/unit/chat_v2/components/inspector/ChatInspector.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.21 Day 4 §4.1 Inspector 4-tab frame + Turn + 3 coming-soon.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.21 Day 4 §4.1
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.1)
 *
 * Modification History:
 *   - 2026-06-15: Sprint 57.120 — +active_skill row cases (⚡ set / "—" absent); null-dash count 6→7
 *   - 2026-06-03: Sprint 57.75 — Trace+Memory tabs now wired (A-5); replace ComingSoon assertions with empty states
 *   - 2026-06-03: Sprint 57.72 — Tree tab now renders InspectorTree (A-5c); replace ComingSoon-Tree assertion with empty + populated tree
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.1)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { ChatInspector } from "@/features/chat_v2/components/inspector/ChatInspector";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { AgentTurn } from "@/features/chat_v2/types";
import type { SubagentNode } from "@/features/subagent/types";

function makeSubagent(overrides: Partial<SubagentNode> = {}): SubagentNode {
  return {
    subagentId: "sa-root",
    parentId: "chat-1",
    mode: "fork",
    status: "running",
    summary: null,
    tokensUsed: null,
    spawnedAt: Date.now(),
    childEvents: [],
    ...overrides,
  };
}

function makeAgentTurn(overrides: Partial<AgentTurn> = {}): AgentTurn {
  return {
    role: "agent",
    id: "t_a1",
    at: "10:42:19",
    stopReason: "tool_use",
    durationMs: 2410,
    blocks: [
      { type: "thinking", text: "Analyzing pool saturation" },
      {
        type: "tool",
        toolCallId: "tc-1",
        name: "metrics.query",
        status: "ok",
        input: "{}",
        output: "ok",
        durationMs: 210,
        isError: false,
      },
    ],
    tokensIn: 14820,
    tokensOut: 186,
    tokensThinking: 412,
    costUsd: 0.0142,
    traceId: "6f3a.b2k1",
    spanId: "a04.zp2",
    ...overrides,
  };
}

describe("ChatInspector (Sprint 57.21 Day 4 §4.1)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("default tab = Turn; renders InspectorTurn empty state when no agent turn", () => {
    render(<ChatInspector />);
    expect(screen.getByTestId("inspector-turn-empty")).toBeInTheDocument();
    expect(screen.getByText("No active turn")).toBeInTheDocument();
  });

  test("InspectorTurn populated with KV pairs when agent turn exists", () => {
    useChatStore.setState({ turns: [makeAgentTurn()] });
    render(<ChatInspector />);
    expect(screen.getByTestId("inspector-turn")).toBeInTheDocument();
    expect(screen.getByText("Turn 1 · tool_use")).toBeInTheDocument();
    expect(screen.getByText("2.41s")).toBeInTheDocument();
    expect(screen.getByText("14,820")).toBeInTheDocument();
    expect(screen.getByText("186")).toBeInTheDocument();
    expect(screen.getByText("412")).toBeInTheDocument();
    expect(screen.getByText("$0.0142")).toBeInTheDocument();
    expect(screen.getByText("6f3a.b2k1")).toBeInTheDocument();
    expect(screen.getByText("a04.zp2")).toBeInTheDocument();
  });

  test("InspectorTurn shows '—' placeholders when metadata fields null", () => {
    useChatStore.setState({
      turns: [
        makeAgentTurn({
          tokensIn: null,
          tokensOut: null,
          tokensThinking: null,
          costUsd: null,
          traceId: null,
          spanId: null,
        }),
      ],
    });
    render(<ChatInspector />);
    const dashes = screen.getAllByText("—");
    // 7 fields nullable: tokens.in / tokens.out / tokens.thinking / cost / trace_id /
    // span_id / active_skill (Sprint 57.120 — makeAgentTurn default carries no skill)
    expect(dashes.length).toBeGreaterThanOrEqual(7);
  });

  // Sprint 57.120: the Inspector Turn tab surfaces the force-loaded skill (carried
  // onto the AgentTurn at turn_start) as an active_skill KV row.
  test("InspectorTurn shows the active_skill row with ⚡ {skill} when set", () => {
    useChatStore.setState({ turns: [makeAgentTurn({ activeSkill: "code-review" })] });
    render(<ChatInspector />);
    expect(screen.getByTestId("inspector-turn")).toBeInTheDocument();
    expect(screen.getByText("active_skill")).toBeInTheDocument();
    expect(screen.getByText("⚡ code-review")).toBeInTheDocument();
  });

  test("InspectorTurn shows active_skill '—' when the turn carries no skill", () => {
    useChatStore.setState({ turns: [makeAgentTurn()] }); // default: no activeSkill
    render(<ChatInspector />);
    expect(screen.getByText("active_skill")).toBeInTheDocument();
    // the only nullable-rendered field in the otherwise-populated default turn
    expect(screen.getAllByText("—")).toHaveLength(1);
  });

  test("Block sequence renders 1 line per block with correct type label", () => {
    useChatStore.setState({ turns: [makeAgentTurn()] });
    render(<ChatInspector />);
    expect(screen.getByText("thinking")).toBeInTheDocument();
    expect(screen.getByText("tool")).toBeInTheDocument();
    expect(screen.getByText("metrics.query · 210ms")).toBeInTheDocument();
  });

  test("Switch to Trace tab → InspectorTrace empty state when no spans (no ComingSoon placeholder)", async () => {
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Trace" }));
    expect(screen.getByTestId("inspector-trace-empty")).toBeInTheDocument();
    expect(screen.getByText("no spans yet")).toBeInTheDocument();
    // Trace tab no longer renders the ComingSoon placeholder (Sprint 57.75 wire-in).
    expect(screen.queryByTestId("inspector-tab-coming-soon-trace")).toBeNull();
  });

  test("Switch to Memory tab → InspectorMemory empty state when no memory ops (no ComingSoon placeholder)", async () => {
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Memory" }));
    expect(screen.getByTestId("inspector-memory-empty")).toBeInTheDocument();
    expect(screen.getByText("no memory accesses this session")).toBeInTheDocument();
    // Memory tab no longer renders the ComingSoon placeholder (Sprint 57.75 wire-in).
    expect(screen.queryByTestId("inspector-tab-coming-soon-memory")).toBeNull();
  });

  test("Switch to Tree tab → InspectorTree empty state when no subagents (no ComingSoon placeholder)", async () => {
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Tree" }));
    expect(screen.getByTestId("inspector-tree-empty")).toBeInTheDocument();
    expect(screen.getByText("no subagents spawned this session")).toBeInTheDocument();
    // Tree tab no longer renders the ComingSoon placeholder (Sprint 57.72 wire-in).
    expect(screen.queryByTestId("inspector-tab-coming-soon-tree")).toBeNull();
  });

  test("Switch to Tree tab → InspectorTree renders root + 2 children with status + summary rows", async () => {
    useChatStore.setState({
      subagents: [
        makeSubagent({ subagentId: "sa-root", parentId: "chat-1", mode: "fork", status: "running" }),
        makeSubagent({
          subagentId: "child-a",
          parentId: "sa-root",
          mode: "teammate",
          status: "completed",
          summary: "scanned logs",
          tokensUsed: 1200,
        }),
        makeSubagent({
          subagentId: "child-b",
          parentId: "sa-root",
          mode: "teammate",
          status: "completed",
          summary: "checked deps",
          tokensUsed: 800,
        }),
      ],
    });
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Tree" }));

    expect(screen.getByTestId("inspector-tree")).toBeInTheDocument();
    // node rows (names) + nesting
    expect(screen.getByTestId("inspector-tree-node-sa-root")).toBeInTheDocument();
    const childA = screen.getByTestId("inspector-tree-node-child-a");
    expect(childA).toBeInTheDocument();
    expect(screen.getByTestId("inspector-tree-node-child-b")).toBeInTheDocument();
    // status labels
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getAllByText("completed").length).toBe(2);
    // summary rows: Depth (root + children = 2), Concurrency (1 running), Tokens (1200+800 = 2,000)
    expect(screen.getByText("Depth")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Concurrency")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("Tokens (subtree)")).toBeInTheDocument();
    expect(screen.getByText("2,000")).toBeInTheDocument();
    // no ComingSoon placeholder
    expect(screen.queryByTestId("inspector-tab-coming-soon-tree")).toBeNull();
  });

  test("Switch to Tree tab → a node with childEvents renders the child's per-turn TAO rows (Sprint 57.96)", async () => {
    useChatStore.setState({
      subagents: [
        makeSubagent({
          subagentId: "sa-root",
          parentId: "chat-1",
          mode: "fork",
          status: "running",
          childEvents: [
            { kind: "turn_start", turn: 1 },
            { kind: "llm_response", text: "child says hi" },
            { kind: "tool_call_request", toolName: "echo", toolCallId: "c1" },
          ],
        }),
      ],
    });
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Tree" }));

    // the child's per-turn TAO events render as nested rows under the node
    expect(screen.getAllByTestId("inspector-tree-child-event")).toHaveLength(3);
    expect(screen.getByText("turn 1")).toBeInTheDocument();
    expect(screen.getByText("LLM · child says hi")).toBeInTheDocument();
    expect(screen.getByText("→ echo()")).toBeInTheDocument();
  });

  test("Switch to Tree tab → a node with empty childEvents renders no child-event rows (collapsed preserved)", async () => {
    useChatStore.setState({
      subagents: [
        makeSubagent({ subagentId: "sa-solo", parentId: "chat-1", mode: "fork", status: "running" }),
      ],
    });
    const user = userEvent.setup();
    render(<ChatInspector />);
    await user.click(screen.getByRole("tab", { name: "Tree" }));

    expect(screen.getByTestId("inspector-tree-node-sa-solo")).toBeInTheDocument();
    expect(screen.queryAllByTestId("inspector-tree-child-event")).toHaveLength(0);
  });

  test("All 4 tabs render in tablist with correct aria-selected default Turn=true", () => {
    render(<ChatInspector />);
    const turnTab = screen.getByRole("tab", { name: "Turn" });
    const traceTab = screen.getByRole("tab", { name: "Trace" });
    const memoryTab = screen.getByRole("tab", { name: "Memory" });
    const treeTab = screen.getByRole("tab", { name: "Tree" });
    expect(turnTab.getAttribute("aria-selected")).toBe("true");
    expect(traceTab.getAttribute("aria-selected")).toBe("false");
    expect(memoryTab.getAttribute("aria-selected")).toBe("false");
    expect(treeTab.getAttribute("aria-selected")).toBe("false");
  });
});
