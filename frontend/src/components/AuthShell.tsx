/**
 * File: frontend/src/components/AuthShell.tsx
 * Purpose: Auth-only routes layout shell — full-screen centered card per mockup AuthShell (no sidebar/no sticky header).
 * Category: Frontend / components / layout (auth-only)
 * Scope: Phase 57 / Sprint 57.7 US-B2 (initial as AppShell) → Sprint 57.8 US-4 (renamed AuthShell per Day 0 Decision B1) → Sprint 57.23 US-B1 (mockup full-screen centered rewrite)
 *
 * Description:
 *   Container layout for unauthenticated routes (/auth/login, /auth/callback,
 *   /auth/register, /auth/invite/:token, /auth/mfa, /auth/expired, /auth/dev).
 *
 *   Sprint 57.23 US-B1 rewrite per `reference/design-mockups/page-extras.jsx:5-25`:
 *     - Full-screen flex centered (no container max-width / no sidebar / no sticky header)
 *     - Radial gradient backdrop using --primary token (one inline-style escape hatch
 *       per STYLE.md §3 — Tailwind utilities can't express multi-stop HSL gradient)
 *     - 420px-wide column with brand mark + IPA Platform title + V2 · loop-first metadata
 *     - Optional footer slot (mockup pattern — replaces prior headerActions prop)
 *
 *   `data-testid="auth-shell"` anchor preserved for Playwright e2e selector stability
 *   across the AuthShell rewrite cascade (Sprint 57.23 R7 mitigation).
 *
 *   Differs from AppShellV2 in 2 critical ways:
 *     1. NO sidebar (user not authed yet — no nav target available)
 *     2. NO UserMenu (no JWT to consume)
 *
 * Created: 2026-05-10 (Sprint 57.7 Day 3 Tier 3 — initial as AppShell)
 * Last Modified: 2026-05-18
 *
 * Modification History:
 *   - 2026-05-18: Sprint 57.23 US-B1 — rewrite to mockup full-screen centered (closes AD-AuthShell-Mockup-Refactor)
 *   - 2026-05-10: Sprint 57.8 US-4 Day 2 — rename AppShell → AuthShell per Day 0 Decision B1; remove 3 hardcoded nav links
 *   - 2026-05-10: Initial creation (Sprint 57.7 US-B2)
 */

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
      className="flex min-h-screen items-center justify-center p-10"
      // eslint-disable-next-line no-restricted-syntax -- STYLE.md §3 escape hatch: Tailwind can't express multi-stop HSL gradient with --primary token (Sprint 57.23 US-B1 mockup AuthShell L7-12)
      style={{
        background:
          "radial-gradient(ellipse 800px 600px at 50% -10%, hsl(var(--primary) / 0.12) 0%, transparent 60%), hsl(var(--background))",
      }}
    >
      <div className="flex w-[420px] flex-col gap-[18px]">
        <div className="mb-1 flex flex-row items-center justify-center gap-2.5">
          <div className="h-8 w-8 rounded-md bg-primary" aria-hidden />
          <div>
            <div className="text-base font-semibold">IPA Platform</div>
            <div className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-fg-subtle">
              V2 · loop-first
            </div>
          </div>
        </div>
        {children}
        {footer && <div className="mt-1 text-center text-[11px] text-fg-subtle">{footer}</div>}
      </div>
    </div>
  );
};
