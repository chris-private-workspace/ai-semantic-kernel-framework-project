/**
 * File: frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx
 * Purpose: Renders verification block — Tailwind translation of mockup L234-244.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Inline block within AgentTurn body. Check-icon + claim + evidence row
 *   in success tone (ok) or x-icon in danger tone (failed). Source: mockup
 *   reference/design-mockups/page-chat.jsx L234-244; styles
 *   reference/design-mockups/styles.css L822-832.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L234-244 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L234-244 (source JSX)
 *   - reference/design-mockups/styles.css L822-832 (block.verification + .failed)
 *   - ../../types.ts (VerificationBlock type)
 */

import { Check, X } from "lucide-react";

import type { VerificationBlock as VerificationBlockType } from "../../types";

export function VerificationBlock({ block }: { block: VerificationBlockType }): JSX.Element {
  const containerClass = block.ok
    ? "border-success/30 bg-success/[0.06]"
    : "border-danger/40 bg-danger/[0.06]";
  const iconClass = block.ok ? "text-success" : "text-danger";
  return (
    <div className={`my-1.5 flex items-start gap-2 rounded-md border px-3 py-2 text-[11.5px] ${containerClass}`}>
      <div className={`pt-px ${iconClass}`}>
        {block.ok ? <Check size={13} /> : <X size={13} />}
      </div>
      <div>
        <div className="font-medium">{block.claim}</div>
        {block.evidence && (
          <div className="mt-0.5 text-[11px] text-fg-subtle">evidence: {block.evidence}</div>
        )}
      </div>
    </div>
  );
}
