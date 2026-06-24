/**
 * File: frontend/tests/unit/chat_v2/components/inspector/InspectorTodos.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.140 InspectorTodos (task primitive panel).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.140 (research #1 — explicit task primitive Todos tab)
 *
 * Created: 2026-06-24 (Sprint 57.140)
 *
 * Modification History:
 *   - 2026-06-24: Initial creation (Sprint 57.140) — empty / rows / status badges / count
 */

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import { InspectorTodos } from "@/features/chat_v2/components/inspector/InspectorTodos";
import { useChatStore } from "@/features/chat_v2/store/chatStore";
import type { TodoItem } from "@/features/chat_v2/store/chatStore";

function makeTodo(overrides: Partial<TodoItem> = {}): TodoItem {
  return {
    id: "1",
    title: "Research the topic",
    status: "pending",
    ...overrides,
  };
}

describe("InspectorTodos (Sprint 57.140)", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });
  afterEach(() => {
    useChatStore.getState().reset();
  });

  test("honest empty state when no plan (single-step session)", () => {
    render(<InspectorTodos />);
    expect(screen.getByTestId("inspector-todos-empty")).toBeInTheDocument();
    expect(
      screen.getByText("no plan yet — the agent writes one for multi-step tasks"),
    ).toBeInTheDocument();
  });

  test("renders one row per todo with status badge + title", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "1", title: "Gather requirements", status: "completed" }),
        makeTodo({ id: "2", title: "Write code", status: "in_progress" }),
        makeTodo({ id: "3", title: "Run tests", status: "pending" }),
      ],
    });
    render(<InspectorTodos />);
    expect(screen.getByTestId("inspector-todos")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-todo-0")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-todo-1")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-todo-2")).toBeInTheDocument();
    expect(screen.getByText("Gather requirements")).toBeInTheDocument();
    expect(screen.getByText("Run tests")).toBeInTheDocument();
  });

  test("status badges use the existing mockup .badge tone classes (no new CSS)", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "1", title: "done", status: "completed" }),
        makeTodo({ id: "2", title: "doing", status: "in_progress" }),
        makeTodo({ id: "3", title: "todo", status: "pending" }),
      ],
    });
    render(<InspectorTodos />);
    const completed = screen.getByText("completed");
    const inProgress = screen.getByText("in_progress");
    const pending = screen.getByText("pending");
    expect(completed.className).toContain("badge");
    expect(completed.className).toContain("success");
    expect(inProgress.className).toContain("badge");
    expect(inProgress.className).toContain("info");
    // pending → bare badge (no tone modifier)
    expect(pending.className).toBe("badge");
  });

  test("shows the completed/total count summary", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "1", status: "completed" }),
        makeTodo({ id: "2", status: "completed" }),
        makeTodo({ id: "3", status: "pending" }),
      ],
    });
    render(<InspectorTodos />);
    expect(screen.getByText("2/3 completed")).toBeInTheDocument();
  });
});
