/**
 * File: frontend/src/features/overview/components/_primitives.tsx
 * Purpose: Feature-scoped Badge + RiskBadge primitives for the /overview rebuild widgets.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   Extracted 1:1 from the OverviewPage.tsx inline `Badge` / `RiskBadge`
 *   definitions so the NEW feature-scoped widget components (ActiveLoopsCard,
 *   HITLQueueCard, and Day-2 IncidentsCard) can import a single shared copy
 *   instead of half-migrating. Feature-scoped (NOT components/ui) because the
 *   current consumer set is the overview feature only (Karpathy §2 — no
 *   speculative shared promotion).
 *
 *   Mockup-fidelity corrections vs the OverviewPage inline originals:
 *   - Badge default radius `rounded-[4px]` per mockup `.badge` (styles.css:512)
 *     — the inline version used `rounded-full` (pill); closes drift D11.
 *   - RiskBadge tone map matches mockup `.badge.risk-*` (styles.css:532-540):
 *     low → success, medium → warning, high → warning (risk-high orange),
 *     critical → danger (risk-critical deep red); closes drift D12.
 *
 * Key Components:
 *   - Tone: badge tone union
 *   - Badge: mockup `.badge` 1:1 (4px radius, dot variant)
 *   - RiskBadge: severity badge mapping `level` → tone
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — extract Badge + RiskBadge from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/styles.css §Badge (.badge / .badge.dot / .badge.risk-*)
 *   - frontend/src/pages/overview/OverviewPage.tsx (inline-primitive origin; AP-3 migration)
 */

import type { FC, ReactNode } from "react";

export type Tone =
  | "success"
  | "warning"
  | "danger"
  | "thinking"
  | "info"
  | "primary"
  | "muted";

const TONE_CLASS: Record<Tone, string> = {
  success: "bg-success/16 text-success",
  warning: "bg-warning/16 text-warning",
  danger: "bg-danger/16 text-danger",
  thinking: "bg-thinking/16 text-thinking",
  info: "bg-info/16 text-info",
  primary: "bg-primary/16 text-primary",
  muted: "bg-bg-2 text-fg-muted",
};

/**
 * Mockup `.badge` (styles.css:507-523): 4px radius (NOT pill), 10.5px mono-ish
 * uppercase label, optional leading dot. `dot` renders the mockup `.badge.dot`
 * 5px current-colour bullet.
 */
export const Badge: FC<{ tone?: Tone; dot?: boolean; children: ReactNode }> = ({
  tone = "muted",
  dot,
  children,
}) => (
  <span
    className={`inline-flex items-center gap-1 rounded-[4px] px-[6px] py-[1px] text-[10.5px] font-medium uppercase tracking-wide ${TONE_CLASS[tone]}`}
  >
    {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
    {children}
  </span>
);

/**
 * Mockup `.badge.risk-*` tone map (styles.css:532-540):
 * risk-low → success green, risk-medium → warning amber,
 * risk-high → orange (closest wired token = warning),
 * risk-critical → deep red (closest wired token = danger).
 */
const RISK_TONE: Record<string, Tone> = {
  low: "success",
  medium: "warning",
  high: "warning",
  critical: "danger",
};

export const RiskBadge: FC<{ level: string }> = ({ level }) => (
  <Badge tone={RISK_TONE[level] ?? "muted"}>{level}</Badge>
);
