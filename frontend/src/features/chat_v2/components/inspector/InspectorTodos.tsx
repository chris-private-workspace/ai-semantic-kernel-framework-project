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
 *   Sprint 57.162 (DAG viz): when ANY todo declares a dependency, an inline
 *   TodoDagGraph renders ABOVE the flat list — a leveled (longest-path) node-link
 *   diagram: fixed-size circular nodes coloured by status/blocked/cycle via existing
 *   var(--*) tokens (--success/--info/--warning/--danger/--border-strong), numbered
 *   1..N (aria-label carries the full title so getByText stays unique to the flat
 *   list), edges = SVG lines in var(--border) (a cycle edge is dashed var(--danger)).
 *   A cycle is detected locally (detectCyclesTs mirrors the backend detect_cycles).
 *   No new CSS / no oklch literal → styles-mockup.css byte-identical. The flat list
 *   below is retained as the textual / a11y fallback.
 *
 *   Pure read; no side effects.
 *
 * Key Components:
 *   - InspectorTodos: tab component reading useChatStore((s) => s.todos)
 *   - statusBadgeClass(): TodoItem status → mockup .badge tone class
 *   - TodoDagGraph(): inline leveled node-link DAG viz (Sprint 57.162)
 *   - detectCyclesTs(): local cycle detection mirroring backend detect_cycles
 *
 * Created: 2026-06-24 (Sprint 57.140)
 * Last Modified: 2026-07-08
 *
 * Modification History (newest-first):
 *   - 2026-07-08: Sprint 57.162 — inline TodoDagGraph (leveled node-link) + cycle marker (DAG viz)
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

/** Local cycle detection mirroring the backend `detect_cycles` (known-deps only). */
function detectCyclesTs(todos: TodoItem[], knownIds: Set<string>): Set<string> {
  const adj = new Map<string, string[]>();
  for (const t of todos) {
    if (!adj.has(t.id)) {
      adj.set(
        t.id,
        (t.depends_on ?? []).filter((d) => knownIds.has(d) && d !== t.id),
      );
    }
  }
  const WHITE = 0;
  const GREY = 1;
  const BLACK = 2;
  const color = new Map<string, number>();
  adj.forEach((_deps, id) => color.set(id, WHITE));
  const cyclic = new Set<string>();
  const path: string[] = [];
  const visit = (node: string): void => {
    color.set(node, GREY);
    path.push(node);
    for (const dep of adj.get(node) ?? []) {
      const c = color.get(dep) ?? BLACK;
      if (c === GREY) {
        for (let i = path.indexOf(dep); i < path.length; i += 1) cyclic.add(path[i]);
      } else if (c === WHITE) {
        visit(dep);
      }
    }
    path.pop();
    color.set(node, BLACK);
  };
  adj.forEach((_deps, id) => {
    if (color.get(id) === WHITE) visit(id);
  });
  return cyclic;
}

const DAG_NODE = 26; // node diameter (px)
const DAG_COL_W = 92; // horizontal gap between dependency levels
const DAG_ROW_H = 40; // vertical gap between nodes in a level
const DAG_PAD = 14;

/** Border colour for a graph node — status, then blocked/cycle overrides (var(--*) only). */
function dagNodeColor(status: TodoItem["status"], blocked: boolean, cyclic: boolean): string {
  if (cyclic) return "var(--danger)";
  if (status === "completed") return "var(--success)";
  if (status === "in_progress") return "var(--info)";
  if (blocked) return "var(--warning)";
  return "var(--border-strong)"; // ready pending
}

/**
 * Inline leveled node-link DAG viz (Sprint 57.162). Nodes are placed by longest-path
 * dependency level (a cycle back-edge is guarded to level 0 so layout terminates);
 * edges are SVG lines to each known prerequisite. Reuses existing var(--*) tokens
 * only — no new CSS, no oklch literal. Rendered only when the plan has a dependency.
 */
