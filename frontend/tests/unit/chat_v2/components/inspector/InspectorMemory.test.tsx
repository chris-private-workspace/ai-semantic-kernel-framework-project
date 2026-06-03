/**
 * File: frontend/tests/unit/chat_v2/components/inspector/InspectorMemory.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.75 InspectorMemory (memory ops list).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.75 (A-5 Inspector Memory tab)
 *
 * Created: 2026-06-03 (Sprint 57.75)
 *
 * Modification History:
 *   - 2026-06-03: Initial creation (Sprint 57.75) — empty / ops render / scope+timeScale / key=summary
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { InspectorMemory } from "@/features/chat_v2/components/inspector/InspectorMemory";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { MemoryOp } from "@/features/chat_v2/store/chatStore";

function makeOp(overrides: Partial<MemoryOp> = {}): MemoryOp {
  return {
    op: "READ",
    scope: "user",
    timeScale: "permanent",
    key: "preferences.rca_format",
    summary: "5-whys + timeline",
    at: new Date("2026-06-03T10:42:24").getTime(),
    ...overrides,
  };
}

describe("InspectorMemory (Sprint 57.75)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("honest empty state when no memory ops (echo_demo session)", () => {
    render(<InspectorMemory />);
    expect(screen.getByTestId("inspector-memory-empty")).toBeInTheDocument();
    expect(screen.getByText("no memory accesses this session")).toBeInTheDocument();
  });

  test("renders one row per memory op with op badge + key = summary line", () => {
    useChatStore.setState({ memoryOps: [makeOp()] });
    render(<InspectorMemory />);
    expect(screen.getByTestId("inspector-memory")).toBeInTheDocument();
    const row = screen.getByTestId("inspector-memory-op-0");
    expect(row).toBeInTheDocument();
    expect(screen.getByText("READ")).toBeInTheDocument();
    // Key + summary share a div with the "=" separator span, so the key/summary
    // text nodes are split — assert against the row's combined textContent.
    expect(row.textContent).toContain("preferences.rca_format");
    expect(row.textContent).toContain("5-whys + timeline");
  });

  test("scope row appends time_scale (memory 雙軸)", () => {
    useChatStore.setState({ memoryOps: [makeOp({ scope: "tenant", timeScale: "quarterly" })] });
    render(<InspectorMemory />);
    expect(screen.getByText("tenant · quarterly")).toBeInTheDocument();
  });

  test("scope without time_scale shows bare scope (no trailing separator)", () => {
    useChatStore.setState({ memoryOps: [makeOp({ scope: "session", timeScale: "" })] });
    render(<InspectorMemory />);
    expect(screen.getByText("session")).toBeInTheDocument();
  });

  test("op badge uses verbatim mockup .badge.memory class (not shadcn Badge)", () => {
    useChatStore.setState({ memoryOps: [makeOp({ op: "WRITE" })] });
    render(<InspectorMemory />);
    const badge = screen.getByText("WRITE");
    expect(badge.className).toContain("badge");
    expect(badge.className).toContain("memory");
  });

  test("multiple ops render in arrival order", () => {
    useChatStore.setState({
      memoryOps: [
        makeOp({ key: "k1", op: "READ" }),
        makeOp({ key: "k2", op: "WRITE" }),
      ],
    });
    render(<InspectorMemory />);
    expect(screen.getByTestId("inspector-memory-op-0")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-memory-op-1")).toBeInTheDocument();
  });

  test("timestamp formatted HH:MM:SS from client at epoch", () => {
    useChatStore.setState({
      memoryOps: [makeOp({ at: new Date("2026-06-03T09:05:07").getTime() })],
    });
    render(<InspectorMemory />);
    expect(screen.getByText("09:05:07")).toBeInTheDocument();
  });
});
