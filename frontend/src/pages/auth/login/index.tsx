/**
 * File: frontend/src/pages/auth/login/index.tsx
 * Purpose: Login entry — mockup-direct rewrite per Sprint 57.23 US-B2 (3 SSO outline placeholders + email + Continue).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.7 → US-B9 (AuthShell + Tailwind) → Sprint 57.23 US-B2 (mockup-direct rewrite)
 *
 * Description:
 *   Sprint 57.23 US-B2 rewrite per `reference/design-mockups/page-extras.jsx:27-57`:
 *     - Card with "Sign in" 18px + subtitle 12.5px
 *     - 3 SSO outline buttons (SAML / Microsoft / Google) disabled with tooltip
 *       "Enterprise SSO via WorkOS roadmap" — wired by AD-WorkOS-Multi-IdP-Phase58
 *     - "or" divider with muted lines
 *     - Work email input (13.5px) — currently visual-only (Continue still kicks WorkOS OIDC redirect)
 *     - Continue PRIMARY button → preserves existing `handleLogin` (window.location WorkOS redirect)
 *     - MFA hint footer (SAML 2.0 / OIDC · MFA required by tenant policy)
 *     - dev-login link → /auth/dev (extracted Sprint 57.23 US-B3 from prior DevLoginSection)
 *
 *   AuthShell footer slot: "By signing in you agree to the Terms · Privacy"
 *
 *   Preserved:
 *     - `handleLogin` window.location WorkOS redirect (with redirect_to)
 *     - `setPostLoginRedirect` flow
 *     - `?error=` param surface via ErrorAlert (same UX shape)
 *
 *   Removed Sprint 57.23:
 *     - `<h1>IPA Platform V2 — Sign In</h1>` (mockup intentional no-heading)
 *     - Embedded DevLoginSection (extracted to /auth/dev per US-B3)
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-18
 *
 * Modification History:
 *   - 2026-05-18: Sprint 57.23 Day 4 — gate dev-link with import.meta.env.DEV (R8 hardening; route was already gated in App.tsx)
 *   - 2026-05-18: Sprint 57.23 US-B2 — mockup-direct rewrite (3 SSO disabled + email + Continue; extract DevLoginSection)
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <Card> + <Button>; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A4 — add DEV-only <DevLoginSection>
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:login (WorkOS OIDC redirect endpoint)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/pages/auth/dev/index.tsx (Sprint 57.23 US-B3 extracted DevLoginSection)
 *   - frontend/src/features/auth/services/authService.ts (setPostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.login.* / auth.dev.* namespaces)
 *   - reference/design-mockups/page-extras.jsx:27-57 (AuthLogin canonical visual source)
 */

import { AlertTriangle, ArrowRight, Globe, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, CardContent } from "@/components/ui";
import { setPostLoginRedirect } from "@/features/auth/services/authService";

function ErrorAlert({ message }: { message: string }) {
  const { t } = useTranslation("auth");
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
      <span>
        <strong>{t("errorTitle")}:</strong> {message}
      </span>
    </div>
  );
}

export default function LoginPage() {
  const { t } = useTranslation("auth");
  const [params] = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const error = params.get("error");
    if (error) setErrorMessage(decodeURIComponent(error));
  }, [params]);

  const handleLogin = () => {
    const redirectTo = params.get("redirect_to") || "/overview";
    setPostLoginRedirect(redirectTo);
    window.location.href = `/api/v1/auth/login?redirect_to=${encodeURIComponent(redirectTo)}`;
  };

  // Sprint 57.23 US-B2: AD-WorkOS-Multi-IdP-Phase58 placeholders (3 SSO buttons disabled with tooltip)
  const ssoButtons = [
    { id: "saml", icon: ShieldCheck, label: t("login.sso.saml") },
    { id: "microsoft", icon: Globe, label: t("login.sso.microsoft") },
    { id: "google", icon: Globe, label: t("login.sso.google") },
  ];

  return (
    <AuthShell footer={t("login.footer")}>
      <Card>
        <CardContent className="flex flex-col gap-4 p-6">
          <div>
            <div className="mb-1 text-lg font-semibold">{t("login.title")}</div>
            <div className="text-[12.5px] text-fg-muted">{t("login.subtitle")}</div>
          </div>

          {errorMessage ? <ErrorAlert message={errorMessage} /> : null}

          {ssoButtons.map((sso) => (
            <Button
              key={sso.id}
              variant="outline"
              size="lg"
              disabled
              aria-disabled="true"
              title={t("login.sso.comingSoonTooltip")}
              className="justify-start text-[13.5px]"
            >
              <sso.icon size={16} className="mr-1" />
              {sso.label}
            </Button>
          ))}

          <div className="my-1 flex flex-row items-center gap-2">
            <div className="h-px flex-1 bg-border" aria-hidden />
            <span className="text-[11px] text-fg-subtle">{t("login.orDivider")}</span>
            <div className="h-px flex-1 bg-border" aria-hidden />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="login-email" className="text-[12px] font-medium text-fg-muted">
              {t("login.workEmail")}
            </label>
            <input
              id="login-email"
              type="email"
              placeholder={t("login.workEmailPlaceholder")}
              className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <Button type="button" onClick={handleLogin} size="lg" className="w-full text-[13.5px]">
            {t("login.continue")}
            <ArrowRight size={16} className="ml-1" />
          </Button>

          <div className="flex flex-row items-center justify-center gap-1.5 text-[11px] text-fg-subtle">
            <ShieldCheck size={11} aria-hidden />
            <span>{t("login.mfaHint")}</span>
          </div>
        </CardContent>
      </Card>

      {/* Sprint 57.23 Day 4 R8 hardening: gate dev-link with DEV flag (route was already gated in App.tsx; this hides the link too in prod build) */}
      {import.meta.env.DEV && (
        <Link to="/auth/dev" className="text-center text-[11px] text-fg-subtle hover:text-foreground">
          {t("login.devLink")}
        </Link>
      )}
    </AuthShell>
  );
}
