/**
 * File: frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx
 * Purpose: Renders tool call block — Tailwind translation of mockup L208-223.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Head row (tool icon + name +
 *   status badge + duration label) + monospace input pre-block (// input
 *   comment) + dashed-separator monospace output pre-block (// output).
 *   Status: pending (no badge / "—" duration) / ok (success badge / ms)
 *   / error (danger badge / ms). Source: mockup
 *   reference/design-mockups/page-chat.jsx L208-223; styles
 *   reference/design-mockups/styles.css L794-820.
 *
 *   Replaces Sprint 50.2 ToolCallCard.tsx for chat_v2 usage; ToolCallCard
 *   becomes thin compat re-export Day 3 EOD (Sprint 57.x SubagentTree +
 *   other consumers preserve via re-export until full migration).
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L208-223 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L208-223 (source JSX)
 *   - reference/design-mockups/styles.css L794-820 (block.tool-call / .tool-call-head / .tool-call-body)
 *   - ../../types.ts (ToolBlock type)
 */

import { Wrench } from "lucide-react";

import type { ToolBlock as ToolBlockType } from "../../types";

const STATUS_BADGE: Record<ToolBlockType["status"], string> = {
  pending: "bg-bg-2 text-fg-muted",
  ok: "bg-success/15 text-success",
  error: "bg-danger/15 text-danger",
};

const STATUS_LABEL: Record<ToolBlockType["status"], string> = {
  pending: "pending",
  ok: "success",
  error: "error",
};

export function ToolBlock({ block }: { block: ToolBlockType }): JSX.Element {
  const durationLabel = block.durationMs !== null ? `${block.durationMs}ms` : "—";
  return (
    <div className="my-1.5 overflow-hidden rounded-md border border-tool/30 bg-bg-1 text-xs">
      <div className="flex items-center gap-2 border-b border-tool/20 bg-tool/10 px-3 py-2 font-mono text-[11.5px]">
        <Wrench size={13} className="text-tool" />
        <span className="font-semibold text-tool">{block.name}</span>
        <span className="ml-auto flex items-center gap-1.5">
          <span className={`inline-flex items-center gap-1 rounded-full px-1.5 py-px text-[10.5px] ${STATUS_BADGE[block.status]}`}>
            <span className="h-1 w-1 rounded-full bg-current" />
            {STATUS_LABEL[block.status]}
          </span>
          <span className="font-mono text-[10.5px] text-fg-subtle">{durationLabel}</span>
        </span>
      </div>
      <pre className="max-h-[200px] overflow-y-auto whitespace-pre-wrap bg-bg-1 px-3 py-2 font-mono text-[11px] text-fg-muted">
        <span className="text-fg-subtle">{"// input"}</span>
        {"\n"}
        {block.input}
      </pre>
      {block.output !== null && (
        <pre className="max-h-[200px] overflow-y-auto whitespace-pre-wrap border-t border-dashed border-border bg-bg-1 px-3 py-2 pt-2 font-mono text-[11px] text-fg-muted">
          <span className="text-fg-subtle">{"// output"}</span>
          {"\n"}
          {block.output}
        </pre>
      )}
    </div>
  );
}
