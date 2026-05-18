/**
 * File: frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx
 * Purpose: Renders subagent fork block — Tailwind translation of mockup L245-264.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Header (fork icon + "Fork ·
 *   concurrent" + spawned N count) + agent row list (chevron + name +
 *   task + status badge done/running + turns count). Source: mockup
 *   reference/design-mockups/page-chat.jsx L245-264; styles
 *   reference/design-mockups/styles.css L899-916.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L245-264 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L245-264 (source JSX)
 *   - reference/design-mockups/styles.css L899-916 (subagent-tree / subagent-row / .indent)
 *   - ../../types.ts (SubagentForkBlock + SubagentEntry types)
 */

import { ChevronRight, GitFork } from "lucide-react";

import type { SubagentForkBlock as SubagentForkBlockType } from "../../types";

const STATUS_BADGE: Record<"running" | "done", string> = {
  running: "bg-info/15 text-info",
  done: "bg-success/15 text-success",
};

export function SubagentForkBlock({ block }: { block: SubagentForkBlockType }): JSX.Element {
  return (
    <div className="my-1.5 rounded-md border border-border bg-bg-1 p-2">
      <div className="flex items-center gap-2 px-2 py-1 text-[11px] text-fg-muted">
        <GitFork size={12} />
        <span className="font-mono font-semibold text-primary">Fork · concurrent</span>
        <span className="font-mono text-fg-subtle">
          spawned {block.agents.length} subagent{block.agents.length === 1 ? "" : "s"}
        </span>
      </div>
      {block.agents.map((a) => (
        <div
          key={a.id}
          className="flex items-center gap-2 rounded-sm px-2 py-1 font-mono text-[11.5px] hover:bg-bg-2"
        >
          <ChevronRight size={12} className="text-fg-subtle" />
          <span className="text-primary">{a.name}</span>
          <span className="text-fg-subtle">·</span>
          <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-fg-muted">
            {a.task}
          </span>
          <span className={`inline-flex items-center gap-1 rounded-full px-1.5 py-px text-[10.5px] ${STATUS_BADGE[a.status]}`}>
            <span className="h-1 w-1 rounded-full bg-current" />
            {a.status}
          </span>
          <span className="text-fg-subtle">{a.turns}t</span>
        </div>
      ))}
    </div>
  );
}
