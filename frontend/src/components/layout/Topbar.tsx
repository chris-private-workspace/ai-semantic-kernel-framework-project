/**
 * File: frontend/src/components/layout/Topbar.tsx
 * Purpose: Top horizontal bar — breadcrumb + tenant pill + ⌘K search + locale + theme + bell + UserMenu avatar.
 * Category: Frontend / components / layout
 * Scope: Phase 57 / Sprint 57.20 US-B1 Day 1 (NEW; mockup shell.jsx 1:1 port)
 *
 * Description:
 *   Replaces the inline `<header>` previously embedded in AppShellV2.tsx with
 *   a dedicated component that ports the mockup `shell.jsx` Topbar 1:1.
 *
 *   Composition (left → right):
 *     1. Breadcrumb: route title + route path pill (resolved from useLocation())
 *     2. Tenant pill: "acme-prod · <role>" (fixture name; real tenant API wires
 *        in AD-UserMenu-Tenant-Switch Sprint 57.21+)
 *     3. Spacer (flex-1)
 *     4. ⌘K cmdk button (clickable + Enter-keyed → triggers CommandPalette open)
 *     5. Locale toggle (EN ↔ 中) — direct toggle, not dropdown (UserMenu retains
 *        full locale list for accessibility)
 *     6. Theme toggle (sun/moon — directly mutates ThemeProvider state)
 *     7. Divider
 *     8. Bell — triggers NotificationsPanel; unread dot if count > 0
 *     9. UserMenu (Sprint 57.19 extended; Radix DropdownMenu)
 *
 *   pageTitle prop: when provided by AppShellV2 caller, takes precedence over
 *   route-derived breadcrumb title. headerActions prop: rendered between
 *   spacer and ⌘K for backward compat with 14 existing pages.
 *
 * Created: 2026-05-17 (Sprint 57.20 Day 1 US-B1)
 * Last Modified: 2026-05-17
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.20 Day 1) — mockup shell.jsx port
 *
 * Related:
 *   - reference/design-mockups/shell.jsx §Topbar (canonical visual source)
 *   - frontend/src/components/AppShellV2.tsx (host)
 *   - frontend/src/components/UserMenu.tsx (avatar dropdown — Sprint 57.19)
 *   - frontend/src/components/topbar/CommandPalette.tsx (⌘K — Sprint 57.19 US-D1)
 *   - frontend/src/components/topbar/NotificationsPanel.tsx (bell — Sprint 57.19 US-D2)
 *   - frontend/src/components/ThemeProvider.tsx (theme state)
 *   - frontend/src/routes.config.ts (ROUTES single-source for breadcrumb)
 */

import { Bell, Globe, Moon, Search, Sun } from "lucide-react";
import { type FC, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";

import { useTheme } from "@/components/ThemeProvider";
import { UserMenu } from "@/components/UserMenu";
import { useAuthStore } from "@/features/auth/store/authStore";
import { LOCALE_STORAGE_KEY } from "@/i18n";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/routes.config";

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
    <header
      className="flex h-12 items-center gap-3 border-b border-border bg-bg-1 px-4"
      data-testid="topbar"
    >
      {/* Breadcrumb — h1 preserves pre-Sprint-57.20 page-title-is-h1 contract for a11y */}
      <div className="flex items-center gap-2 min-w-0">
        <h1 className="truncate text-sm font-medium text-foreground m-0">{title}</h1>
        {pathPill && (
          <span className="rounded-sm border border-border bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
            {pathPill}
          </span>
        )}
      </div>

      {/* Tenant pill */}
      <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-bg-2 px-2.5 py-1 text-xs text-fg-muted">
        <span className="h-1.5 w-1.5 rounded-full bg-success" aria-hidden="true" />
        <span>
          {tenantName} · {roleLabel}
        </span>
      </span>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Optional header actions slot (backward compat) */}
      {headerActions && <div className="flex items-center gap-2">{headerActions}</div>}

      {/* ⌘K cmdk pill */}
      <button
        type="button"
        onClick={onOpenPalette}
        className={cn(
          "inline-flex h-7 items-center gap-2 rounded-md border border-border bg-bg-2 px-2.5",
          "text-xs text-fg-muted hover:bg-bg-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
        title={t("topbar.openPalette", "Open command palette")}
        data-testid="topbar-cmdk"
      >
        <Search size={12} />
        <span>{t("shell.search", "Search…")}</span>
        <span className="ml-2 rounded border border-border bg-bg-1 px-1 py-0.5 font-mono text-[9px]">
          ⌘K
        </span>
      </button>

      {/* Locale toggle */}
      <button
        type="button"
        onClick={toggleLocale}
        className={cn(
          "inline-flex h-7 min-w-7 items-center justify-center gap-1 rounded-md border border-border bg-transparent px-2",
          "font-mono text-[11px] font-medium uppercase text-fg-muted hover:bg-bg-2",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
        title={currentLng === "en" ? "切換到繁體中文" : "Switch to English"}
        aria-label={t("topbar.toggleLocale", "Toggle locale")}
        data-testid="topbar-locale"
      >
        <Globe size={12} />
        <span>{localeShort}</span>
      </button>

      {/* Theme toggle */}
      <button
        type="button"
        onClick={toggleTheme}
        className={cn(
          "inline-flex h-7 w-7 items-center justify-center rounded-md text-fg-muted hover:bg-bg-2",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
        title={theme === "dark"
          ? t("topbar.themeLight", "Switch to light theme")
          : t("topbar.themeDark", "Switch to dark theme")}
        aria-label={t("topbar.toggleTheme", "Toggle theme")}
        data-testid="topbar-theme"
      >
        {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
      </button>

      {/* Divider */}
      <span className="h-4 w-px bg-border" aria-hidden="true" />

      {/* Bell */}
      <button
        type="button"
        onClick={onToggleNotifs}
        aria-label={t("topbar.notifications.title", "Notifications")}
        data-testid="notifications-bell"
        className={cn(
          "relative inline-flex h-7 w-7 items-center justify-center rounded-md text-fg-muted hover:bg-bg-2",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
      >
        <Bell size={14} />
        {unreadCount > 0 && (
          <span
            className={cn(
              "absolute -right-0.5 -top-0.5 inline-flex h-3.5 min-w-3.5 items-center justify-center",
              "rounded-full bg-warning px-1 font-mono text-[9px] font-bold text-bg",
            )}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* UserMenu avatar (Sprint 57.19 extended); override slot for backward compat */}
      {userMenu ?? <UserMenu />}
    </header>
  );
};
