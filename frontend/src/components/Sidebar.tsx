/**
 * File: frontend/src/components/Sidebar.tsx
 * Purpose: Left sidebar — brand + tenant switcher + 6-category nav + bottom user identity card.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.20 Day 1 US-B1 (mockup shell.jsx 1:1 enrichment)
 *
 * Description:
 *   Mockup-direct port of `reference/design-mockups/shell.jsx` Sidebar.
 *   Four stacked sections (top → bottom):
 *
 *     1. Sidebar head — brand mark + brand text (name "IPA Platform V2" + sub
 *        "LOOP-FIRST" badge per mockup)
 *     2. Tenant switcher pill — avatar + tenant name + tenant_id+plan meta +
 *        chevron (Sprint 57.20: fixture; AD-UserMenu-Tenant-Switch Sprint
 *        57.21+ wires real)
 *     3. Nav body — 6 category headers (Operations / Business / Governance /
 *        Observability / Resources / Admin) consumed from CATEGORY_ORDER in
 *        routes.config.ts; per-entry PROP/DRAFT/SOON badges (Sprint 57.18)
 *     4. Sidebar foot — user identity card (gradient avatar + display name +
 *        role; consumes authStore.user)
 *
 *   Active page highlighted via useLocation().pathname matching r.path.
 *
 *   Collapse state retained from Sprint 57.8 (uiStore.sidebarCollapsed).
 *   Collapsed (64px): icon-only nav, tenant switcher + user card hidden.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-17
 *
 * Modification History:
 *   - 2026-05-17: Sprint 57.20 Day 1 — mockup shell.jsx port (tenant switcher + bottom user-card)
 *   - 2026-05-16: Sprint 57.18 US-C3 — PROP/DRAFT badge per entry + propCount header
 *   - 2026-05-16: Sprint 57.18 US-C1 cascade — CATEGORY_ORDER imported from routes.config
 *   - 2026-05-10: Sprint 57.13 US-B5 — nav labels + category headers + aria labels via i18n t()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.2)
 *
 * Related:
 *   - reference/design-mockups/shell.jsx §Sidebar + .sidebar-head + .tenant-switcher + .sidebar-foot
 *   - frontend/src/routes.config.ts (ROUTES + CATEGORY_ORDER single-source)
 *   - frontend/src/features/auth/store/authStore.ts (user identity for bottom card)
 *   - frontend/src/store/uiStore.ts (sidebarCollapsed state)
 *   - frontend/src/components/AppShellV2.tsx (host component)
 *   - frontend/src/i18n/locales/{en,zh-TW}/common.json (nav.* + shell.* + sidebar.* keys)
 */

