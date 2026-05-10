/**
 * File: frontend/src/pages/verification/index.tsx
 * Purpose: Verification page real ship — auth gate + AppShellV2 wrap + 2-tab nested routes (Recent / Correction Trace).
 * Category: Frontend / pages / verification
 * Scope: Phase 57 / Sprint 57.11 Day 2 / US-4 (was Phase 49.1 placeholder)
 *
 * Description:
 *   Sprint 57.11 Day 2 promotes the Sprint 49.1 placeholder to real ship
 *   under AppShellV2 architecture, mirroring Sprint 57.9 governance/index.tsx
 *   pattern:
 *
 *     1. Auth gate — if !isAuthenticated → setPostLoginRedirect("/verification")
 *        + <Navigate to="/auth/login" replace />
 *     2. AppShellV2 wrap — pageTitle "Verification"; sidebar + sticky header +
 *        UserMenu auto-injected from Sprint 57.8 US-2
 *     3. 2-tab nested Routes (URL-addressable):
 *        - /verification          → Navigate to "recent" (default)
 *        - /verification/recent   → VerificationList (Day 3 §3.1 full impl)
 *        - /verification/timeline → CorrectionTraceView (Day 3 §3.2 full impl)
 *
 *   Tab nav uses NavLink with isActive callback for active highlighting.
 *
 * Created: 2026-04-29 (Sprint 49.1 placeholder)
 * Last Modified: 2026-05-10
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-B5 — pageTitle + tab labels via i18n t()
 *   - 2026-05-10: Sprint 57.13 US-A1 — gate via <RequireAuth> (was inline isAuthenticated() check)
 *   - 2026-05-10: Sprint 57.11 US-4 Day 2 — auth gate + AppShellV2 + 2-tab routes (real ship)
 *   - 2026-04-29: Initial placeholder (Sprint 49.1; Phase 54.1 deferred)
 *
 * Related:
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/components/AppShellV2.tsx (Sprint 57.8 US-1.3)
 *   - frontend/src/features/verification/components/VerificationList.tsx (Day 3 §3.1)
 *   - frontend/src/features/verification/components/CorrectionTraceView.tsx (Day 3 §3.2)
 *   - frontend/src/i18n/locales/{en,zh-TW}/common.json (nav.verification + verification.tab.* keys)
 */

import { useTranslation } from "react-i18next";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { CorrectionTraceView } from "@/features/verification/components/CorrectionTraceView";
import { VerificationList } from "@/features/verification/components/VerificationList";

const tabClass = ({ isActive }: { isActive: boolean }): string =>
  `px-4 py-2 text-sm font-medium ${
    isActive
      ? "border-b-2 border-primary text-primary"
      : "text-muted-foreground hover:text-foreground"
  }`;

export default function VerificationPage(): JSX.Element {
  const { t } = useTranslation("common");
  return (
    <RequireAuth>
      <AppShellV2 pageTitle={t("nav.verification")}>
        <nav className="mb-4 flex gap-2 border-b border-border" aria-label={t("verification.tabsLabel")}>
          <NavLink to="recent" className={tabClass}>
            {t("verification.tab.recent")}
          </NavLink>
          <NavLink to="timeline" className={tabClass}>
            {t("verification.tab.correctionTrace")}
          </NavLink>
        </nav>
        <Routes>
          <Route index element={<Navigate to="recent" replace />} />
          <Route path="recent" element={<VerificationList />} />
          <Route path="timeline" element={<CorrectionTraceView />} />
          <Route path="*" element={<Navigate to="recent" replace />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
