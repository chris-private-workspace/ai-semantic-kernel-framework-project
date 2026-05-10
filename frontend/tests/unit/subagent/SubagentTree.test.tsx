/**
 * File: frontend/tests/unit/subagent/SubagentTree.test.tsx
 * Purpose: Vitest tests for SubagentTree component — null when empty + node rendering + parent→child nesting + status display.
 * Category: Frontend / tests / unit / subagent
 * Scope: Phase 57 / Sprint 57.12 Day 3 / US-6
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 3 / US-6)
 *
 * Modification History:
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 3 / US-6)
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { LoopEvent } from "@/features/chat_v2/types";
import { SubagentTree } from "@/features/subagent/components/SubagentTree";

function feed(events: LoopEvent[]): void {
  const merge = useChatStore.getState().mergeEvent;
  for (const ev of events) merge(ev);
}

describe("SubagentTree (Sprint 57.12 US-6)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("renders null when no subagents", () => {
    const { container } = render(<SubagentTree />);
    expect(container.firstChild).toBeNull();
  });

  test("renders a running node after subagent_spawned", () => {
    feed([
      {
        type: "subagent_spawned",
        data: { subagent_id: "sa-aaaaaaaa", mode: "fork", parent_session_id: "chat-1" },
      },
    ]);
    render(<SubagentTree />);
    expect(screen.getByTestId("subagent-tree")).toBeInTheDocument();
    expect(screen.getByTestId("subagent-node-sa-aaaaaaaa")).toBeInTheDocument();
    expect(screen.getByTestId("subagent-status-badge-running")).toBeInTheDocument();
    // header shows running count
    expect(screen.getByText(/1 running/i)).toBeInTheDocument();
  });

  test("renders completed node with tokens + summary snippet after subagent_completed", () => {
    feed([
      {
        type: "subagent_spawned",
        data: { subagent_id: "sa-bbbbbbbb", mode: "fork", parent_session_id: "chat-1" },
      },
      {
        type: "subagent_completed",
        data: { subagent_id: "sa-bbbbbbbb", summary: "Did the thing", tokens_used: 120 },
      },
    ]);
    render(<SubagentTree />);
    expect(screen.getByTestId("subagent-status-badge-completed")).toBeInTheDocument();
    expect(screen.getByText(/120 tok/i)).toBeInTheDocument();
    expect(screen.getByText(/Did the thing/i)).toBeInTheDocument();
  });

  test("nests a child subagent under its parent subagent (depth ≥ 2)", () => {
    feed([
      {
        type: "subagent_spawned",
        data: { subagent_id: "parent-1", mode: "fork", parent_session_id: "chat-1" },
      },
      {
        // child's parent_session_id is the PARENT SUBAGENT's id → nested
        type: "subagent_spawned",
        data: { subagent_id: "child-1", mode: "teammate", parent_session_id: "parent-1" },
      },
    ]);
    render(<SubagentTree />);
    const parentNode = screen.getByTestId("subagent-node-parent-1");
    const childNode = screen.getByTestId("subagent-node-child-1");
    // child node is rendered INSIDE the parent node's subtree
    expect(parentNode).toContainElement(childNode);
  });

  test("hides header running-count suffix when all nodes completed", () => {
    feed([
      {
        type: "subagent_spawned",
        data: { subagent_id: "sa-cccccccc", mode: "fork", parent_session_id: "chat-1" },
      },
      {
        type: "subagent_completed",
        data: { subagent_id: "sa-cccccccc", summary: "ok", tokens_used: 1 },
      },
    ]);
    render(<SubagentTree />);
    expect(screen.getByText(/Subagents \(1\)/)).toBeInTheDocument();
    expect(screen.queryByText(/running/i)).toBeNull();
  });
});
