/**
 * File: frontend/src/components/AppShellV2.tsx
 * Purpose: V2 layout shell — sidebar + main column with header (per-page title + user menu slot).
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.8 US-1.3 Day 1
 *
 * Description:
 *   Root layout for ALL authenticated routes in V2. Adopts V1-style admin
 *   portal pattern (sidebar left + main right) replacing Sprint 57.7 minimal
 *   header-only AppShell (renamed AuthShell.tsx, reserved for /auth/*).
 *
 *   Layout:
 *     <div flex>
 *       <Sidebar />            ← consume routes.config + uiStore
 *       <div flex-col>
 *         <header>
 *           <h1>{pageTitle}</h1>
 *           <UserMenu slot />   ← Day 2 US-2 will fill (placeholder div for now)
 *         </header>
 *         <main>{children}</main>
 *       </div>
 *     </div>
 *
 *   Per-page title prop drives <h1> rendering. headerActions slot accepts
 *   per-page action buttons (e.g. cost-dashboard month picker).
 *
 *   Tailwind utilities only (per .claude/rules/frontend-react.md — no inline
 *   style). Sticky sidebar via Sidebar.tsx itself; main column scrolls.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-A5 — add data-testid="app-shell" on root (connectivity spec anchor)
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.3)
 *
 * Related:
 *   - frontend/src/components/Sidebar.tsx (left nav)
 *   - frontend/src/components/UserMenu.tsx (Day 2 US-2 — header right slot)
 *   - frontend/src/components/AuthShell.tsx (renamed from AppShell.tsx;
 *     reserved for /auth/* routes per Day 0 Decision B1)
 */

import type { FC, ReactNode } from "react";

import { Sidebar } from "./Sidebar";
import { UserMenu } from "./UserMenu";

interface AppShellV2Props {
  children: ReactNode;
  /** Page title rendered as <h1> in header */
  pageTitle: string;
  /** Optional per-page action buttons (right of title, left of user menu) */
  headerActions?: ReactNode;
  /**
   * Optional user menu slot override. Default = <UserMenu /> (Sprint 57.8 US-2.2:
   * auto-wired to consume Sprint 57.7 IAM JWT). Pass null to suppress.
   */
  userMenu?: ReactNode;
}

export const AppShellV2: FC<AppShellV2Props> = ({
  children,
  pageTitle,
  headerActions,
  userMenu,
}) => {
  const userMenuSlot = userMenu === undefined ? <UserMenu /> : userMenu;
  return (
    <div data-testid="app-shell" className="flex min-h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur">
          <h1 className="text-lg font-semibold tracking-tight">{pageTitle}</h1>
          <div className="flex items-center gap-3">
            {headerActions && <div className="flex items-center gap-2">{headerActions}</div>}
            {userMenuSlot}
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
};
