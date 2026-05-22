/**
 * File: frontend/src/components/layout/Topbar.tsx
 * Purpose: Top horizontal bar — breadcrumb + tenant pill + ⌘K search + locale + theme + bell + UserMenu avatar.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.20 US-B1 Day 1 (NEW; mockup shell.jsx 1:1 port)
 *
 * Description:
 *   Verbatim re-point of `reference/design-mockups/shell.jsx` Topbar — the
 *   component now consumes mockup CSS class names from `styles-mockup.css`
 *   directly (`.topbar`, `.crumb`, `.here`, `.route-pill`, `.tenant-pill`,
 *   `.cmdk`, `.kbd`, `.avatar`) instead of re-expressing them as Tailwind
 *   utilities. Component-logic layer unchanged: react-router useLocation(),
 *   useTheme(), useAuthStore, i18n toggleLocale, all props/testids/a11y attrs.
 *
 *   Composition (left → right):
 *     1. Breadcrumb (.crumb): route title (.here h1) + route path pill (.route-pill)
 *     2. Tenant pill (.tenant-pill): "acme-prod · <role>" with green .dot
 *     3. Spacer (.topbar-spacer)
 *     4. ⌘K cmdk div (.cmdk): clickable + Enter-keyed → CommandPalette open
 *     5. Locale toggle — inline-style literals from mockup (visual layer)
 *     6. Theme toggle — Button ghost sm (mockup uses Button variant ghost)
 *     7. Divider — inline-style literal from mockup (visual layer)
 *     8. Bell — Button ghost sm with unread badge (inline-style literal)
 *     9. UserMenu (.avatar) at end
 *
 *   pageTitle prop: takes precedence over route-derived title.
 *   headerActions prop: rendered between spacer and ⌘K (backward compat).
 *
 * Created: 2026-05-17 (Sprint 57.20 Day 1 US-B1)
 * Last Modified: 2026-05-22
 *
 * Modification History:
 *   - 2026-05-22: Sprint 57.29 US-B4 — verbatim re-point to mockup .topbar/.cmdk classes (drop Tailwind translation)
 *   - 2026-05-17: Initial creation (Sprint 57.20 Day 1) — mockup shell.jsx port
 *
 * Related:
 *   - reference/design-mockups/shell.jsx §Topbar (canonical visual source)
 *   - reference/design-mockups/styles.css / frontend/src/styles-mockup.css (class definitions)
 *   - frontend/src/components/AppShellV2.tsx (host)
 *   - frontend/src/components/UserMenu.tsx (avatar dropdown — Sprint 57.19)
 *   - frontend/src/components/topbar/CommandPalette.tsx (⌘K — Sprint 57.19 US-D1)
 *   - frontend/src/components/topbar/NotificationsPanel.tsx (bell — Sprint 57.19 US-D2)
 *   - frontend/src/components/ThemeProvider.tsx (theme state)
 *   - frontend/src/routes.config.ts (ROUTES single-source for breadcrumb)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup shell.jsx visual-layer literals (locale toggle button, divider, bell badge, avatar, notifs badge) copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import { type CSSProperties, type FC, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";

import { Icon } from "@/components/mockup-ui";
import { useTheme } from "@/components/ThemeProvider";
import { UserMenu } from "@/components/UserMenu";
import { useAuthStore } from "@/features/auth/store/authStore";
import { LOCALE_STORAGE_KEY } from "@/i18n";
import { ROUTES } from "@/routes.config";

// Verbatim mockup shell.jsx inline-style literals — locale toggle button (visual layer).
const LOCALE_BTN_STYLE: CSSProperties = {
  height: 28, minWidth: 28, padding: "0 8px",
  background: "transparent", border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)", color: "var(--fg-muted)",
  fontSize: 11, fontWeight: 500, fontFamily: "var(--font-mono)",
  letterSpacing: "0.04em", cursor: "pointer",
  display: "inline-flex", alignItems: "center", gap: 4,
};

// Verbatim mockup shell.jsx inline-style literals — divider between theme-toggle and bell.
const DIVIDER_STYLE: CSSProperties = {
  width: 1, height: 18, background: "var(--border)", margin: "0 4px", display: "inline-block",
};

// Verbatim mockup shell.jsx inline-style literals — notifsAnchorRef span wrapper.
const NOTIFS_ANCHOR_STYLE: CSSProperties = { position: "relative" };

// Verbatim mockup shell.jsx inline-style literals — unread badge on bell button.
const NOTIFS_BADGE_STYLE: CSSProperties = {
  position: "absolute", top: 3, right: 3,
  minWidth: 14, height: 14, padding: "0 3px", borderRadius: 7,
  background: "var(--warning)", color: "oklch(0.18 0.02 60)",
  fontSize: 9, fontWeight: 700, fontFamily: "var(--font-mono)",
  display: "inline-flex", alignItems: "center", justifyContent: "center",
  boxShadow: "0 0 0 2px var(--bg-1)",
};

// Verbatim mockup shell.jsx inline-style literals — cmdk div cursor.
const CMDK_STYLE: CSSProperties = { cursor: "pointer" };


interface TopbarProps {
  pageTitle?: string;
  headerActions?: ReactNode;
  /** Override slot for the avatar/menu area (rare; defaults to canonical <UserMenu />). */
  userMenu?: ReactNode;
  onOpenPalette: () => void;
  onToggleNotifs: () => void;
  unreadCount?: number;
}

