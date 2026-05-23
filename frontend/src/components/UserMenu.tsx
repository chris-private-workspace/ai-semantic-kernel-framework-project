/**
 * File: frontend/src/components/UserMenu.tsx
 * Purpose: Header avatar dropdown — current user (authStore) + role badges + locale switcher + sign out.
 * Category: Frontend / components / auth-aware
 * Scope: Phase 57 / Sprint 57.8 US-2 → Sprint 57.13 US-A1 (authStore) → US-B3 (Radix DropdownMenu) → US-B5 (i18n) → Sprint 57.29 US-B5 (verbatim re-point) → Sprint 57.30 US-B1+B2 (Radix-drop)
 *
 * Description:
 *   Avatar circle in AppShellV2's header right slot. Click → menu showing the
 *   signed-in user (display name / email) + role badges + a language switcher
 *   (one item per SUPPORTED_LOCALES; the active one is marked) + Sign out (calls
 *   logout() — backend /auth/logout + clear authStore + redirect to vendor signout).
 *   Renders null unless authStore.status === "authenticated".
 *
 *   Sprint 57.30 US-B1+B2: dropped Radix <DropdownMenu> entirely; verbatim port of
 *   the mockup topbar-overlays.jsx UserMenu (useDismiss hook + position-absolute
 *   panel pinned to top:50 right:12 + 26×26 .avatar trigger class). The two
 *   avatar visuals are now sourced separately: the trigger uses className="avatar"
 *   (CSS class → 26×26 per styles-mockup.css L387-394), while the in-panel
 *   identity card keeps the 36×36 inline-style avatar. This closes
 *   AD-UserMenu-Mockup-Structural-Deltas carryover from Sprint 57.29.
 *
 *   Trade-off: loses Radix free aria-activedescendant arrow-key nav + focus-trap;
 *   mockup ships without those (ESC + click-outside via useDismiss are sufficient).
 *   useDismiss is kept inline (not extracted to a hook file) per Karpathy §2
 *   simplicity-first; extract when a 2nd consumer arrives (Sprint 57.31+).
 *
 * Created: 2026-05-10 (Sprint 57.8 Day 2)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-05-23: Sprint 57.30 US-B1+B2 — drop Radix DropdownMenu, port useDismiss verbatim (closes AD-UserMenu-Mockup-Structural-Deltas)
 *   - 2026-05-22: Sprint 57.29 US-B5 — verbatim re-point to mockup topbar-overlays.jsx UserMenu markup
 *   - 2026-05-17: Sprint 57.19 US-D3 — mockup port (tenant switch fixtures + nav items + role/region + theme toggle)
 *   - 2026-05-10: Sprint 57.13 US-B5 — locale switcher items + i18n the labels
 *   - 2026-05-10: Sprint 57.13 US-B3 — swap custom popover → <DropdownMenu>; add role badges
 *   - 2026-05-10: Sprint 57.13 US-A1 — read authStore.user instead of decoding the JWT; sign out via logout()
 *   - 2026-05-10: Initial creation (Sprint 57.8 US-2)
 *
 * Related:
 *   - reference/design-mockups/topbar-overlays.jsx (canonical visual source — useDismiss L9-26 + UserMenu L331-441)
 *   - reference/design-mockups/styles.css L387-394 (.avatar 26×26)
 *   - frontend/src/styles-mockup.css (Sprint 57.28 byte-identical foundation; .avatar class)
 *   - frontend/src/features/auth/store/authStore.ts (user + status + roles)
 *   - frontend/src/features/auth/services/authService.ts (logout)
 *   - frontend/src/i18n/index.ts (SUPPORTED_LOCALES + LOCALE_STORAGE_KEY)
 *   - frontend/src/components/AppShellV2.tsx (host via userMenu prop slot)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup topbar-overlays.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import { useEffect, useRef, useState, type CSSProperties, type FC, type KeyboardEvent as ReactKeyboardEvent, type RefObject } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { useTheme } from "@/components/ThemeProvider";
import { Icon } from "@/components/mockup-ui";
import { logout } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";
import { LOCALE_STORAGE_KEY, SUPPORTED_LOCALES } from "@/i18n";

// ───────────────── useDismiss — verbatim port of mockup topbar-overlays.jsx L9-26 ─────────────────
// Inline (NOT extracted to a hook file) per Karpathy §2 simplicity-first; extract when a 2nd
// consumer arrives in Sprint 57.31+. Semantics:
//   - on Escape key → onClose()
//   - on document mousedown → if click is inside the anchor (the trigger), return (let trigger toggle)
//   - on document mousedown → if click target is inside any [data-topbar-overlay], return (let panel handle)
//   - otherwise → onClose()
function useDismiss(
  open: boolean,
  onClose: () => void,
  anchorRef: RefObject<HTMLElement | null>,
): void {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    const onClick = (e: MouseEvent): void => {
      const target = e.target as Element | null;
      if (target === null) return;
      if (anchorRef.current && anchorRef.current.contains(target)) return;
      if (target.closest("[data-topbar-overlay]")) return;
      onClose();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open, onClose, anchorRef]);
}

// ───────────────── inline style objects (verbatim from mockup topbar-overlays.jsx) ─────────────────

const panelStyle: CSSProperties = {
  position: "absolute", top: 50, right: 12, width: 260,
  background: "var(--bg-1)", border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius)", boxShadow: "0 12px 32px oklch(0 0 0 / 0.5)",
  zIndex: 999, padding: 4,
};

const identityCardStyle: CSSProperties = {
  gap: 10, padding: "10px 12px", borderRadius: 5,
  background: "var(--bg-2)", marginBottom: 4,
};

// In-panel identity-card avatar — 36×36 inline-style per mockup topbar-overlays.jsx L351-356.
// (The TRIGGER avatar uses className="avatar" CSS class → 26×26 per styles-mockup.css L387-394.)
const identityAvatarStyle: CSSProperties = {
  width: 36, height: 36, borderRadius: "50%",
  background: "linear-gradient(135deg, oklch(0.7 0.14 30), oklch(0.6 0.16 350))",
  color: "white", fontSize: 13, fontWeight: 600,
  display: "flex", alignItems: "center", justifyContent: "center",
};

const identityNameStyle: CSSProperties = { gap: 2, minWidth: 0 };

const sectionLabelStyle: CSSProperties = {
  padding: "6px 12px 4px", fontSize: 10, color: "var(--fg-subtle)",
  textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: "var(--font-mono)",
};

const roleSectionStyle: CSSProperties = {
  padding: "6px 12px", gap: 6, justifyContent: "space-between", fontSize: 11,
};

const logoutRowStyle: CSSProperties = {
  gap: 10, padding: "8px 10px", borderRadius: 5, cursor: "pointer",
  color: "var(--danger)", fontSize: 12.5,
};

const logoutShortcutStyle: CSSProperties = {
  fontSize: 10, color: "var(--fg-subtle)",
};

const itemRowStyle: CSSProperties = {
  gap: 10, padding: "7px 10px", borderRadius: 5, cursor: "pointer", fontSize: 12.5,
};

// Mockup fixture tenant list — replace with real API in Sprint 57.20+ (Cat 12 tenant feed).
const TENANT_FIXTURES = [
  { id: "t1", name: "acme-prod", region: "ap-east-1", active: true },
  { id: "t2", name: "globex-eu", region: "eu-west-1", active: false },
  { id: "t3", name: "initech-jp", region: "ap-northeast-1", active: false },
];

// Nav items (verbatim from mockup topbar-overlays.jsx lines 394-398)
const NAV_ITEMS = [
  { icon: "user" as const,     labelKey: "userMenu.profile",     route: "/profile" },
  { icon: "keys" as const,     labelKey: "userMenu.mfa",         route: "/mfa" },
  { icon: "settings" as const, labelKey: "userMenu.preferences", route: "/admin/tenants" },
  { icon: "help" as const,     labelKey: "userMenu.help",        route: "/devui", external: true },
];

export const UserMenu: FC = () => {
  const { t, i18n } = useTranslation("common");
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const roles = useAuthStore((s) => s.roles);

  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLButtonElement>(null);
  useDismiss(open, () => setOpen(false), anchorRef);

  if (status !== "authenticated" || user === null) return null;

  const label = user.display_name?.trim() || user.email;
  const initial = label ? label.charAt(0).toUpperCase() : "?";

  const currentLng = i18n.resolvedLanguage ?? i18n.language;
  const changeLocale = (id: string): void => {
    try {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, id);
    } catch {
      /* localStorage unavailable (private mode) — changeLanguage still works for the session */
    }
    void i18n.changeLanguage(id);
  };

  // Active tenant region for the region info row
  const activeTenant = TENANT_FIXTURES.find((tn) => tn.active);

  // Close-and-do helper — every item closes the panel after firing its action.
  const closeAnd = (fn: () => void) => (): void => {
    fn();
    setOpen(false);
  };

  // Keyboard handler for menuitem <div>s — Enter/Space fires the row's click handler.
  // (Mockup uses raw <div> for menu rows; production adds this to satisfy jsx-a11y/click-events-have-key-events.)
  const onMenuItemKey = (e: ReactKeyboardEvent<HTMLDivElement>): void => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      (e.currentTarget as HTMLElement).click();
    }
  };

  return (
    <>
      {/* Avatar trigger — uses mockup .avatar CSS class (26×26 per styles-mockup.css L387-394) */}
      <button
        ref={anchorRef}
        type="button"
        className="avatar"
        aria-label={t("userMenu.label")}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {initial}
      </button>

      {/* Panel — verbatim mockup top:50 right:12; useDismiss handles ESC + click-outside */}
      {open && (
        <div
          data-topbar-overlay
          role="menu"
          aria-label={t("userMenu.options")}
          style={panelStyle}
        >
          {/* identity card (mockup lines 347-361) + "Signed in as" label (production contract) */}
          <div className="row" style={identityCardStyle}>
            <div style={identityAvatarStyle}>{initial}</div>
            <div className="col grow" style={identityNameStyle}>
              <div className="mono subtle" style={{ fontSize: 10 }}>{t("userMenu.signedInAs")}</div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{label}</div>
              <div className="mono subtle" style={{ fontSize: 10.5 }}>{user.email}</div>
              {roles.length > 0 && (
                <div className="row" style={{ gap: 4, flexWrap: "wrap", marginTop: 3 }}>
                  {roles.map((r) => (
                    <span key={r} className="badge primary" style={{ fontSize: 10 }}>{r}</span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* tenant switch section label (mockup line 364) */}
          <div style={sectionLabelStyle}>{t("userMenu.switchTenant")}</div>

          {/* tenant list (mockup lines 367-389) */}
          {TENANT_FIXTURES.map((tn) => (
            <div
              key={tn.id}
              role="menuitem"
              tabIndex={-1}
              className="row"
              aria-current={tn.active ? "true" : undefined}
              style={{
                gap: 8, padding: "7px 10px", borderRadius: 5, cursor: "pointer",
                background: tn.active ? "oklch(from var(--primary) l c h / 0.10)" : "transparent",
              }}
              onClick={closeAnd(() => { /* tenant switch wired Sprint 57.20+ */ })}
              onKeyDown={onMenuItemKey}
            >
              <div style={{
                width: 22, height: 22, borderRadius: 4,
                background: tn.active ? "var(--primary)" : "var(--bg-3)",
                color: tn.active ? "white" : "var(--fg-muted)",
                fontSize: 10, fontWeight: 600,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>{tn.name[0].toUpperCase()}</div>
              <div className="col grow" style={{ gap: 1 }}>
                <span style={{ fontSize: 12 }}>{tn.name}</span>
                <span className="mono subtle" style={{ fontSize: 10 }}>{tn.region}</span>
              </div>
              {tn.active && <Icon name="check" size={11} style={{ color: "var(--primary)" }} />}
            </div>
          ))}

          <div className="hr" style={{ margin: "4px 0" }} />

          {/* nav items (mockup lines 394-411) */}
          {NAV_ITEMS.map((it) => (
            <div
              key={it.labelKey}
              role="menuitem"
              tabIndex={-1}
              className="row"
              style={itemRowStyle}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
              onClick={closeAnd(() => navigate(it.route))}
              onKeyDown={onMenuItemKey}
            >
              <Icon name={it.icon} size={13} className="subtle" />
              <span style={{ flex: 1 }}>{t(it.labelKey)}</span>
              {it.external && <Icon name="arrow_right" size={10} className="subtle" />}
            </div>
          ))}

          {/* theme toggle */}
          <div
            role="menuitem"
            tabIndex={-1}
            className="row"
            style={itemRowStyle}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
            onClick={closeAnd(toggleTheme)}
            onKeyDown={onMenuItemKey}
          >
            <Icon name={theme === "dark" ? "sun" : "moon"} size={13} className="subtle" />
            <span style={{ flex: 1 }}>{t(theme === "dark" ? "userMenu.themeLight" : "userMenu.themeDark")}</span>
          </div>

          <div className="hr" style={{ margin: "4px 0" }} />

          {/* region row (mockup line 420-423) */}
          <div className="row" style={roleSectionStyle}>
            <span className="muted">{t("userMenu.region")}</span>
            <span className="mono subtle">{activeTenant?.region ?? "—"}</span>
          </div>

          {/* language section */}
          <div className="hr" style={{ margin: "4px 0" }} />
          <div style={sectionLabelStyle}>{t("userMenu.language")}</div>
          {SUPPORTED_LOCALES.map((loc) => {
            const isCurrent = currentLng === loc.id;
            return (
              <div
                key={loc.id}
                role="menuitem"
                tabIndex={-1}
                className="row"
                aria-current={isCurrent ? "true" : undefined}
                style={itemRowStyle}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                onClick={closeAnd(() => changeLocale(loc.id))}
                onKeyDown={onMenuItemKey}
              >
                {isCurrent
                  ? <Icon name="check" size={13} style={{ color: "var(--primary)" }} />
                  : <span style={{ width: 13, display: "inline-block" }} />}
                <span style={{ flex: 1 }}>{loc.label}</span>
              </div>
            );
          })}

          <div className="hr" style={{ margin: "4px 0" }} />

          {/* logout (mockup lines 428-438) */}
          <div
            role="menuitem"
            tabIndex={-1}
            className="row"
            style={logoutRowStyle}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "oklch(from var(--danger) l c h / 0.08)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
            onClick={closeAnd(() => void logout())}
            onKeyDown={onMenuItemKey}
          >
            <Icon name="x" size={13} />
            <span style={{ flex: 1 }}>{t("userMenu.signOut")}</span>
            <span className="mono subtle" style={logoutShortcutStyle}>⇧⌘Q</span>
          </div>
        </div>
      )}
    </>
  );
};
