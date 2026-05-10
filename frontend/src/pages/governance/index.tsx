/**
 * File: frontend/src/pages/governance/index.tsx
 * Purpose: Governance page real ship — auth gate + AppShellV2 wrap + 2-tab nested routes (Pending Approvals / Audit Log).
 * Category: Frontend / pages / governance
 * Scope: Phase 57 / Sprint 57.9 US-1 Day 1 (was Phase 53 / Sprint 53.5 placeholder)
 *
 * Description:
 *   Sprint 57.9 Day 1 promotes the Sprint 53.5 inline-styled placeholder
 *   (40-line nested Routes container) to a real ship under the Sprint 57.8
 *   AppShellV2 architecture:
 *
 *     1. Auth gate — if !isAuthenticated → setPostLoginRedirect("/governance")
 *        + <Navigate to="/auth/login" replace /> (mirror chat-v2 Sprint 57.8 US-5)
 *     2. AppShellV2 wrap — pageTitle "Governance"; sidebar + sticky header +
 *        UserMenu auto-injected from Sprint 57.8 US-2
 *     3. 2-tab nested Routes (URL-addressable per Sprint 57.9 plan Q3 select A):
 *        - /governance        → Navigate to "approvals" (default)
 *        - /governance/approvals → ApprovalsPage (Sprint 53.5 US-1; Sprint 57.9
 *          US-2/US-3 polish: Tailwind + TanStack Query hooks)
 *        - /governance/audit-log → AuditLogViewer (Sprint 57.9 US-4 Day 3)
 *
 *   Tab nav uses NavLink with isActive callback for active state highlighting.
 *
 * Created: 2026-04-29 (Sprint 49.1 placeholder)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A1 — gate via <RequireAuth> (was inline isAuthenticated() check)
 *   - 2026-05-09: Sprint 57.9 US-1 Day 1 — auth gate + AppShellV2 + 2-tab routes (real ship)
 *   - 2026-05-04: Wire ApprovalsPage at /approvals (Sprint 53.5 US-1)
 *   - 2026-04-29: Initial placeholder (Sprint 49.1)
 *
 * Related:
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/components/AppShellV2.tsx (Sprint 57.8 US-1.3)
 *   - frontend/src/features/governance/components/ApprovalsPage.tsx (Sprint 53.5 US-1)
 *   - frontend/src/features/governance/components/AuditLogViewer.tsx (Sprint 57.9 US-4 Day 3)
 */

import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { ApprovalsPage } from "@/features/governance/components/ApprovalsPage";
import { AuditLogViewer } from "@/features/governance/components/AuditLogViewer";

const tabClass = ({ isActive }: { isActive: boolean }): string =>
  `px-4 py-2 text-sm font-medium ${
    isActive
      ? "border-b-2 border-primary text-primary"
      : "text-muted-foreground hover:text-foreground"
  }`;

export default function GovernancePage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Governance">
        <nav className="mb-4 flex gap-2 border-b border-border" aria-label="Governance tabs">
          <NavLink to="approvals" className={tabClass}>
            Pending Approvals
          </NavLink>
          <NavLink to="audit-log" className={tabClass}>
            Audit Log
          </NavLink>
        </nav>
        <Routes>
          <Route index element={<Navigate to="approvals" replace />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="audit-log" element={<AuditLogViewer />} />
          <Route path="*" element={<Navigate to="approvals" replace />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