export const Topbar: FC<TopbarProps> = ({
  pageTitle,
  headerActions,
  userMenu,
  onOpenPalette,
  onToggleNotifs,
  unreadCount = 0,
}) => {
  const { t, i18n } = useTranslation("common");
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const roles = useAuthStore((s) => s.roles);

  const matchedRoute = ROUTES.find((r) => r.path === location.pathname);
  const derivedTitle = matchedRoute ? t(matchedRoute.nameKey, matchedRoute.name) : "";
  const title = pageTitle ?? derivedTitle;
  const pathPill = location.pathname;

  // Tenant pill: fixture name + first role; AD-UserMenu-Tenant-Switch Sprint 57.21+ wires real tenant API
  const tenantName = "acme-prod";
  const roleLabel = roles[0] ?? "operator";

  const currentLng = i18n.resolvedLanguage ?? i18n.language;
  const toggleLocale = (): void => {
    const next = currentLng === "en" ? "zh-TW" : "en";
    try {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, next);
    } catch {
      /* localStorage unavailable (private mode) — changeLanguage still works for the session */
    }
    void i18n.changeLanguage(next);
  };
  const localeShort = currentLng === "en" ? "EN" : "中";

  return (
    <header className="topbar" data-testid="topbar">
      {/* Breadcrumb — h1 preserves page-title-is-h1 a11y contract */}
      <div className="crumb">
        <h1 className="here" style={{ margin: 0 }}>{title}</h1>
        {pathPill && <span className="route-pill">{pathPill}</span>}
      </div>

      {/* Tenant pill */}
      <span className="tenant-pill">
        <span className="dot" aria-hidden="true" />
        {tenantName} · {roleLabel}
      </span>

      {/* Spacer */}
      <div className="topbar-spacer" />

      {/* Optional header actions slot (backward compat) */}
      {headerActions && <div className="row">{headerActions}</div>}

      {/* ⌘K cmdk pill — mockup uses a div role="button" */}
      <div
        className="cmdk"
        role="button"
        tabIndex={0}
        onClick={onOpenPalette}
        onKeyDown={(e) => { if (e.key === "Enter") onOpenPalette(); }}
        style={CMDK_STYLE}
        title={t("topbar.openPalette", "Open command palette")}
        data-testid="topbar-cmdk"
      >
        <Icon name="search" size={13} />
        <span className="grow">{t("shell.search", "Search…")}</span>
        <span className="kbd">⌘K</span>
      </div>

      {/* Locale toggle — verbatim mockup inline-style button */}
      <button
        type="button"
        onClick={toggleLocale}
        style={LOCALE_BTN_STYLE}
        title={currentLng === "en" ? "切換到繁體中文" : "Switch to English"}
        aria-label={currentLng === "en" ? "Switch to Traditional Chinese" : "Switch to English"}
        data-testid="topbar-locale"
      >
        <Icon name="globe" size={12} />
        <span>{localeShort}</span>
      </button>

      {/* Theme toggle — mockup uses Button variant ghost size sm */}
      <button
        type="button"
        onClick={toggleTheme}
        className="btn ghost"
        data-size="sm"
        title={theme === "dark"
          ? t("topbar.themeLight", "Switch to light theme")
          : t("topbar.themeDark", "Switch to dark theme")}
        aria-label={t("topbar.toggleTheme", "Toggle theme")}
        data-testid="topbar-theme"
      >
        <Icon name={theme === "dark" ? "sun" : "moon"} size={14} />
      </button>

      {/* Divider — verbatim mockup inline-style literal */}
      <span style={DIVIDER_STYLE} aria-hidden="true" />

      {/* Bell — mockup wraps in a ref span; production keeps button semantics for a11y */}
      <span style={NOTIFS_ANCHOR_STYLE}>
        <button
          type="button"
          className="btn ghost"
          data-size="sm"
          aria-label={t("topbar.notifications.title", "Notifications")}
          onClick={onToggleNotifs}
          data-testid="notifications-bell"
        >
          <Icon name="bell" size={14} />
          {unreadCount > 0 && (
            <span style={NOTIFS_BADGE_STYLE}>
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>
      </span>

      {/* UserMenu avatar — mockup uses .avatar div; production wraps UserMenu for full Radix menu */}
      {userMenu ?? <UserMenu />}
    </header>
  );
};
