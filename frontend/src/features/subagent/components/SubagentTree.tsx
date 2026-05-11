/**
 * File: frontend/src/features/subagent/components/SubagentTree.tsx
 * Purpose: Inline subagent tree panel for chat-v2 — live spawn/complete status (Sprint 57.12 US-6).
 * Category: Frontend / subagent / components
 * Scope: Phase 57 / Sprint 57.12 Day 3 / US-6
 *
 * Description:
 *   Subscribes to chatStore.subagents and renders a nested tree:
 *     - Root nodes = subagents whose parentId is the chat session_id (or whose
 *       parentId is not itself a known subagent_id — defensive).
 *     - Child nodes = subagents whose parentId matches another subagent's id
 *       (recursive subagent spawning; depth capped at 5 for layout safety).
 *     - Each node shows: SubagentStatusBadge (running/completed + mode) +
 *       subagent_id short prefix + on completion: tokens + summary snippet.
 *
 *   Hidden when subagents.length === 0 (no empty panel — preserves chat-v2
 *   layout when no multi-agent activity). Mirrors VerificationPanel.tsx pattern.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 3 / US-6)
 * Last Modified: 2026-05-11
 *
 * Modification History:
 *   - 2026-05-11: Sprint 57.15 — drop the lone inline style (dynamic tree-indent) for a finite ml-* class lookup (AD-Inline-Style-Cleanup-Sweep)
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 3 / US-6)
 *
 * Related:
 *   - ../../chat_v2/store/chatStore.ts (subagents slice + reducers)
 *   - ../types.ts (SubagentNode)
 *   - ./SubagentStatusBadge.tsx
 *   - frontend/src/features/verification/components/VerificationPanel.tsx (sibling pattern)
 */

import { cn } from "../../../lib/utils";
import { useChatStore } from "../../chat_v2/store/chatStore";
import type { SubagentNode } from "../types";
import { SubagentStatusBadge } from "./SubagentStatusBadge";

const MAX_DEPTH = 5;
const SUMMARY_SNIPPET_MAX = 60;

// Tree-indent per depth (depth*12px), as literal Tailwind classes so the JIT
// can see them; depth is bounded by MAX_DEPTH so 0..5. Replaces a dynamic
// `style={{ marginLeft: depth*12 }}`.
const DEPTH_INDENT = ["ml-0", "ml-3", "ml-6", "ml-9", "ml-12", "ml-[60px]"];

function _truncate(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max)}…`;
}

interface RenderNode {
  node: SubagentNode;
  children: RenderNode[];
}

/** Build a forest from the flat node list, keyed by parentId. Cycles guarded by visited set. */
function buildForest(nodes: SubagentNode[]): RenderNode[] {
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
    if (depth >= MAX_DEPTH) return { node, children: [] };
    const kids = (childrenOf.get(node.subagentId) ?? []).filter((c) => !visited.has(c.subagentId));
    return { node, children: kids.map((c) => expand(c, depth + 1)) };
  }
  return roots.map((r) => expand(r, 0));
}

function NodeRow({ rn, depth }: { rn: RenderNode; depth: number }): JSX.Element {
  const { node } = rn;
  return (
    <li
      className={cn("space-y-1", DEPTH_INDENT[depth] ?? "ml-[60px]")}
      data-testid={`subagent-node-${node.subagentId}`}
    >
      <div className="flex items-start gap-2 rounded bg-background p-2">
        <SubagentStatusBadge status={node.status} mode={node.mode} />
        <div className="min-w-0 flex-1">
          <span className="font-mono text-[11px] text-muted-foreground">
            {node.subagentId.slice(0, 8)}…
          </span>
          {node.status === "completed" && (
            <p className="mt-1 text-xs text-muted-foreground">
              {node.tokensUsed !== null ? `${node.tokensUsed} tok` : ""}
              {node.summary ? ` · ${_truncate(node.summary, SUMMARY_SNIPPET_MAX)}` : ""}
            </p>
          )}
        </div>
      </div>
      {rn.children.length > 0 && (
        <ul className="space-y-1">
          {rn.children.map((c) => (
            <NodeRow key={c.node.subagentId} rn={c} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function SubagentTree(): JSX.Element | null {
  const subagents = useChatStore((s) => s.subagents);
  if (subagents.length === 0) return null;

  const forest = buildForest(subagents);
  const runningCount = subagents.filter((n) => n.status === "running").length;

  return (
    <div
      className="border-t border-border bg-muted/30 p-3"
      data-testid="subagent-tree"
      aria-label="Subagent tree"
    >
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Subagents ({subagents.length}
        {runningCount > 0 ? ` · ${runningCount} running` : ""})
      </h3>
      <ul className="space-y-1">
        {forest.map((rn) => (
          <NodeRow key={rn.node.subagentId} rn={rn} depth={0} />
        ))}
      </ul>
    </div>
  );
}
