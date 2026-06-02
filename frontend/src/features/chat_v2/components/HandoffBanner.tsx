/**
 * File: frontend/src/features/chat_v2/components/HandoffBanner.tsx
 * Purpose: Transition notice shown after a Cat 11 HANDOFF pivots the chat to the child session.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57 / Sprint 57.69 (A-3b slice 2 — FE session-pivot + banner)
 *
 * Description:
 *   Renders a dismissible notice strip when chatStore.handoffBanner is set
 *   (raised by the `agent_handoff` mergeEvent pivot — Sprint 57.69). Shows the
 *   handoff target agent + reason and a dismiss button that clears the banner
 *   via chatStore.dismissHandoffBanner. Renders nothing when handoffBanner is
 *   null. Mounted above <TurnList> in ChatLayout.
 *
 *   AP-2 honesty: there is NO mockup source for a handoff banner (Day-0 audit
 *   D8 — reference/design-mockups/ has no handoff/transition markup). This is a
 *   production-only widget composed from EXISTING design-system primitives —
 *   the `.badge.info` class (styles-mockup.css L527, oklch `--info` token) for
 *   the agent badge, and a wrapper whose border/background reuse the same
 *   `oklch(from var(--info) ...)` recipe `.badge.info` itself uses (no new
 *   styles-mockup.css class, no new oklch colour). User-facing copy is inline
 *   繁體中文 — chat_v2 has no keyed i18n system (sibling HITLTurn / TurnList use
 *   inline strings); copy is kept in a local COPY map for scannability.
 *
 * Key Components:
 *   - HandoffBanner: reads handoffBanner + dismissHandoffBanner from the store.
 *
 * Created: 2026-06-02 (Sprint 57.69)
 * Last Modified: 2026-06-02
 *
 * Modification History (newest-first):
 *   - 2026-06-02: Initial creation (Sprint 57.69 A-3b slice 2) — HANDOFF transition banner
 *
 * Related:
 *   - ../store/chatStore.ts (handoffBanner state + dismissHandoffBanner action)
 *   - ./ChatLayout.tsx (mounts this above TurnList)
 *   - frontend/src/styles-mockup.css L507/527 (.badge / .badge.info — oklch --info token)
 *   - docs/.../sprint-57-69-plan.md §3.4 (US-4)
 */

/* eslint-disable no-restricted-syntax -- AP-2 production-only widget: no mockup
   source exists for a handoff banner (Day-0 D8). The wrapper inline-style reuses
   the exact `var(--info)`-derived relative-colour recipe from `.badge.info`
   (styles-mockup.css L527) so no NEW colour is introduced; all values are
   existing design-system tokens. */

import { ArrowRightLeft, X } from "lucide-react";

import { useChatStore } from "../store/chatStore";

// chat_v2 has no keyed i18n system (sibling components use inline strings).
// User-facing copy is 繁體中文 per project convention; {agent} interpolated.
const COPY = {
  label: "已交棒",
  to: (agent: string): string => `已交棒給 ${agent}`,
  reasonLabel: "原因",
  dismiss: "關閉",
} as const;

export function HandoffBanner(): JSX.Element | null {
  const handoffBanner = useChatStore((s) => s.handoffBanner);
  const dismissHandoffBanner = useChatStore((s) => s.dismissHandoffBanner);

  if (handoffBanner === null) return null;

  const { targetAgent, reason } = handoffBanner;

  return (
    <div
      data-testid="handoff-banner"
      role="status"
      aria-label={COPY.label}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        margin: "8px 12px",
        padding: "8px 12px",
        borderRadius: "var(--radius)",
        fontSize: 12.5,
        color: "var(--fg)",
        border: "1px solid oklch(from var(--info) l c h / 0.32)",
        background: "oklch(from var(--info) l c h / 0.14)",
      }}
    >
      <span className="badge info">
        <ArrowRightLeft size={11} />
        {COPY.to(targetAgent)}
      </span>
      <span className="subtle" style={{ flex: 1, color: "var(--fg-muted)" }}>
        {COPY.reasonLabel}: {reason}
      </span>
      <button
        type="button"
        aria-label={COPY.dismiss}
        onClick={() => dismissHandoffBanner()}
        className="btn ghost"
        data-size="sm"
        data-testid="handoff-banner-dismiss"
      >
        <X size={12} />
      </button>
    </div>
  );
}

export default HandoffBanner;
