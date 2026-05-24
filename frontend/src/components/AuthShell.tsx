/**
 * File: frontend/src/components/AuthShell.tsx
 * Purpose: Auth-only routes layout shell — verbatim re-point per mockup AuthShell.
 * Category: Frontend / components / layout (auth-only)
 * Scope: Phase 57 / Sprint 57.7 US-B2 (initial as AppShell) → Sprint 57.8 US-4 (renamed AuthShell) → Sprint 57.23 US-B1 (mockup full-screen centered rewrite) → Sprint 57.35 US-B1 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Container layout for unauthenticated routes (/auth/login, /auth/callback,
 *   /auth/register, /auth/invite/:token, /auth/mfa, /auth/expired, /auth/dev).
 *
 *   Sprint 57.35 US-B1 verbatim re-point per `reference/design-mockups/page-extras.jsx:5-25`:
 *     - Drop Tailwind translations (Sprint 57.23 HSL-translated `flex min-h-screen items-center
 *       justify-center p-10` + `w-[420px] flex-col gap-[18px]` etc.) in favour of inline-style
 *       literals copied byte-for-byte from mockup.
 *     - Mockup uses `.row` + `.brand-mark` verbatim CSS classes from styles-mockup.css.
 *     - Outer container background: `radial-gradient ... oklch(from var(--primary) l c h / 0.12)`
 *       (oklch end-to-end per Sprint 57.28+ verbatim-CSS rule; the Sprint 57.26 token-baseline
 *       alignment that swapped --background→--bg is preserved).
 *     - 400px column width verbatim (was 420px in Sprint 57.23 HSL translation — mockup truth = 400).
 *
 *   `data-testid="auth-shell"` anchor preserved for Playwright e2e selector stability.
 *
 *   Differs from AppShellV2 in 2 critical ways:
 *     1. NO sidebar (user not authed yet — no nav target available)
 *     2. NO UserMenu (no JWT to consume)
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3 — initial as AppShell)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 US-B1 — verbatim re-point per page-extras.jsx:5-25 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-21: Sprint 57.26 — backdrop base --background→--bg (foundation-fidelity token alignment)
 *   - 2026-05-18: Sprint 57.23 US-B1 — rewrite to mockup full-screen centered (closes AD-AuthShell-Mockup-Refactor)
 *   - 2026-05-10: Sprint 57.8 US-4 Day 2 — rename AppShell → AuthShell per Day 0 Decision B1; remove 3 hardcoded nav links
 *   - 2026-05-10: Initial creation (Sprint 57.7 US-B2)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals copied byte-for-byte from mockup page-extras.jsx:5-25 (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md §verbatim-CSS rule) */

import type { FC, ReactNode } from "react";

interface AuthShellProps {
  children: ReactNode;
  /** Mockup pattern: optional footer slot below content column (replaces prior headerActions prop) */
  footer?: ReactNode;
}

export const AuthShell: FC<AuthShellProps> = ({ children, footer }) => {
  return (
    <div
      data-testid="auth-shell"
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 40,
        background:
          "radial-gradient(ellipse 800px 600px at 50% -10%, oklch(from var(--primary) l c h / 0.12) 0%, transparent 60%), var(--bg)",
      }}
    >
      <div style={{ width: 400, display: "flex", flexDirection: "column", gap: 18 }}>
        <div className="row" style={{ gap: 10, marginBottom: 4, justifyContent: "center" }}>
          <div className="brand-mark" style={{ width: 32, height: 32 }} />
          <div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>IPA Platform</div>
            <div
              style={{
                fontSize: 10.5,
                color: "var(--fg-subtle)",
                fontFamily: "var(--font-mono)",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              V2 · loop-first
            </div>
          </div>
        </div>
        {children}
        {footer && (
          <div
            style={{
              fontSize: 11,
              color: "var(--fg-subtle)",
              textAlign: "center",
              marginTop: 4,
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
