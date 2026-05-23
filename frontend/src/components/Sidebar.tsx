/**
 * File: frontend/src/components/Sidebar.tsx
 * Purpose: Left sidebar — brand + tenant switcher + 6-category nav + bottom user identity card.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.29 US-B3 (verbatim re-point — consume mockup sidebar classes directly)
 *
 * Description:
 *   Verbatim re-point of `reference/design-mockups/shell.jsx` Sidebar — the
 *   component now consumes the mockup CSS class names from `styles-mockup.css`
 *   directly (`.sidebar`, `.sidebar-head`, `.brand-mark`, `.nav-item`, …) instead
 *   of re-expressing them as Tailwind utilities. Four stacked sections:
 *
 *     1. Sidebar head — brand mark + brand text (`.brand-name` / `.brand-sub`) +
 *        the production-only collapse-toggle button (mockup has none — kept)
 *     2. Tenant switcher pill — `.tenant-switcher` avatar + name + meta + chevron
 *     3. Nav body — `.nav` with 6 `.nav-section` headers consumed from
 *        CATEGORY_ORDER; per-entry `.nav-item` + `.nav-icon` + `.nav-label` +
 *        `.nav-badge` (PROP/DRAFT/SOON)
 *     4. Sidebar foot — `.user-card` gradient avatar + display name + role
 *
 *   Visual layer (mockup class names + inline-style literals for nav-badge
 *   colours and the foot avatar gradient) is copied verbatim. Component-logic
 *   layer is the production model: `react-router` `<Link>` + `useLocation()`
 *   active state → `data-active` on `.nav-item`; `routes.config.ts` ROUTES +
 *   CATEGORY_ORDER 6-group registry (Lucide icon components); `useUIStore`
 *   collapse; i18n `nav.*` keys.
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 1)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: FIX-009 — collapsed-state sidebar-head column-stack (toggle button no longer clipped past 56px boundary)
 *   - 2026-05-22: Sprint 57.29 US-B3 — verbatim re-point to mockup .sidebar/.nav-* classes (drop Tailwind translation)
 *   - 2026-05-17: Sprint 57.20 Day 1 — mockup shell.jsx port (tenant switcher + bottom user-card)
 *   - 2026-05-16: Sprint 57.18 US-C3 — PROP/DRAFT badge per entry + propCount header
 *   - 2026-05-16: Sprint 57.18 US-C1 cascade — CATEGORY_ORDER imported from routes.config
 *   - 2026-05-10: Sprint 57.13 US-B5 — nav labels + category headers + aria labels via i18n t()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-1.2)
 *
 * Related:
 *   - reference/design-mockups/shell.jsx §Sidebar (canonical visual source)
 *   - frontend/src/styles-mockup.css §.sidebar / .nav-item / .tenant-switcher / .user-card
 *   - frontend/src/routes.config.ts (ROUTES + CATEGORY_ORDER single-source)
 *   - frontend/src/features/auth/store/authStore.ts (user identity for bottom card)
 *   - frontend/src/store/uiStore.ts (sidebarCollapsed state)
 *   - frontend/src/components/AppShellV2.tsx (host component)
 *   - frontend/src/i18n/locales/{en,zh-TW}/common.json (nav.* + shell.* + sidebar.* keys)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup shell.jsx visual-layer literals (nav-badge tints + foot avatar gradient) copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import { ChevronDown, ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";
import type { CSSProperties, FC } from "react";
import { Fragment } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { useAuthStore } from "@/features/auth/store/authStore";
import { CATEGORY_ORDER, ROUTES, type RouteEntry } from "@/routes.config";
import { useUIStore } from "@/store/uiStore";

// Verbatim mockup `shell.jsx` nav-badge inline-style literals (visual layer — copied, not translated).
const NAV_BADGE_PROP_STYLE: CSSProperties = {
  background: "oklch(from var(--thinking) l c h / 0.16)",
  color: "var(--thinking)",
  fontSize: 9,
};
const NAV_BADGE_DRAFT_STYLE: CSSProperties = {
  background: "oklch(from var(--warning) l c h / 0.16)",
  color: "var(--warning)",
  fontSize: 9,
};
const NAV_BADGE_SOON_STYLE: CSSProperties = { fontSize: 9 };

// Verbatim mockup `shell.jsx` sidebar-foot avatar gradient (visual layer literal).
const FOOT_AVATAR_STYLE: CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: "50%",
  background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
  color: "white",
  fontSize: 11,
  fontWeight: 600,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

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
      className="sidebar"
      data-collapsed={sidebarCollapsed || undefined}
      aria-label={t("shell.primaryNavigation")}
    >
      {/* Sidebar head — brand mark + brand text + production-only collapse toggle.
          FIX-009 (2026-05-24): When collapsed, switch to column-stack so the
          toggle button stays inside the 56px sidebar column (instead of being
          pushed past the right edge by row-flex + marginLeft:auto + 26px
          brand-mark in only 28px of usable inner width). Expanded layout is
          untouched (style is undefined when !sidebarCollapsed). */}
      <div
        className="sidebar-head"
        style={
          sidebarCollapsed
            ? { flexDirection: "column", height: "auto", padding: 8, gap: 6 }
            : undefined
        }
      >
        <div className="brand-mark" aria-hidden="true" />
        {!sidebarCollapsed && (
          <Link to="/" className="brand-text grow" style={{ minWidth: 0 }}>
            <div className="brand-name">{t("shell.brand", "IPA Platform V2")}</div>
            <div className="brand-sub">{t("shell.brandSub", "LOOP-FIRST")}</div>
          </Link>
        )}
        <button
          type="button"
          onClick={toggleSidebar}
          className="btn ghost"
          data-size="sm"
          style={{ marginLeft: "auto" }}
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
          className="tenant-switcher"
          title={t("sidebar.tenantSwitcher", "Switch tenant")}
          data-testid="sidebar-tenant-switcher"
        >
          <div className="tenant-avatar">{FIXTURE_TENANT.initial}</div>
          <div className="tenant-text grow" style={{ minWidth: 0 }}>
            <div className="tenant-name">{FIXTURE_TENANT.name}</div>
            <div className="tenant-meta">{FIXTURE_TENANT.meta}</div>
          </div>
          <ChevronDown size={13} />
        </button>
      )}

      {/* Nav body */}
      <nav className="nav" aria-label={t("shell.mainNav")}>
        {CATEGORY_ORDER.map((category) => {
          const entries = ROUTES.filter((r) => r.category === category);
          if (entries.length === 0) return null;
          const propCount = entries.filter((r) => r.proposed).length;
          return (
            <Fragment key={category}>
              {!sidebarCollapsed && (
                <div className="nav-section">
                  <span>{t(`nav.category.${category}`)}</span>
                  {propCount > 0 && (
                    <span className="nav-badge" style={NAV_BADGE_PROP_STYLE}>
                      {propCount} PROP
                    </span>
                  )}
                </div>
              )}
              {entries.map((r) => (
                <SidebarItem
                  key={r.path}
                  entry={r}
                  isActive={location.pathname === r.path}
                  collapsed={sidebarCollapsed}
                />
              ))}
            </Fragment>
          );
        })}
      </nav>

      {/* Sidebar foot — user identity card */}
      {!sidebarCollapsed && (
        <div className="sidebar-foot">
          <div className="user-card">
            <div style={FOOT_AVATAR_STYLE}>{userInitials}</div>
            <div className="grow" style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500 }}>{userDisplay}</div>
              <div
                style={{
                  fontSize: 10.5,
                  color: "var(--fg-subtle)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                {userRole}
              </div>
            </div>
            <MoreHorizontal size={14} className="subtle" />
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
      <span className="nav-badge" style={NAV_BADGE_PROP_STYLE}>
        PROP
      </span>
    );
  }
  if (entry.designed && !entry.active) {
    return (
      <span className="nav-badge" style={NAV_BADGE_DRAFT_STYLE}>
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

  // Inactive + not-designed: non-navigable item with SOON badge (verbatim mockup style).
  if (!entry.active && !entry.designed) {
    return (
      <div
        className="nav-item"
        title={t("shell.comingSoon")}
        aria-disabled="true"
        style={{ opacity: 0.55, cursor: "not-allowed" }}
      >
        <Icon size={15} className="nav-icon" />
        {!collapsed && <span className="nav-label">{label}</span>}
        {!collapsed && (
          <span className="nav-badge" style={NAV_BADGE_SOON_STYLE}>
            SOON
          </span>
        )}
      </div>
    );
  }

  // Designed-but-inactive: navigable preview not allowed (no <Route>); render as disabled DRAFT.
  if (!entry.active) {
    return (
      <div
        className="nav-item"
        title={t("shell.comingSoon")}
        aria-disabled="true"
        style={{ opacity: 0.55, cursor: "not-allowed" }}
      >
        <Icon size={15} className="nav-icon" />
        {!collapsed && <span className="nav-label">{label}</span>}
        {renderEntryBadge(entry, collapsed)}
      </div>
    );
  }

  return (
    <Link
      to={entry.path}
      className="nav-item"
      data-active={isActive || undefined}
      title={collapsed ? label : undefined}
      aria-current={isActive ? "page" : undefined}
    >
      <Icon size={15} className="nav-icon" />
      {!collapsed && <span className="nav-label">{label}</span>}
      {renderEntryBadge(entry, collapsed)}
    </Link>
  );
};