function TodoDagGraph({ todos }: { todos: TodoItem[] }): JSX.Element {
  const knownIds = new Set(todos.map((t) => t.id));
  const depsById = new Map(
    todos.map((t) => [t.id, (t.depends_on ?? []).filter((d) => knownIds.has(d) && d !== t.id)]),
  );
  const completedIds = new Set(todos.filter((t) => t.status === "completed").map((t) => t.id));
  const cyclic = detectCyclesTs(todos, knownIds);
  const numberById = new Map(todos.map((t, i) => [t.id, i + 1]));

  // longest-path level per node, with a cycle guard (a re-entered node contributes 0).
  const level = new Map<string, number>();
  const visiting = new Set<string>();
  const levelOf = (id: string): number => {
    const memo = level.get(id);
    if (memo !== undefined) return memo;
    if (visiting.has(id)) return 0;
    visiting.add(id);
    let m = 0;
    for (const d of depsById.get(id) ?? []) m = Math.max(m, 1 + levelOf(d));
    visiting.delete(id);
    level.set(id, m);
    return m;
  };
  todos.forEach((t) => levelOf(t.id));

  const byLevel = new Map<number, TodoItem[]>();
  for (const t of todos) {
    const lvl = level.get(t.id) ?? 0;
    byLevel.set(lvl, [...(byLevel.get(lvl) ?? []), t]);
  }
  const pos = new Map<string, { x: number; y: number }>();
  byLevel.forEach((arr, lvl) => {
    arr.forEach((t, row) => {
      pos.set(t.id, { x: DAG_PAD + lvl * DAG_COL_W, y: DAG_PAD + row * DAG_ROW_H });
    });
  });
  const maxLevel = Math.max(0, ...byLevel.keys());
  const maxRows = Math.max(1, ...[...byLevel.values()].map((a) => a.length));
  const width = DAG_PAD * 2 + maxLevel * DAG_COL_W + DAG_NODE;
  const height = DAG_PAD * 2 + (maxRows - 1) * DAG_ROW_H + DAG_NODE;
  const c = DAG_NODE / 2;

  return (
    <div
      data-testid="todo-dag-graph"
      style={{ position: "relative", width, height, margin: "2px 0 12px", overflowX: "auto" }}
    >
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
        aria-hidden="true"
      >
        {todos.flatMap((t) =>
          (depsById.get(t.id) ?? []).map((d) => {
            const from = pos.get(d);
            const to = pos.get(t.id);
            if (!from || !to) return null;
            const cycleEdge = cyclic.has(t.id) && cyclic.has(d);
            return (
              <line
                key={`${d}-${t.id}`}
                data-testid={`todo-dag-edge-${d}-${t.id}`}
                x1={from.x + c}
                y1={from.y + c}
                x2={to.x + c}
                y2={to.y + c}
                stroke={cycleEdge ? "var(--danger)" : "var(--border)"}
                strokeWidth={1.5}
                strokeDasharray={cycleEdge ? "3 3" : undefined}
              />
            );
          }),
        )}
      </svg>
      {todos.map((t) => {
        const p = pos.get(t.id);
        if (!p) return null;
        const deps = depsById.get(t.id) ?? [];
        const blocked = t.status === "pending" && deps.some((d) => !completedIds.has(d));
        const isCycle = cyclic.has(t.id);
        const border = dagNodeColor(t.status, blocked, isCycle);
        return (
          <span
            key={t.id}
            data-testid={`todo-dag-node-${t.id}`}
            aria-label={`${numberById.get(t.id)}. ${t.title} (${isCycle ? "cycle" : blocked ? "blocked" : t.status})`}
            title={t.title}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              width: DAG_NODE,
              height: DAG_NODE,
              borderRadius: "50%",
              border: `2px ${isCycle ? "dashed" : "solid"} ${border}`,
              background: "var(--bg)",
              color: "var(--fg)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              boxSizing: "border-box",
            }}
          >
            {numberById.get(t.id)}
            {isCycle && (
              <i
                data-testid={`todo-dag-cycle-node-${t.id}`}
                aria-hidden="true"
                style={{ display: "none" }}
              />
            )}
          </span>
        );
      })}
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
  // Sprint 57.162: the DAG viz only adds value once a dependency exists; a flat
  // (no-dep) plan keeps the Sprint 57.140/156 list-only rendering unchanged.
  const hasDeps = todos.some((t) => (t.depends_on ?? []).length > 0);

  return (
    <div data-testid="inspector-todos" style={{ padding: "12px 16px" }}>
      {header}
      <div className="subtle" style={{ marginBottom: 8 }}>
        {completed}/{todos.length} completed
      </div>
      {hasDeps && <TodoDagGraph todos={todos} />}
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
