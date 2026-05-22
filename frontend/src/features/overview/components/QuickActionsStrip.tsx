/**
 * File: frontend/src/features/overview/components/QuickActionsStrip.tsx
 * Purpose: /overview quick-actions strip — 4 static action buttons (flex row).
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C3
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:236-266`.
 *   Strip component (NO CardShell, NO fixture, NO BackendGapBanner — 4 static
 *   navigation actions). Flex row, gap 12, each button: flex-col gap-6, p-3,
 *   bg-bg-1, border border-border, rounded-[8px], left-aligned.
 *
 *   4 actions (left-to-right):
 *   1. New Chat  → /chat-v2    (MessageSquarePlus, primary)
 *   2. Review    → /governance (ClipboardCheck, warning)
 *   3. Tenants   → /admin/tenants (Building2, info)
 *   4. Verification → /verification (CheckCheck, success)
 *
 * Key Components:
 *   - QuickActionsStrip: flex row of 4 action buttons
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C3) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:236-266 (QuickActionsStrip canonical)
 */

import { Building2, CheckCheck, ClipboardCheck, MessageSquarePlus } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

interface QuickAction {
  labelKey: string;
  subKey: string;
  icon: FC<{ className?: string }>;
  iconClass: string;
  to: string;
}

const ACTIONS: QuickAction[] = [
  {
    labelKey: "overview.quickActions.newChat",
    subKey: "overview.quickActions.newChatSub",
    icon: MessageSquarePlus,
    iconClass: "text-primary",
    to: "/chat-v2",
  },
  {
    labelKey: "overview.quickActions.review",
    subKey: "overview.quickActions.reviewSub",
    icon: ClipboardCheck,
    iconClass: "text-warning",
    to: "/governance",
  },
  {
    labelKey: "overview.quickActions.tenants",
    subKey: "overview.quickActions.tenantsSub",
    icon: Building2,
    iconClass: "text-info",
    to: "/admin/tenants",
  },
  {
    labelKey: "overview.quickActions.verification",
    subKey: "overview.quickActions.verificationSub",
    icon: CheckCheck,
    iconClass: "text-success",
    to: "/verification",
  },
];

export const QuickActionsStrip: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="flex gap-3">
      {ACTIONS.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.labelKey}
            type="button"
            onClick={() => navigate(action.to)}
            className="flex flex-1 flex-col items-start gap-[6px] rounded-[8px] border border-border bg-bg-1 p-3 text-left hover:bg-bg-hover"
          >
            <span className="flex items-center gap-[6px]">
              <Icon className={`h-3.5 w-3.5 ${action.iconClass}`} />
              <span className="text-[12.5px] font-medium">{t(action.labelKey)}</span>
            </span>
            <span className="text-[11px] text-fg-muted">{t(action.subKey)}</span>
          </button>
        );
      })}
    </div>
  );
};