import { ChevronDown, ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { useAuthStore } from "@/features/auth/store/authStore";
import { cn } from "@/lib/utils";
import { CATEGORY_ORDER, ROUTES, type RouteEntry } from "@/routes.config";
import { useUIStore } from "@/store/uiStore";

const BADGE_BASE_CLASS =
  "ml-auto rounded px-1.5 py-0.5 text-[9px] font-medium uppercase";

// Sprint 57.20 fixture (matches mockup shell.jsx tenant-switcher); AD-UserMenu-Tenant-Switch Sprint 57.21+ wires real
const FIXTURE_TENANT = { initial: "A", name: "acme-prod", meta: "tenant_01h9a2 · Pro" };

export const Sidebar: FC = () => {
  const { t } = useTranslation("common");
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const roles = useAuthStore((s) => s.roles);

  const userDisplay = user?.display_name?.trim() || user?.email || t("sidebar.guest", "Guest");
  const userInitials = userDisplay.charAt(0).toUpperCase();
  const userRole = roles[0] ?? "operator";

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border bg-bg-1",
        "transition-[width] duration-200 ease-out",
        sidebarCollapsed ? "w-16" : "w-60",
      )}
      aria-label={t("shell.primaryNavigation")}
    >
      {/* Sidebar head — brand mark + brand text + collapse toggle */}
      <div className="flex h-14 items-center gap-2.5 border-b border-border px-3.5">
        <div className="h-7 w-7 shrink-0 rounded-md bg-gradient-to-br from-primary to-thinking" aria-hidden="true" />
        {!sidebarCollapsed && (
          <Link to="/" className="min-w-0 grow leading-tight hover:opacity-80">
            <div className="truncate text-sm font-semibold text-foreground">{t("shell.brand", "IPA Platform V2")}</div>
            <div className="truncate font-mono text-[10px] uppercase tracking-wider text-fg-muted">
              {t("shell.brandSub", "LOOP-FIRST")}
            </div>
          </Link>
        )}
        <button
          type="button"
          onClick={toggleSidebar}
          className="ml-auto inline-flex h-7 w-7 shrink-0 items-center justify-center rounded text-fg-muted hover:bg-bg-2"
          aria-label={sidebarCollapsed ? t("shell.expandSidebar") : t("shell.collapseSidebar")}
          data-testid="sidebar-toggle"
        >
          {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Tenant switcher pill */}
      {!sidebarCollapsed && (
        <button
          type="button"
          className={cn(
            "mx-2 mt-2 mb-1 flex items-center gap-2 rounded border border-border bg-bg-2 px-2 py-1.5",
            "text-left text-foreground hover:bg-bg-3",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
          title={t("sidebar.tenantSwitcher", "Switch tenant")}
          data-testid="sidebar-tenant-switcher"
        >
          <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded bg-primary text-[11px] font-semibold text-primary-foreground">
            {FIXTURE_TENANT.initial}
          </span>
          <span className="min-w-0 grow">
            <span className="block truncate text-xs font-medium">{FIXTURE_TENANT.name}</span>
            <span className="block truncate font-mono text-[10px] text-fg-muted">{FIXTURE_TENANT.meta}</span>
          </span>
          <ChevronDown size={12} className="shrink-0 text-fg-muted" />
        </button>
      )}

      {/* Nav body */}
      <nav className="flex-1 overflow-y-auto py-2" aria-label={t("shell.mainNav")}>
        {CATEGORY_ORDER.map((category) => {
          const entries = ROUTES.filter((r) => r.category === category);
          if (entries.length === 0) return null;
          const propCount = entries.filter((r) => r.proposed).length;
          return (
            <div key={category} className="mb-3">
              {!sidebarCollapsed && (
                <div className="mb-1 flex items-center justify-between px-3 text-[10px] font-medium uppercase tracking-wider text-fg-subtle">
                  <span>{t(`nav.category.${category}`)}</span>
                  {propCount > 0 && (
                    <span className={cn(BADGE_BASE_CLASS, "ml-0 bg-thinking/16 text-thinking")}>
                      {propCount} PROP
                    </span>
                  )}
                </div>
              )}
              <ul className="space-y-0.5 px-2">
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

      {/* Sidebar foot — user identity card */}
      {!sidebarCollapsed && (
        <div className="border-t border-border p-2.5">
          <div className="flex items-center gap-2 rounded px-1.5 py-1.5 hover:bg-bg-2">
            <span
              className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-warning to-memory text-[11px] font-semibold text-white"
              aria-hidden="true"
            >
              {userInitials}
            </span>
            <div className="min-w-0 grow">
              <div className="truncate text-xs font-medium text-foreground">{userDisplay}</div>
              <div className="truncate font-mono text-[10px] text-fg-muted">{userRole}</div>
            </div>
            <MoreHorizontal size={14} className="shrink-0 text-fg-subtle" />
          </div>
        </div>
      )}
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
    "flex items-center gap-2.5 rounded px-3 py-1.5 text-sm transition-colors",
    collapsed && "justify-center px-2",
  );
  const badge = renderEntryBadge(entry, collapsed);

  if (!entry.active) {
    return (
      <li>
        <span
          className={cn(baseClass, "cursor-not-allowed text-fg-muted/60")}
          title={t("shell.comingSoon")}
          aria-disabled="true"
        >
          <Icon size={15} />
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
            ? "bg-primary-soft font-medium text-foreground"
            : "text-fg-muted hover:bg-bg-2 hover:text-foreground",
        )}
        title={collapsed ? label : undefined}
        aria-current={isActive ? "page" : undefined}
      >
        <Icon size={15} />
        {!collapsed && <span>{label}</span>}
        {badge}
      </Link>
    </li>
  );
};
