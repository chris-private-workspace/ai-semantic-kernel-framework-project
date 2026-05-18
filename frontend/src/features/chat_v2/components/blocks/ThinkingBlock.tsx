/**
 * File: frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx
 * Purpose: Renders agent thinking block — Tailwind translation of mockup L200-207.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Left-rail border in thinking-tone +
 *   subtle thinking-tinted background + italic muted text body + uppercase
 *   monospace "thinking" label. Source: mockup
 *   reference/design-mockups/page-chat.jsx L200-207; styles
 *   reference/design-mockups/styles.css L779-792.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L200-207 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L200-207 (source JSX)
 *   - reference/design-mockups/styles.css L779-792 (block.thinking / .label)
 *   - ../../types.ts (ThinkingBlock type)
 */

import { Brain } from "lucide-react";

import type { ThinkingBlock as ThinkingBlockType } from "../../types";

export function ThinkingBlock({ block }: { block: ThinkingBlockType }): JSX.Element {
  return (
    <div className="my-1.5 rounded-sm border-l-2 border-thinking bg-thinking/[0.04] px-3 py-2 text-xs italic text-fg-muted">
      <div className="mb-1 inline-flex items-center gap-1.5 font-mono text-[10.5px] font-medium uppercase not-italic tracking-wider text-thinking">
        <Brain size={11} />
        thinking
      </div>
      <div>{block.text}</div>
    </div>
  );
}
