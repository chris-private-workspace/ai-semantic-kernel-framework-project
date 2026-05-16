/**
 * File: frontend/src/components/Sidebar.tsx
 * Purpose: Left sidebar nav consuming routes.config single-source registry.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.8 US-1.2 Day 1; Sprint 57.18 US-C3 refactor
 *
 * Description:
 *   Fixed-left sidebar nav with 6 category headers (Operations / Business /
 *   Governance / Observability / Resources / Admin) consumed from CATEGORY_ORDER
 *   in routes.config.ts (Sprint 57.18 refactor).
 *
 *   Per-entry visual states:
 *     - active=true + no flags: standard link (Sprint 57.13 ship target)
 *     - active=true + proposed=true: standard link + blue PROP badge
 *       (Sprint 57.18 stub → ComingSoonPlaceholder; Sprint 57.19+ real port)
 *     - active=false + designed=true: disabled span + yellow DRAFT badge
 *     - active=false + (no flags): disabled span + "Coming soon" tooltip (gray)
 *
 *   Per-category header: category label + optional "N PROP" count badge
 *   if any entries in that category have proposed=true.
 *
 *   Collapse states:
 *     - sidebarCollapsed=false: 240px wide, full label + icon + badges, section headers
 *     - sidebarCollapsed=true: 64px wide, icon-only, section headers + badges hidden
 *
 *   Active page highlighted via useLocation().pathname matching r.path.
 *
 *   Mobile responsiveness (<md=768px):
 *     - Plan §Risks A: full mobile drawer overlay deferred to Phase 58.x
 *       (need shadcn Sheet + backdrop interaction) — Sprint 57.8 ships
 *       desktop-first sidebar; mobile = collapsed icon-only is acceptable
 *       degradation (still functional, sidebar 64px doesn't dominate viewport).
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-16
 *
 * Modification History:
 *   - 2026-05-16: Sprint 57.18 US-C3 — PROP/DRAFT badge per entry + propCount header (closes Phase 1 mockup integration)
 *   - 2026-05-16: Sprint 57.18 US-C1 cascade — CATEGORY_ORDER imported from routes.config (was local "settings" const)
 *   - 2026-05-10: Sprint 57.13 US-B5 — nav labels + category headers + aria labels via i18n t()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.2)
 *
 * Related:
 *   - frontend/src/routes.config.ts (ROUTES + CATEGORY_ORDER single-source; nameKey for i18n)
 *   - frontend/src/components/ComingSoonPlaceholder.tsx (PROP/DRAFT stub renderer)
 *   - frontend/src/store/uiStore.ts (sidebarCollapsed state)
 *   - frontend/src/components/AppShellV2.tsx (host component)
 *   - frontend/src/i18n/locales/{en,zh-TW}/common.json (nav.* + shell.* + nav.category.* keys)
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { CATEGORY_ORDER, ROUTES, type RouteEntry } from "@/routes.config";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/lib/utils";

const BADGE_BASE_CLASS =
  "ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase";

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
          const propCount = entries.filter((r) => r.proposed).length;
          return (
            <div key={category} className="mb-4">
              {!sidebarCollapsed && (
                <div className="mb-1 flex items-center justify-between px-3 text-xs font-medium uppercase text-muted-foreground">
                  <span>{t(`nav.category.${category}`)}</span>
                  {propCount > 0 && (
                    <span className={cn(BADGE_BASE_CLASS, "ml-0 bg-thinking/16 text-thinking")}>
                      {propCount} PROP
                    </span>
                  )}
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

const renderEntryBadge = (entry: RouteEntry, collapsed: boolean) => {
  if (collapsed) return null;
  if (entry.proposed) {
    return (
      <span className={cn(BADGE_BASE_CLASS, "bg-thinking/16 text-thinking")}>
        PROP
      </span>
    );
  }
  if (entry.designed && !entry.active) {
    return (
      <span className={cn(BADGE_BASE_CLASS, "bg-warning/16 text-warning")}>
        DRAFT
      </span>
    );
  }
  return null;
};

const SidebarItem: FC<SidebarItemProps> = ({ entry, isActive, collapsed }) => {
  const { t } = useTranslation("common");
  const Icon = entry.icon;
  const label = t(entry.nameKey, entry.name);
  const baseClass = cn(
    "flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors",
    collapsed && "justify-center px-2",
  );
  const badge = renderEntryBadge(entry, collapsed);

  if (!entry.active) {
    return (
      <li>
        <span
          className={cn(baseClass, "cursor-not-allowed text-muted-foreground/60")}
          title={t("shell.comingSoon")}
          aria-disabled="true"
        >
          <Icon size={16} />
          {!collapsed && <span>{label}</span>}
          {badge}
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
        {badge}
      </Link>
    </li>
  );
};
