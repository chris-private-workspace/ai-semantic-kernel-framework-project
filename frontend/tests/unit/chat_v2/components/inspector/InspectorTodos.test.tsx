/**
 * File: frontend/tests/unit/chat_v2/components/inspector/InspectorTodos.test.tsx
 * Purpose: Vitest render coverage for Sprint 57.140 InspectorTodos (task primitive panel).
 * Category: Frontend / tests / unit / chat_v2
 * Scope: Phase 57.140 (research #1 — explicit task primitive Todos tab)
 *
 * Created: 2026-06-24 (Sprint 57.140)
 *
 * Modification History:
 *   - 2026-07-08: Sprint 57.162 — DAG viz graph render / no-graph-for-flat / cycle-marker coverage
 *   - 2026-07-01: Sprint 57.156 — DAG: blocked badge + "⤷ needs" deps line coverage
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

  test("Sprint 57.156 DAG: a blocked pending todo shows a 'blocked' badge + '⤷ needs' line", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "a", title: "Design schema", status: "pending" }),
        makeTodo({ id: "b", title: "Write migration", status: "pending", depends_on: ["a"] }),
      ],
    });
    render(<InspectorTodos />);
    // b (index 1) is blocked on a (still pending)
    expect(screen.getByTestId("inspector-todo-blocked-1")).toBeInTheDocument();
    expect(screen.getByTestId("inspector-todo-deps-1")).toHaveTextContent("needs: Design schema");
    // a (index 0) has no deps → no badge / no needs line
    expect(screen.queryByTestId("inspector-todo-blocked-0")).not.toBeInTheDocument();
    expect(screen.queryByTestId("inspector-todo-deps-0")).not.toBeInTheDocument();
  });

  test("Sprint 57.156 DAG: deps completed → '⤷ needs' line but NO blocked badge (ready)", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "a", title: "Design schema", status: "completed" }),
        makeTodo({ id: "b", title: "Write migration", status: "pending", depends_on: ["a"] }),
      ],
    });
    render(<InspectorTodos />);
    expect(screen.queryByTestId("inspector-todo-blocked-1")).not.toBeInTheDocument();
    expect(screen.getByTestId("inspector-todo-deps-1")).toHaveTextContent("needs: Design schema");
  });

  test("Sprint 57.156 DAG: the blocked badge reuses the mockup .badge class (no new CSS)", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "a", title: "x", status: "pending" }),
        makeTodo({ id: "b", title: "y", status: "pending", depends_on: ["a"] }),
      ],
    });
    render(<InspectorTodos />);
    const blocked = screen.getByTestId("inspector-todo-blocked-1");
    expect(blocked.className).toBe("badge");
    expect(blocked).toHaveTextContent("blocked");
  });

  test("Sprint 57.162 DAG viz: a plan with deps renders the node-link graph + edges", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "a", title: "Design schema", status: "completed" }),
        makeTodo({ id: "b", title: "Write migration", status: "pending", depends_on: ["a"] }),
        makeTodo({ id: "c", title: "Run tests", status: "pending", depends_on: ["b"] }),
      ],
    });
    render(<InspectorTodos />);
    expect(screen.getByTestId("todo-dag-graph")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-node-a")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-node-b")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-node-c")).toBeInTheDocument();
    // edges point from each prerequisite to its dependent
    expect(screen.getByTestId("todo-dag-edge-a-b")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-edge-b-c")).toBeInTheDocument();
    // the flat list is retained below the graph (a11y / text fallback)
    expect(screen.getByTestId("inspector-todos")).toBeInTheDocument();
    expect(screen.getByText("Design schema")).toBeInTheDocument(); // unique to the flat list
  });

  test("Sprint 57.162 DAG viz: NO graph for a flat (no-dependency) plan", () => {
    useChatStore.setState({
      todos: [makeTodo({ id: "1", title: "a" }), makeTodo({ id: "2", title: "b" })],
    });
    render(<InspectorTodos />);
    expect(screen.queryByTestId("todo-dag-graph")).not.toBeInTheDocument();
  });

  test("Sprint 57.162 DAG viz: cyclic nodes carry a cycle marker + dashed cycle edge", () => {
    useChatStore.setState({
      todos: [
        makeTodo({ id: "a", title: "A", status: "pending", depends_on: ["b"] }),
        makeTodo({ id: "b", title: "B", status: "pending", depends_on: ["a"] }),
      ],
    });
    render(<InspectorTodos />);
    expect(screen.getByTestId("todo-dag-graph")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-cycle-node-a")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-cycle-node-b")).toBeInTheDocument();
    expect(screen.getByTestId("todo-dag-edge-b-a")).toBeInTheDocument();
  });
});
