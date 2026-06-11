/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorTree.tsx
 * Purpose: Inspector "Tree" tab — verbatim mockup re-point of page-chat.jsx L489-531 (Subagent tree).
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.72 (A-5c Inspector UI — Subagent Tree tab; Tree tab only)
 *
 * Description:
 *   Mockup L489-531 (InspectorTree): section header "Subagent tree · live";
 *   a `.subagent-tree` of root `.subagent-row`s with `.indent`-nested children
 *   (each row: lucide icon + name + status Badge); a `.thin-rule`; then a
 *   `.col` of 4 `.spread` summary rows — Mode / Depth / Concurrency / Tokens.
 *
 *   Reads the existing chatStore.subagents slice (Sprint 57.12; populated by the
 *   subagent_spawned / subagent_completed SSE branches). buildTree() folds the
 *   flat SubagentNode[] into a forest by parentId (roots = nodes whose parentId
 *   is the dispatching session, i.e. not another known subagent); a visited set
 *   guards self-ancestor cycles and the depth is capped for layout safety.
 *
 *   Render-vs-placeholder (Phase 57.72 D5): no concurrency `max`, so Concurrency
 *   shows the running-count only (NOT a fabricated "running / max"). Per the
 *   InspectorTurn "—" convention, an all-null token subtree renders "—". Nothing
 *   is fabricated (AP-4). Sprint 57.96 (Scope B): SubagentNode now carries
 *   `childEvents` (the child loop's per-turn TAO subset), rendered as nested
 *   `.subagent-row`s inside the node's `.indent` (the node "expands"); the
 *   mockup's "· Nt" summary suffix stays deferred polish. The Depth summary still
 *   counts subagent nesting only (child-turn rows are not subagents).
 *
 *   Mostly read; the Sprint 57.103 (B2b) inject-to-teammate control on a RUNNING
 *   teammate node is the one side effect (POST /chat/{id}/subagents/{sid}/inject).
 *   Empty state when subagents slice is empty.
 *
 * Key Components:
 *   - InspectorTree: tab component reading useChatStore((s) => s.subagents)
 *   - buildTree(): flat SubagentNode[] → RenderNode forest (parentId nesting, cycle-guarded)
 *   - NodeRow: one `.subagent-row` + recursive `.indent` children + childEvents rows
 *   - ChildTurnRow: one child-loop TAO event as a nested `.subagent-row` (Sprint 57.96)
 *   - TeammateInjectControl: inject-to-teammate input on a running teammate node (Sprint 57.103 B2b)
 *
 * Created: 2026-06-03 (Sprint 57.72)
 * Last Modified: 2026-06-11
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Sprint 57.103 B2b — inject-to-teammate control + message_injected child row
 *   - 2026-06-09: Sprint 57.96 — render childEvents as nested rows (Scope B turn-stream)
 *   - 2026-06-03: Initial creation (Sprint 57.72) — A-5c Tree tab verbatim re-point
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L489-531 (InspectorTree)
 *   - frontend/src/styles-mockup.css L900-916 (.subagent-tree/.subagent-row/.indent)
 *   - frontend/src/styles-mockup.css L615+L617+L618+L620 (.spread/.subtle/.grow/.mono) + L1119 (.thin-rule)
 *   - ../../store/chatStore.ts (subagents slice — Sprint 57.12)
 *   - ../../../subagent/types.ts (SubagentNode)
 *   - ./InspectorTurn.tsx (sibling wired tab — empty-state + verbatim-class pattern)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L491
   (section header inline font-size/color/text-transform/letter-spacing/font-family),
   L494-497/L501-504/L513-517 (subagent-row inline name color + Badge marginLeft auto),
   L524 (summary .col inline font-size/color). Colors via var(--*) tokens — not literals.
   Sprint 57.103 B2b: + the TeammateInjectControl input/button inline styles (mockup tokens
   --bg-1/--border/--primary/--danger; the inject-to-teammate control has no mockup design). */

import { useState } from "react";

import { ChevronRight, GitFork, MessageSquare } from "lucide-react";

import { injectToSubagent } from "../../services/chatService";
import { useChatStore } from "../../store/chatStore";
import type { ChildTurnEvent, SubagentNode } from "../../../subagent/types";

// Layout-safety cap: subagent spawning is bounded, but a malformed parentId
// chain could in theory recurse; mirror SubagentTree.tsx MAX_DEPTH.
const MAX_DEPTH = 5;

interface RenderNode {
  node: SubagentNode;
  children: RenderNode[];
  depth: number;
}

/**
 * Fold the flat node list into a forest keyed by parentId.
 * Roots = nodes whose parentId is the dispatching session (i.e. not another
 * known subagent's id). A visited set guards self-ancestor cycles; depth is
 * capped at MAX_DEPTH for layout safety. Mirrors SubagentTree.buildForest.
 */
function buildTree(nodes: SubagentNode[]): RenderNode[] {
  const byId = new Map(nodes.map((n) => [n.subagentId, n]));
  const childrenOf = new Map<string, SubagentNode[]>();
  const roots: SubagentNode[] = [];
  for (const n of nodes) {
    const parentIsKnownSubagent = n.parentId !== null && byId.has(n.parentId);
    if (parentIsKnownSubagent) {
      const arr = childrenOf.get(n.parentId as string) ?? [];
      arr.push(n);
      childrenOf.set(n.parentId as string, arr);
    } else {
      roots.push(n);
    }
  }
  const visited = new Set<string>();
  function expand(node: SubagentNode, depth: number): RenderNode {
    visited.add(node.subagentId);
    if (depth >= MAX_DEPTH) return { node, children: [], depth };
    const kids = (childrenOf.get(node.subagentId) ?? []).filter((c) => !visited.has(c.subagentId));
    return { node, children: kids.map((c) => expand(c, depth + 1)), depth };
  }
  return roots.map((r) => expand(r, 0));
}

/** Max nesting depth across the forest (root = depth 1; matches mockup "Depth: 2"). */
function maxDepth(forest: RenderNode[]): number {
  let max = 0;
  const walk = (rn: RenderNode): void => {
    max = Math.max(max, rn.depth + 1);
    rn.children.forEach(walk);
  };
  forest.forEach(walk);
  return max;
}

/** Most-frequent mode across all nodes (dominant fork shape for the summary row). */
function dominantMode(nodes: SubagentNode[]): string {
  const counts = new Map<string, number>();
  for (const n of nodes) counts.set(n.mode, (counts.get(n.mode) ?? 0) + 1);
  let best = "";
  let bestN = -1;
  for (const [mode, c] of counts) {
    if (c > bestN) {
      best = mode;
      bestN = c;
    }
  }
  return best;
}

function StatusBadge({ status }: { status: SubagentNode["status"] }): JSX.Element {
  // Mockup L497 root row = <Badge tone="warning">; L517 child row = <Badge tone="success" dot>.
  // Map by status: running → warning (live), completed → success + dot.
  if (status === "completed") {
    return <span className="badge success dot">completed</span>;
  }
  return <span className="badge warning">running</span>;
}

/** Human label for one child-loop TAO event row (Sprint 57.96 Scope B). */
function childTurnLabel(ev: ChildTurnEvent): string {
  const clip = (t: string | undefined): string =>
    t && t.length > 48 ? `${t.slice(0, 48)}…` : t ?? "";
  switch (ev.kind) {
    case "turn_start":
      return `turn ${ev.turn ?? "?"}`;
    case "llm_response":
      return ev.text ? `LLM · ${clip(ev.text)}` : "LLM";
    case "tool_call_request":
      return `→ ${ev.toolName ?? "tool"}()`;
    case "tool_call_result":
      return ev.text
        ? `← ${ev.toolName ?? "tool"} · ${clip(ev.text)}`
        : `← ${ev.toolName ?? "tool"}`;
    case "message_injected":
      // Sprint 57.103 (B2b): a chat-user inject the teammate drained mid-run.
      return ev.text ? `injected · ${clip(ev.text)}` : "injected mid-run";
    default:
      return ev.kind;
  }
}

/**
 * Sprint 57.103 (B2b): inject a message into a RUNNING teammate from its Tree node.
 * The teammate runs to completion while the parent turn blocks (await-completion), so
 * this control is only shown while the node is running (a brief window); the message is
 * drained at the teammate's next turn boundary and surfaces back as a `message_injected`
 * child row. No mockup design exists for this control — it reuses the mockup token set.
 */
function TeammateInjectControl({
  sessionId,
  subagentId,
}: {
  sessionId: string;
  subagentId: string;
}): JSX.Element {
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const send = async (): Promise<void> => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setSending(true);
    setError(null);
    try {
      await injectToSubagent(sessionId, subagentId, trimmed);
      setText("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="subagent-row" data-testid={`teammate-inject-${subagentId}`}>
      <input
        className="mono"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") void send();
        }}
        placeholder="message this teammate…"
        disabled={sending}
        data-testid={`teammate-inject-input-${subagentId}`}
        style={{
          flex: 1,
          fontSize: 11,
          padding: "2px 6px",
          background: "var(--bg-1)",
          border: "1px solid var(--border)",
          borderRadius: 4,
        }}
      />
      <button
        type="button"
        onClick={() => void send()}
        disabled={sending || text.trim().length === 0}
        className="mono"
        data-testid={`teammate-inject-send-${subagentId}`}
        style={{
          fontSize: 11,
          padding: "2px 8px",
          background: "transparent",
          border: "1px solid var(--border)",
          borderRadius: 4,
          color: "var(--primary)",
          cursor: "pointer",
        }}
      >
        inject
      </button>
      {error != null && (
        <span className="subtle" style={{ color: "var(--danger)" }}>
          {error}
        </span>
      )}
    </div>
  );
}

