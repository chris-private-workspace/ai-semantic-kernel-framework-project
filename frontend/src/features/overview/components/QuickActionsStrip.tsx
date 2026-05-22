/**
 * File: frontend/src/features/overview/components/QuickActionsStrip.tsx
 * Purpose: /overview quick-actions strip — 4 static action buttons (flex row).
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C3
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:236-266`.
 *   Strip component (NO CardShell, NO fixture, NO BackendGapBanner — 4 static
 *   navigation actions). Flex row, gap 12, each button uses the mockup `quickBtn`
 *   inline-style object verbatim. Icon from mockup-ui.tsx.
 *
 *   4 actions (left-to-right):
 *   1. New Chat  → /chat-v2    (chat icon, primary)
 *   2. Review    → /governance (approval icon, warning)
 *   3. Tenants   → /admin/tenants (tenants icon, info)
 *   4. Verification → /verification (checkcheck icon, success)
 *
 * Key Components:
 *   - QuickActionsStrip: flex row of 4 action buttons
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point to mockup .row+quickBtn+Icon
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C3) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:236-266 (QuickActionsStrip canonical)
 *   - frontend/src/components/mockup-ui.tsx (Icon primitive)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Icon } from "@/components/mockup-ui";
import type { IconName } from "@/components/mockup-ui";

// Verbatim from page-overview.jsx:33-37
const quickBtn: CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  gap: 6,
  alignItems: "flex-start",
  padding: 12,
  background: "var(--bg-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  cursor: "pointer",
  textAlign: "left",
};

interface QuickAction {
  labelKey: string;
  subKey: string;
  icon: IconName;
  iconColor: string;
  to: string;
}

const ACTIONS: QuickAction[] = [
  {
    labelKey: "overview.quickActions.newChat",
    subKey: "overview.quickActions.newChatSub",
    icon: "chat",
    iconColor: "var(--primary)",
    to: "/chat-v2",
  },
  {
    labelKey: "overview.quickActions.review",
    subKey: "overview.quickActions.reviewSub",
    icon: "approval",
    iconColor: "var(--warning)",
    to: "/governance",
  },
  {
    labelKey: "overview.quickActions.tenants",
    subKey: "overview.quickActions.tenantsSub",
    icon: "tenants",
    iconColor: "var(--info)",
    to: "/admin/tenants",
  },
  {
    labelKey: "overview.quickActions.verification",
    subKey: "overview.quickActions.verificationSub",
    icon: "checkcheck",
    iconColor: "var(--success)",
    to: "/verification",
  },
];

export const QuickActionsStrip: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="row" style={{ gap: 12 }}>
      {ACTIONS.map((action) => (
        <button
          key={action.labelKey}
          type="button"
          style={quickBtn}
          onClick={() => navigate(action.to)}
        >
          <span className="row" style={{ gap: 6, alignItems: "center" } satisfies CSSProperties}>
            <Icon name={action.icon} size={14} style={{ color: action.iconColor } satisfies CSSProperties} />
            <span style={{ fontSize: 12.5, fontWeight: 500 } satisfies CSSProperties}>{t(action.labelKey)}</span>
          </span>
          <span className="muted" style={{ fontSize: 11 } satisfies CSSProperties}>{t(action.subKey)}</span>
        </button>
      ))}
    </div>
  );
};
