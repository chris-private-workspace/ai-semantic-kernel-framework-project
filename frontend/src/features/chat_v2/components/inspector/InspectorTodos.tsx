/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx
 * Purpose: Inspector "Todos" tab — renders the agent's durable structured plan (task primitive).
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.140 (research #1 — explicit task primitive; consumes todos_updated SSE)
 *
 * Description:
 *   The visibility half of the explicit task primitive (CC `TodoWrite`-like). Reads
 *   the chatStore.todos slice (populated by the `todos_updated` SSE branch when the
 *   agent calls write_todos). One bordered row per todo: a status `.badge`
 *   (completed → success / in_progress → info / pending → base) + the title.
 *
 *   NOTE (mockup fidelity): the reference mockup (page-chat.jsx) predates this
 *   feature and has NO todos surface — this is a NEW 5th Inspector tab for a backend
 *   feature the mockup doesn't cover. It consumes ONLY existing mockup CSS classes
 *   (.badge / .badge.success / .badge.info / var(--*) tokens) so styles-mockup.css is
 *   UNTOUCHED (no new CSS / no oklch literals) — the fidelity diff stays empty. The
 *   row/empty-state structure mirrors the sibling InspectorMemory tab verbatim.
 *
 *   Honest empty state: until the agent writes a plan (single-step requests never
 *   do), the tab shows "no plan yet", NOT a fabricated row (AP-4).
 *
 *   Sprint 57.156 (DAG): when a todo declares depends_on, the row shows a "⤷ needs"
 *   line + a "blocked" badge (a pending todo whose known deps aren't all completed),
 *   mirroring the backend ready_todos rule. Reuses the same .badge / var(--*) classes
 *   (styles-mockup.css still UNTOUCHED).
 *
 *   Pure read; no side effects.
 *
 * Key Components:
 *   - InspectorTodos: tab component reading useChatStore((s) => s.todos)
 *   - statusBadgeClass(): TodoItem status → mockup .badge tone class
 *
 * Created: 2026-06-24 (Sprint 57.140)
 * Last Modified: 2026-07-01
 *
 * Modification History (newest-first):
 *   - 2026-07-01: Sprint 57.156 — render depends_on ("⤷ needs") + blocked badge (DAG)
 *   - 2026-06-24: Initial creation (Sprint 57.140) — research #1 task-primitive Todos tab
 *
 * Related:
 *   - ../../store/chatStore.ts (todos slice + TodoItem + todos_updated branch)
 *   - ./InspectorMemory.tsx (sibling wired tab — empty-state + verbatim-class pattern)
 *   - frontend/src/styles-mockup.css (.badge / .badge.success / .badge.info / .subtle)
 */

/* eslint-disable no-restricted-syntax -- mirrors the sibling InspectorMemory tab's
   verbatim inline-style pattern (section header + per-row padding/borderBottom/font);
   all colors via var(--*) tokens, no literals. */

import { useChatStore } from "../../store/chatStore";
import type { TodoItem } from "../../store/chatStore";

/** Map a todo status to the existing mockup .badge tone class (no new CSS). */
function statusBadgeClass(status: TodoItem["status"]): string {
  if (status === "completed") return "badge success";
  if (status === "in_progress") return "badge info";
  return "badge";
}

function TodoRow({
  todo,
  index,
  blocked,
  depTitles,
}: {
  todo: TodoItem;
  index: number;
  blocked: boolean;
  depTitles: string[];
}): JSX.Element {
  return (
    <div
      data-testid={`inspector-todo-${index}`}
      style={{
        padding: "7px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: 11,
        fontFamily: "var(--font-mono)",
      }}
    >
      <div className="row" style={{ gap: 6 }}>
        <span className={statusBadgeClass(todo.status)}>{todo.status}</span>
        {blocked && (
          <span data-testid={`inspector-todo-blocked-${index}`} className="badge">
            blocked
          </span>
        )}
        <span style={{ color: "var(--fg)" }}>{todo.title}</span>
      </div>
      {depTitles.length > 0 && (
        <div
          data-testid={`inspector-todo-deps-${index}`}
          style={{ marginTop: 3, color: "var(--fg-muted)", fontSize: 10 }}
        >
          ⤷ needs: {depTitles.join(", ")}
        </div>
      )}
    </div>
  );
}

export function InspectorTodos(): JSX.Element {
  const todos = useChatStore((s) => s.todos);

  const header = (
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
      Plan · this session
    </div>
  );

  if (todos.length === 0) {
    return (
      <div
        data-testid="inspector-todos-empty"
        style={{ padding: "12px 16px", fontSize: 12, color: "var(--fg-muted)" }}
      >
        {header}
        <p style={{ marginTop: 8, lineHeight: 1.55 }}>
          no plan yet — the agent writes one for multi-step tasks
        </p>
      </div>
    );
  }

  const completed = todos.filter((t) => t.status === "completed").length;

  // Sprint 57.156 DAG: mirror the backend ready rule (agent_harness ready_todos) —
  // a pending todo is "blocked" iff any KNOWN dependency is not yet completed;
  // an unknown dep id is ignored (no permanent deadlock). Titles resolve deps for
  // the "⤷ needs" line; an unknown id falls back to the raw id.
  const completedIds = new Set(todos.filter((t) => t.status === "completed").map((t) => t.id));
  const titleById = new Map(todos.map((t) => [t.id, t.title]));

  return (
    <div data-testid="inspector-todos" style={{ padding: "12px 16px" }}>
      {header}
      <div className="subtle" style={{ marginBottom: 8 }}>
        {completed}/{todos.length} completed
      </div>
      {todos.map((todo, i) => {
        const deps = todo.depends_on ?? [];
        const blocked =
          todo.status === "pending" &&
          deps.some((d) => titleById.has(d) && !completedIds.has(d));
        const depTitles = deps.map((d) => titleById.get(d) ?? d);
        return (
          <TodoRow
            key={todo.id || i}
            todo={todo}
            index={i}
            blocked={blocked}
            depTitles={depTitles}
          />
        );
      })}
    </div>
  );
}

export default InspectorTodos;