/**
 * One child-loop TAO event as a nested `.subagent-row` (Sprint 57.96 Scope B).
 * Reuses the mockup's child-row vocabulary (chevron icon + subtle text) — no new
 * widget / no new CSS; the child's per-turn loop renders inside the node's
 * existing `.indent` block alongside any nested subagents.
 */
function ChildTurnRow({ ev }: { ev: ChildTurnEvent }): JSX.Element {
  return (
    <div className="subagent-row" data-testid="inspector-tree-child-event">
      <ChevronRight size={11} aria-hidden="true" className="subtle" />
      <span className="subtle grow" style={{ marginLeft: 4 }}>
        {childTurnLabel(ev)}
      </span>
    </div>
  );
}

function NodeRow({
  rn,
  canInject,
  sessionId,
}: {
  rn: RenderNode;
  canInject: boolean;
  sessionId: string | null;
}): JSX.Element {
  const { node, children, depth } = rn;
  const isRoot = depth === 0;
  // Mockup L494 root icon = chat (MessageSquare); L513 child icon = chevron_right.
  // A node that has children reads as a fork point (GitFork) per mockup L501.
  const Icon = isRoot ? (children.length > 0 ? GitFork : MessageSquare) : ChevronRight;
  const nameColor = isRoot ? "var(--primary)" : "var(--info)";
  // Task text: live mode while running (mockup fork row shows mode), summary once completed.
  const task = node.status === "completed" ? node.summary : node.mode;
  // Sprint 57.103 (B2b): a running teammate node gets an inject control (real_llm only).
  const showInject =
    canInject && sessionId != null && node.mode === "teammate" && node.status === "running";

  return (
    <>
      <div className="subagent-row" data-testid={`inspector-tree-node-${node.subagentId}`}>
        <Icon
          size={isRoot ? 12 : 11}
          aria-hidden="true"
          style={{ color: isRoot ? nameColor : undefined }}
          className={isRoot ? undefined : "subtle"}
        />
        <span style={{ color: nameColor, fontWeight: isRoot ? 600 : undefined }}>
          {node.subagentId}
        </span>
        {isRoot && <span className="subtle">root</span>}
        {task ? (
          <span className="subtle grow" style={{ marginLeft: 4 }}>
            {task}
          </span>
        ) : (
          <span className="grow" />
        )}
        <StatusBadge status={node.status} />
      </div>
      {(showInject || node.childEvents.length > 0 || children.length > 0) && (
        <div className="indent">
          {/* Sprint 57.103 (B2b): the inject-to-teammate control on a running teammate. */}
          {showInject && sessionId != null && (
            <TeammateInjectControl sessionId={sessionId} subagentId={node.subagentId} />
          )}
          {/* Sprint 57.96 (Scope B): the child loop's per-turn TAO events render
              as nested rows under the node (the node "expands"), before any
              nested subagents. */}
          {node.childEvents.map((ce, i) => (
            <ChildTurnRow key={`${node.subagentId}-ce-${i}`} ev={ce} />
          ))}
          {children.map((c) => (
            <NodeRow
              key={c.node.subagentId}
              rn={c}
              canInject={canInject}
              sessionId={sessionId}
            />
          ))}
        </div>
      )}
    </>
  );
}

