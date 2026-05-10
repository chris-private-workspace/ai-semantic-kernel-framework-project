/**
 * File: frontend/src/components/Sidebar.tsx
 * Purpose: Left sidebar nav consuming routes.config single-source registry.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.8 US-1.2 Day 1
 *
 * Description:
 *   Fixed-left sidebar nav with categorized sections (Operations / Admin /
 *   Settings). Reads ROUTES from routes.config.ts and groups by category.
 *
 *   States:
 *     - sidebarCollapsed=false: 240px wide, full label + icon, section headers
 *     - sidebarCollapsed=true: 64px wide, icon-only, section headers hidden
 *
 *   Active page highlighted via useLocation().pathname matching r.path.
 *   Inactive entries (active=false) rendered grayed + cursor-not-allowed
 *   + title tooltip "Coming soon".
 *
 *   Toggle button at top reads/writes via useUIStore (Zustand persist).
 *
 *   Mobile responsiveness (<md=768px):
 *     - Plan §Risks A: full mobile drawer overlay deferred to Phase 58.x
 *       (need shadcn Sheet + backdrop interaction) — Sprint 57.8 ships
 *       desktop-first sidebar; mobile = collapsed icon-only is acceptable
 *       degradation (still functional, sidebar 64px doesn't dominate viewport).
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B5 — nav labels + category headers + aria labels via i18n t()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.2)
 *
 * Related:
 *   - frontend/src/routes.config.ts (ROUTES single-source; nameKey for i18n)
 *   - frontend/src/store/uiStore.ts (sidebarCollapsed state)
 *   - frontend/src/components/AppShellV2.tsx (host component)
 *   - frontend/src/i18n/locales/{en,zh-TW}/common.json (nav.* + shell.* keys)
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { ROUTES, type RouteCategory, type RouteEntry } from "@/routes.config";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

const CATEGORY_ORDER: RouteCategory[] = ["operations", "admin", "settings"];

export const Sidebar: FC = () => {
  const { t } = useTranslation("common");
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "sticky top-0 h-screen border-r border-border bg-background flex flex-col",
        "transition-[width] duration-200 ease-out",
        sidebarCollapsed ? "w-16" : "w-60",
      )}
      aria-label={t("shell.primaryNavigation")}
    >
      {/* Header / brand + collapse toggle */}
      <div className="flex h-14 items-center justify-between border-b border-border px-3">
        {!sidebarCollapsed && (
          <Link to="/" className="font-semibold tracking-tight hover:opacity-80">
            {t("shell.brand")}
          </Link>
        )}
        <button
          type="button"
          onClick={toggleSidebar}
          className="ml-auto inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted"
          aria-label={sidebarCollapsed ? t("shell.expandSidebar") : t("shell.collapseSidebar")}
        >
          {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav body */}
      <nav className="flex-1 overflow-y-auto py-3" aria-label={t("shell.mainNav")}>
        {CATEGORY_ORDER.map((category) => {
          const entries = ROUTES.filter((r) => r.category === category);
          if (entries.length === 0) return null;
          return (
            <div key={category} className="mb-4">
              {!sidebarCollapsed && (
                <div className="mb-1 px-3 text-xs font-medium uppercase text-muted-foreground">
                  {t(`nav.category.${category}`)}
                </div>
              )}
              <ul className="space-y-1 px-2">
                {entries.map((r) => (
                  <SidebarItem
                    key={r.path}
                    entry={r}
                    isActive={location.pathname === r.path}
                    collapsed={sidebarCollapsed}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </nav>
    </aside>
  );
};

interface SidebarItemProps {
  entry: RouteEntry;
  isActive: boolean;
  collapsed: boolean;
}

const SidebarItem: FC<SidebarItemProps> = ({ entry, isActive, collapsed }) => {
  const { t } = useTranslation("common");
  const Icon = entry.icon;
  const label = t(entry.nameKey, entry.name);
  const baseClass = cn(
    "flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors",
    collapsed && "justify-center px-2",
  );

  if (!entry.active) {
    return (
      <li>
        <span
          className={cn(
            baseClass,
            "cursor-not-allowed text-muted-foreground/60",
          )}
          title={t("shell.comingSoon")}
          aria-disabled="true"
        >
          <Icon size={16} />
          {!collapsed && <span>{label}</span>}
        </span>
      </li>
    );
  }

  return (
    <li>
      <Link
        to={entry.path}
        className={cn(
          baseClass,
          isActive
            ? "bg-accent font-medium text-accent-foreground"
            : "text-foreground hover:bg-muted",
        )}
        title={collapsed ? label : undefined}
        aria-current={isActive ? "page" : undefined}
      >
        <Icon size={16} />
        {!collapsed && <span>{label}</span>}
      </Link>
    </li>
  );
};
