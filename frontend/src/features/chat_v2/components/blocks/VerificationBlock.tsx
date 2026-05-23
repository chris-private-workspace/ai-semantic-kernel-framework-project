/**
 * File: frontend/src/features/chat_v2/components/blocks/VerificationBlock.tsx
 * Purpose: Renders verification block — verbatim mockup re-point of page-chat.jsx L234-244.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.30 Day 4 §D2 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Inline block within AgentTurn body. Check-icon (ok) or X-icon (failed)
 *   + claim text + evidence sub-row. Source: mockup
 *   reference/design-mockups/page-chat.jsx L234-244; styles
 *   frontend/src/styles-mockup.css L822-832 (.block.verification + .failed).
 *
 *   Sprint 57.30 Day 4: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.block.verification` + `.failed` modifier. The
 *   border / background / padding / gap / font-size are all CSS-owned
 *   by .block + .block.verification rules; production no longer composes
 *   them via Tailwind (kills the eyeballed `border-success/30` /
 *   `bg-success/[0.06]` translations).
 *
 *   Icon color uses verbatim mockup inline-style literals (var tokens)
 *   matching mockup L237 (`style={{ color: b.ok ? "var(--success)" : "var(--danger)" }}`).
 *   Evidence sub-row uses verbatim mockup .subtle class + 11px inline literal
 *   (mockup L240 `style={{ fontSize: 11, marginTop: 2 }}`).
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.30 Day 4 §D2 — verbatim re-point Tailwind → mockup .block.verification(.failed) + inline-style var(--success|--danger) icon color
 *   - 2026-05-17: Initial extract from mockup L234-244 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L234-244 (source JSX)
 *   - frontend/src/styles-mockup.css L822-832 (block.verification + .failed)
 *   - ../../types.ts (VerificationBlock type)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L237
   (icon style={{ color: b.ok ? "var(--success)" : "var(--danger)" }}) + L240 (evidence
   font-size: 11 + marginTop: 2). Tokens not literals — mockup CSS var only. */

import { Check, X } from "lucide-react";

import type { VerificationBlock as VerificationBlockType } from "../../types";

export function VerificationBlock({ block }: { block: VerificationBlockType }): JSX.Element {
  return (
    <div className={`block verification${block.ok ? "" : " failed"}`}>
      <span style={{ color: block.ok ? "var(--success)" : "var(--danger)", display: "inline-flex" }}>
        {block.ok ? <Check size={13} /> : <X size={13} />}
      </span>
      <div>
        <div style={{ fontWeight: 500 }}>{block.claim}</div>
        {block.evidence && (
          <div className="subtle" style={{ fontSize: 11, marginTop: 2 }}>
            evidence: {block.evidence}
          </div>
        )}
      </div>
    </div>
  );
}
