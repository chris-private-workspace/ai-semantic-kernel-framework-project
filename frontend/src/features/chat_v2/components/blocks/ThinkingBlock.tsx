/**
 * File: frontend/src/features/chat_v2/components/blocks/ThinkingBlock.tsx
 * Purpose: Renders agent thinking block — verbatim mockup re-point of L200-207.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Left-rail border in thinking-tone +
 *   subtle thinking-tinted background + italic muted text body + uppercase
 *   monospace "thinking" label. Source: mockup
 *   reference/design-mockups/page-chat.jsx L200-207; styles
 *   styles-mockup.css L779-792 (.block.thinking + .block.thinking .label).
 *
 *   Sprint 57.30 Day 3: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.block.thinking` + `.label` classes. Mockup CSS
 *   owns left-rail border + bg tint + italic + label styling — no inline.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.30 Day 3 §D2 — verbatim re-point Tailwind → mockup .block.thinking + .label
 *   - 2026-05-17: Initial extract from mockup L200-207 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L200-207 (source JSX)
 *   - frontend/src/styles-mockup.css L779-792 (.block.thinking + .label)
 *   - ../../types.ts (ThinkingBlock type)
 */

import { Brain } from "lucide-react";

import type { ThinkingBlock as ThinkingBlockType } from "../../types";

export function ThinkingBlock({ block }: { block: ThinkingBlockType }): JSX.Element {
  return (
    <div className="block thinking">
      <div className="label">
        <Brain size={11} />
        thinking
      </div>
      {block.text}
    </div>
  );
}
