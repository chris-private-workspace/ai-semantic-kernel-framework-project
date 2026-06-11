/**
 * File: frontend/tests/unit/chat_v2/components/inspector/InspectorTree.inject.test.tsx
 * Purpose: Vitest coverage for the Sprint 57.103 (B2b) inject-to-teammate control in InspectorTree.
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57 / Sprint 57.103 (B2b)
 *
 * Description:
 *   The inject control shows ONLY on a RUNNING teammate node in real_llm mode with a live
 *   session (no dead control — echo runs spawn no real teammate; a fork / completed node
 *   has nothing to inject). Clicking it calls injectToSubagent(sessionId, subagentId, msg).
 *
 * Created: 2026-06-11 (Sprint 57.103 B2b)
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import InspectorTree from "@/features/chat_v2/components/inspector/InspectorTree";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { ChatMode } from "@/features/chat_v2/types";
import type { SubagentNode } from "@/features/subagent/types";

const { injectSpy } = vi.hoisted(() => ({
  injectSpy: vi.fn(() => Promise.resolve()),
}));

vi.mock("@/features/chat_v2/services/chatService", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/features/chat_v2/services/chatService")>();
  return { ...actual, injectToSubagent: injectSpy };
});

function node(overrides: Partial<SubagentNode> = {}): SubagentNode {
  return {
    subagentId: "tm-1",
    parentId: "chat-1",
    mode: "teammate",
    status: "running",
    summary: null,
    tokensUsed: null,
    spawnedAt: Date.now(),
    childEvents: [],
    ...overrides,
  };
}

function seed(opts: {
  nodes: SubagentNode[];
  mode?: ChatMode;
  sessionId?: string | null;
}): void {
  useChatStore.setState({
    subagents: opts.nodes,
    mode: opts.mode ?? "real_llm",
    sessionId: opts.sessionId === undefined ? "sess-1" : opts.sessionId,
  });
}

describe("InspectorTree inject-to-teammate control (Sprint 57.103 B2b)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
    injectSpy.mockClear();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("running teammate node in real_llm shows the inject control", () => {
    seed({ nodes: [node()] });
    render(<InspectorTree />);
    expect(screen.getByTestId("teammate-inject-tm-1")).toBeInTheDocument();
    expect(screen.getByTestId("teammate-inject-input-tm-1")).toBeInTheDocument();
  });

  test("fork node does NOT show the inject control", () => {
    seed({ nodes: [node({ mode: "fork" })] });
    render(<InspectorTree />);
    expect(screen.queryByTestId("teammate-inject-tm-1")).toBeNull();
  });

  test("completed teammate does NOT show the inject control", () => {
    seed({ nodes: [node({ status: "completed", summary: "done" })] });
    render(<InspectorTree />);
    expect(screen.queryByTestId("teammate-inject-tm-1")).toBeNull();
  });

  test("echo mode does NOT show the inject control (no dead control)", () => {
    seed({ nodes: [node()], mode: "echo_demo" });
    render(<InspectorTree />);
    expect(screen.queryByTestId("teammate-inject-tm-1")).toBeNull();
  });

  test("no live session does NOT show the inject control", () => {
    seed({ nodes: [node()], sessionId: null });
    render(<InspectorTree />);
    expect(screen.queryByTestId("teammate-inject-tm-1")).toBeNull();
  });

  test("clicking inject calls injectToSubagent(sessionId, subagentId, message)", async () => {
    seed({ nodes: [node()], sessionId: "sess-9" });
    const user = userEvent.setup();
    render(<InspectorTree />);
    await user.type(
      screen.getByTestId("teammate-inject-input-tm-1"),
      "check the db pool",
    );
    await user.click(screen.getByTestId("teammate-inject-send-tm-1"));
    expect(injectSpy).toHaveBeenCalledWith("sess-9", "tm-1", "check the db pool");
  });
});
