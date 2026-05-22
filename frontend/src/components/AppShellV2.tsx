/**
 * File: frontend/src/components/AppShellV2.tsx
 * Purpose: V2/V3 layout shell — full-screen grid [sidebar | (Topbar + main)] with dark default.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.20 US-B1 Day 1 (V3 mockup-direct rewrite; preserves prop interface)
 *
 * Description:
 *   Root layout for ALL authenticated routes in V2/V3. Sprint 57.20 Day 1
 *   rewrites the prior flex+sticky-header pattern to a full-screen CSS grid
 *   [240px sidebar | 1fr main column] per mockup `shell.jsx` 1:1.
 *
 *   The previous inline `<header>` (pageTitle h1 + headerActions + bell + UserMenu)
 *   is replaced by the new <Topbar /> component at `components/layout/Topbar.tsx`
 *   which ports the mockup topbar verbatim (breadcrumb + tenant pill + ⌘K +
 *   locale + theme + bell + UserMenu).
 *
 *   Prop interface preserved for backward compat with 14 active pages:
 *     - children: page body content
 *     - pageTitle: passed through to Topbar (precedence over route-derived title)
 *     - headerActions: passed through to Topbar slot
 *     - userMenu: kept in interface for backward compat but Topbar always
 *       renders the canonical <UserMenu /> internally (custom slot ignored — if
 *       any caller needs a custom UserMenu replacement, file an AD)
 *
 *   Sprint 57.19 US-D1+D2 functionality preserved:
 *     - CommandPalette mounted at shell root + ⌘K (mac) / Ctrl+K (win) hotkey
 *     - NotificationsPanel mounted next to Topbar; bell click toggles
 *
 *   Sprint 57.20 US-B3 theme/density mechanism: html root receives
 *   [data-variant="linear"] [data-density="default"] class="dark" defaults
 *   set in main.tsx (not here — shell is layout-only).
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 — verbatim re-point to mockup .app/.main/.content classes (drop Tailwind grid)
 *   - 2026-05-21: Sprint 57.26 — sidebar 240→232px + bg-bg/text-fg tokens + main mockup-content padding (foundation-fidelity)
 *   - 2026-05-18: Sprint 57.21 Day 4 D-DAY4-7 — add `fullBleed` opt-in prop; chat-v2 uses it to drop the default `<main p-6>` inset and render mockup `chat-shell` 3-col edge-to-edge
 *   - 2026-05-17: Sprint 57.20 Day 1 — V3 mockup-direct rewrite (grid layout + extract Topbar component)
 *   - 2026-05-17: Sprint 57.19 US-D1+D2 — mount CommandPalette + bell + NotificationsPanel; add ⌘K hotkey
 *   - 2026-05-10: Sprint 57.13 US-A5 — add data-testid="app-shell" on root (connectivity spec anchor)
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.3)
 *
 * Related:
 *   - reference/design-mockups/shell.jsx + styles.css §.app (canonical visual source)
 *   - frontend/src/components/layout/Topbar.tsx (top bar — Sprint 57.20 US-B1)
 *   - frontend/src/components/Sidebar.tsx (left nav — Sprint 57.20 US-B1 enriched)
 *   - frontend/src/components/topbar/CommandPalette.tsx (⌘K palette, Sprint 57.19 US-D1)
 *   - frontend/src/components/topbar/NotificationsPanel.tsx (bell panel, Sprint 57.19 US-D2)
 *   - frontend/src/components/UserMenu.tsx (avatar dropdown, Sprint 57.19 extended)
 *   - frontend/src/components/AuthShell.tsx (renamed from AppShell.tsx; for /auth/*)
 */

import { type FC, type ReactNode, useEffect, useState } from "react";

import { useUIStore } from "@/store/uiStore";

import { Sidebar } from "./Sidebar";
import { CommandPalette } from "./topbar/CommandPalette";
import { NotificationsPanel } from "./topbar/NotificationsPanel";
import { Topbar } from "./layout/Topbar";

interface AppShellV2Props {
  children: ReactNode;
  pageTitle?: string;
  headerActions?: ReactNode;
  /** Override slot for the topbar avatar/menu area; defaults to canonical <UserMenu /> in Topbar. */
  userMenu?: ReactNode;
  /**
   * Sprint 57.21 Day 4 D-DAY4-7: when true, drops the default `p-6` padding around `<main>`.
   * Required for pages whose own body is a full-bleed grid (e.g. chat-v2 `chat-shell` 3-col).
   * Other pages (dashboards, settings) keep p-6 for consistent inset.
   */
  fullBleed?: boolean;
}

// Mockup placeholder unread count; AD-NotificationsPanel-Backend-Feed Sprint 57.21+ wires real feed.
const FIXTURE_UNREAD_COUNT = 3;

export const AppShellV2: FC<AppShellV2Props> = ({
  children,
  pageTitle,
  headerActions,
  userMenu,
  fullBleed = false,
}) => {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  // Global ⌘K (mac) / Ctrl+K (win/linux) hotkey to toggle CommandPalette (Sprint 57.19 US-D1).
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div
      data-testid="app-shell"
      className="app"
      data-collapsed={sidebarCollapsed || undefined}
    >
      <Sidebar />
      <div className="main">
        <Topbar
          pageTitle={pageTitle}
          headerActions={headerActions}
          userMenu={userMenu}
          onOpenPalette={() => setPaletteOpen(true)}
          onToggleNotifs={() => setNotifOpen((p) => !p)}
          unreadCount={FIXTURE_UNREAD_COUNT}
        />
        <NotificationsPanel open={notifOpen} onClose={() => setNotifOpen(false)} />
        <main className={fullBleed ? "content fullbleed" : "content"}>{children}</main>
      </div>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
};