export function InspectorTree(): JSX.Element {
  const subagents = useChatStore((s) => s.subagents);
  // Sprint 57.103 (B2b): the inject-to-teammate control needs the session id + run mode
  // (gated to real_llm — echo runs spawn no real teammate). Hooks before the early return.
  const sessionId = useChatStore((s) => s.sessionId);
  const runMode = useChatStore((s) => s.mode);
  const canInject = runMode === "real_llm";

  if (subagents.length === 0) {
    return (
      <div
        data-testid="inspector-tree-empty"
        style={{ padding: "12px 16px", fontSize: 12, color: "var(--fg-muted)" }}
      >
        <div
          style={{
            fontSize: 11.5,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontFamily: "var(--font-mono)",
          }}
        >
          Subagent tree
        </div>
        <p style={{ marginTop: 8, lineHeight: 1.55 }}>no subagents spawned this session</p>
      </div>
    );
  }

  const forest = buildTree(subagents);
  const depth = maxDepth(forest);
  const runningCount = subagents.filter((n) => n.status === "running").length;
  const mode = dominantMode(subagents);
  const tokenValues = subagents.map((n) => n.tokensUsed).filter((t): t is number => t != null);
  const tokensSubtree =
    tokenValues.length > 0 ? tokenValues.reduce((a, b) => a + b, 0).toLocaleString() : "—";

  return (
    <div data-testid="inspector-tree" style={{ padding: "12px 16px" }}>
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
        Subagent tree · live
      </div>

      <div className="subagent-tree">
        {forest.map((rn) => (
          <NodeRow
            key={rn.node.subagentId}
            rn={rn}
            canInject={canInject}
            sessionId={sessionId}
          />
        ))}
      </div>

      <div className="thin-rule" />

      <div className="col" style={{ gap: 5, fontSize: 11, color: "var(--fg-muted)" }}>
        <div className="spread">
          <span>Mode</span>
          {mode ? <span className="badge">{mode}</span> : <span className="mono">—</span>}
        </div>
        <div className="spread">
          <span>Depth</span>
          <span className="mono">{depth}</span>
        </div>
        <div className="spread">
          <span>Concurrency</span>
          <span className="mono">{runningCount}</span>
        </div>
        <div className="spread">
          <span>Tokens (subtree)</span>
          <span className="mono">{tokensSubtree}</span>
        </div>
      </div>
    </div>
  );
}

export default InspectorTree;
