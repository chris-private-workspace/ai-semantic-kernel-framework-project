/**
 * File: frontend/src/pages/memory/index.tsx
 * Purpose: Memory page (real ship) — auth gate + AppShellV2 wrap + 2-tab nested routes (Recent / By Scope).
 * Category: Frontend / pages / memory
 * Scope: Phase 57 / Sprint 57.12 Day 2-3 / US-5 (was Phase 49.1 placeholder concept)
 *
 * Description:
 *   Sprint 57.12 promotes the Sprint 49.1 placeholder concept to real ship
 *   under AppShellV2 architecture, mirroring verification/index.tsx (Sprint 57.11):
 *
 *     1. Auth gate — if !isAuthenticated → setPostLoginRedirect("/memory")
 *        + <Navigate to="/auth/login" replace />
 *     2. AppShellV2 wrap — pageTitle "Memory"
 *     3. 2-tab nested Routes (URL-addressable):
 *        - /memory          → Navigate to "recent" (default)
 *        - /memory/recent   → MemoryRecentList (layer dropdown + paginated table)
 *        - /memory/by-scope → MemoryByScopeBrowser (5-layer cards + drill-in detail)
 *
 *   Tab nav uses NavLink with isActive callback for active highlighting (same
 *   tabClass helper as verification/index.tsx).
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2-3 / US-5)
 * Last Modified: 2026-05-10
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A1 — gate via <RequireAuth> (was inline isAuthenticated() check)
 *   - 2026-05-10: Initial creation (Sprint 57.12 US-5 Day 2-3 — real ship)
 *
 * Related:
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell)
 *   - frontend/src/features/memory/components/MemoryRecentList.tsx (Day 2-3 §3.1)
 *   - frontend/src/features/memory/components/MemoryByScopeBrowser.tsx (Day 2-3 §3.2)
 *   - frontend/src/pages/verification/index.tsx (sibling pattern)
 */

import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { MemoryByScopeBrowser } from "@/features/memory/components/MemoryByScopeBrowser";
import { MemoryRecentList } from "@/features/memory/components/MemoryRecentList";

const tabClass = ({ isActive }: { isActive: boolean }): string =>
  `px-4 py-2 text-sm font-medium ${
    isActive
      ? "border-b-2 border-primary text-primary"
      : "text-muted-foreground hover:text-foreground"
  }`;

export default function MemoryPage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Memory">
        <nav className="mb-4 flex gap-2 border-b border-border" aria-label="Memory tabs">
          <NavLink to="recent" className={tabClass}>
            Recent
          </NavLink>
          <NavLink to="by-scope" className={tabClass}>
            By Scope
          </NavLink>
        </nav>
        <Routes>
          <Route index element={<Navigate to="recent" replace />} />
          <Route path="recent" element={<MemoryRecentList />} />
          <Route path="by-scope" element={<MemoryByScopeBrowser />} />
          <Route path="*" element={<Navigate to="recent" replace />} />
        </Routes>
      </AppShellV2>
    </RequireAuth>
  );
}
