/**
 * File: frontend/src/features/chat_v2/components/inspector/ComingSoonInspectorTab.tsx
 * Purpose: Empty-state placeholder for Inspector tabs deferred to Sprint 57.22+ Phase-2 ADs.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.30 Day 4 §D3 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Trace / Memory / Tree tabs render this placeholder until their respective
 *   backend feeds land in Sprint 57.22+. Each instance names the carryover AD
 *   so the operator + reviewer can locate the work item:
 *     - AD-ChatV2-Inspector-Trace-Phase2     (Cat 12 OTel spans waterfall)
 *     - AD-ChatV2-Inspector-Memory-Phase2    (Cat 3 memory ops feed)
 *     - AD-ChatV2-Inspector-SubagentTree-Phase2 (Cat 11 live tree)
 *
 *   Layout shape parallels mockup InspectorTrace/InspectorMemory wrapper
 *   pattern (page-chat.jsx L434+L468+L489 all use
 *   `<div style={{ padding: "12px 16px" }}>` + section header inline-style
 *   font-family mono uppercase tracking). Production-only widget (no
 *   mockup equivalent — this is the Phase-1 fallback widget pending
 *   Sprint 57.22+ backend wire-up); uses mockup vocabulary (`.mono`,
 *   `.subtle`, `.thin-rule`) + inline-style verbatim mockup literals
 *   (var(--*) tokens + same 11.5px/uppercase header treatment).
 *
 *   Sprint 57.30 Day 4: re-pointed from Tailwind utility translations
 *   (`text-fg-muted` / `rounded border border-border bg-bg-2`) to
 *   verbatim mockup vocabulary + inline-style literals matching the
 *   sibling Inspector*Trace/Memory wrapper shape.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 4 §4.1)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.30 Day 4 §D3 — verbatim re-point Tailwind → mockup .mono/.subtle inline-style sibling shape
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 4 §4.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L434-466 (Trace), L468-487 (Memory), L489-531 (Tree)
 *   - frontend/src/styles-mockup.css L1119 (.thin-rule) + L617+L620 (.subtle/.mono)
 *   - ./ChatInspector.tsx (tab dispatcher)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: section header inline-style
   matches mockup InspectorTrace/Memory/Tree sibling shape (page-chat.jsx L436/L470/L491).
   Tokens via var(--*) — not literals. */

type Props = {
  name: "Trace" | "Memory" | "Tree";
  mockupSection: string;
  carryoverAd: string;
  hint: string;
};

export function ComingSoonInspectorTab({ name, mockupSection, carryoverAd, hint }: Props): JSX.Element {
  return (
    <div
      data-testid={`inspector-tab-coming-soon-${name.toLowerCase()}`}
      style={{ padding: "12px 16px" }}
    >
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
        {name} · coming soon
      </div>
      <p style={{ fontSize: 12, color: "var(--fg-muted)", lineHeight: 1.55, marginBottom: 8 }}>
        {hint}
      </p>
      <div
        style={{
          border: "1px solid var(--border)",
          background: "var(--bg-2)",
          borderRadius: "var(--radius-sm)",
          padding: "8px 10px",
          fontSize: 11,
          lineHeight: 1.45,
          color: "var(--fg-muted)",
        }}
      >
        <div>
          Mockup design: <span className="mono">page-chat.jsx {mockupSection}</span>
        </div>
        <div style={{ marginTop: 4 }}>
          Backend wire: <span className="mono" style={{ color: "var(--fg)" }}>{carryoverAd}</span> (Sprint 57.22+)
        </div>
      </div>
    </div>
  );
}

export default ComingSoonInspectorTab;
