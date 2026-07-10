/**
 * File: frontend/src/features/chat_v2/components/blocks/ToolBlock.tsx
 * Purpose: Renders tool call block — verbatim mockup re-point of L208-223.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Head row (tool icon + name +
 *   status badge + duration label) + monospace input pre-block (// input
 *   comment) + dashed-separator monospace output pre-block (// output).
 *   Status: pending (info-tinted badge / "—" duration) / ok (success
 *   badge / ms) / error (danger badge / ms). Source: mockup
 *   reference/design-mockups/page-chat.jsx L208-223; styles
 *   styles-mockup.css L794-820 (.block.tool-call + .tool-call-head +
 *   .tool-call-body + .tool-call-body.result) + L507-535 (.badge dot
 *   variants for status).
 *
 *   Sprint 57.30 Day 3: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.block.tool-call` / `.block.tool-call-head` /
 *   `.block.tool-call-body` / `.block.tool-call-body.result` + `.badge dot`
 *   classes. Body's `<div>` (mockup) vs production's `<pre>` preserved as
 *   `<div>` so mockup `.tool-call-body` whitespace-pre-wrap + monospace
 *   styling applies verbatim. Mockup uses `<Icon name="tool" style={{
 *   color: "var(--tool)" }}>` — production uses lucide `<Wrench>` icon.
 *   "// input" / "// output" subtle comments preserved via inline-style
 *   color matching mockup L219-220.
 *
 *   Replaces Sprint 50.2 ToolCallCard.tsx for chat_v2 usage; ToolCallCard
 *   becomes thin compat re-export Day 3 EOD (Sprint 57.x SubagentTree +
 *   other consumers preserve via re-export until full migration).
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-07-10: Sprint 57.164 — conditional error-taxonomy chip (.badge danger; no new CSS)
 *   - 2026-05-23: Sprint 57.30 Day 3 §D2 — verbatim re-point Tailwind → mockup .block.tool-call/.tool-call-head/.tool-call-body + .badge dot
 *   - 2026-05-17: Initial extract from mockup L208-223 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L208-223 (source JSX)
 *   - frontend/src/styles-mockup.css L794-820 (.block.tool-call / .tool-call-head / .tool-call-body / .tool-call-body.result)
 *   - frontend/src/styles-mockup.css L507-535 (.badge .badge.success .badge.danger .badge.info)
 *   - frontend/src/styles-mockup.css L520-523 (.badge.dot::before)
 *   - ../../types.ts (ToolBlock type)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L212+L214+L216
   uses inline-style on Icon (color: var(--tool)) + row gap + mono subtle 10.5px size +
   L219-220 inline-style on "// input"/"// output" subtle comment color: var(--fg-subtle). */

import { Wrench } from "lucide-react";

import type { ToolBlock as ToolBlockType } from "../../types";

const STATUS_BADGE_TONE: Record<ToolBlockType["status"], string> = {
  pending: "info",
  ok: "success",
  error: "danger",
};

const STATUS_LABEL: Record<ToolBlockType["status"], string> = {
  pending: "pending",
  ok: "success",
  error: "error",
};

export function ToolBlock({ block }: { block: ToolBlockType }): JSX.Element {
  const durationLabel = block.durationMs !== null ? `${block.durationMs}ms` : "—";
  return (
    <div className="block tool-call">
      <div className="block tool-call-head">
        <Wrench size={13} style={{ color: "var(--tool)" }} />
        <span className="name">{block.name}</span>
        <span className="row" style={{ marginLeft: "auto", gap: 6 }}>
          <span className={`badge dot ${STATUS_BADGE_TONE[block.status]}`}>
            {STATUS_LABEL[block.status]}
          </span>
          {/* Sprint 57.164 (AD-Tool-Error-Taxonomy-UI): typed error diagnosis on a
              failed tool. Reuses the mockup `.badge danger` primitive (no new CSS);
              renders only when present (success/pending tools unchanged). */}
          {block.errorTaxonomy && (
            <span
              className="badge danger"
              title="tool error taxonomy"
              data-testid="tool-error-taxonomy"
            >
              {block.errorTaxonomy}
            </span>
          )}
          <span className="mono subtle" style={{ fontSize: 10.5 }}>{durationLabel}</span>
        </span>
      </div>
      <div className="block tool-call-body">
        <span style={{ color: "var(--fg-subtle)" }}>{"// input"}</span>
        {"\n"}
        {block.input}
      </div>
      {block.output !== null && (
        <div className="block tool-call-body result">
          <span style={{ color: "var(--fg-subtle)" }}>{"// output"}</span>
          {"\n"}
          {block.output}
        </div>
      )}
    </div>
  );
}
