/**
 * File: frontend/src/pages/auth/login/index.tsx
 * Purpose: Login entry — verbatim re-point per mockup AuthLogin (Sprint 57.35 US-B2).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.7 → US-B9 (AuthShell + Tailwind) → Sprint 57.23 US-B2 (mockup-direct rewrite — HSL-translated) → Sprint 57.35 US-B2 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Sprint 57.35 US-B2 verbatim re-point per `reference/design-mockups/page-extras.jsx:27-57`:
 *     - Drop Tailwind utility translations (the Sprint 57.23 vintage `flex flex-col gap-4 p-6`
 *       + `justify-start text-[13.5px]` + Tailwind divider et al.) in favour of mockup
 *       verbatim CSS classes from `styles-mockup.css`.
 *     - Use `mockup-ui` Button (emits `btn outline` / `btn primary`) + Card (emits `card`/`card-body`)
 *       + Field (emits `.field`/`.field-label`) + Icon (mockup `shield`/`globe`/`git` SVG set).
 *     - `.input` for Work email; `.row` + `subtle` + `mono` for hints; verbatim `or` divider per L38-42.
 *     - 3 SSO buttons remain disabled (visual only — AD-WorkOS-Multi-IdP-Phase58 wiring).
 *     - dev-login orange link: `<span className="mono" style={{ color: "var(--warning)" }}>`
 *       (Hybrid Tailwind+inline color bridge per Sprint 57.31 precedent; required because
 *       `var(--warning)` is dynamic-theme and styles-mockup.css has no `.dev-login` class).
 *     - "Continue" Button uses mockup-ui `iconRight="arrow_right"` (no lucide-react ArrowRight).
 *
 *   AuthShell footer slot: "By signing in you agree to the Terms · Privacy".
 *
 *   Preserved:
 *     - `handleLogin` window.location WorkOS redirect (with redirect_to)
 *     - `setPostLoginRedirect` flow
 *     - `?error=` param surface via ErrorAlert (same UX shape; visual swap only)
 *     - i18n keys + DEV gate for dev-link
 *
 *   Removed Sprint 57.35:
 *     - shadcn `Button` / `Card` / `CardContent` (replaced by mockup-ui)
 *     - lucide-react icon imports (replaced by mockup-ui Icon SVG set)
 *     - Tailwind utility translations of mockup `.btn outline`/`.btn primary`/`.input`/etc.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 US-B2 — verbatim re-point per page-extras.jsx:27-57 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-18: Sprint 57.23 Day 4 — gate dev-link with import.meta.env.DEV (R8 hardening)
 *   - 2026-05-18: Sprint 57.23 US-B2 — mockup-direct rewrite (3 SSO disabled + email + Continue; extract DevLoginSection)
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <Card> + <Button>; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A4 — add DEV-only <DevLoginSection>
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:login (WorkOS OIDC redirect endpoint)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.35 verbatim re-point)
 *   - frontend/src/components/mockup-ui.tsx (Button/Card/Field/Icon primitives)
 *   - frontend/src/pages/auth/dev/index.tsx (Sprint 57.23 US-B3 extracted DevLoginSection)
 *   - frontend/src/features/auth/services/authService.ts (setPostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.login.* / auth.dev.* namespaces)
 *   - reference/design-mockups/page-extras.jsx:27-57 (AuthLogin canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals + var(--warning) color bridge copied byte-for-byte from mockup page-extras.jsx:27-57 (STYLE.md §1 escape hatch + Sprint 57.31 Hybrid Tailwind+inline color bridge precedent) */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, Field, Icon } from "@/components/mockup-ui";
import { setPostLoginRedirect } from "@/features/auth/services/authService";

function ErrorAlert({ message }: { message: string }) {
  const { t } = useTranslation("auth");
  return (
    <div
      role="alert"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 8,
        padding: 10,
        borderRadius: 6,
        border: "1px solid oklch(from var(--danger) l c h / 0.4)",
        background: "oklch(from var(--danger) l c h / 0.1)",
        color: "var(--danger)",
        fontSize: 12.5,
      }}
    >
      <Icon name="warn" size={14} style={{ marginTop: 1, flexShrink: 0 }} />
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

  // Sprint 57.35 US-B2: AD-WorkOS-Multi-IdP-Phase58 placeholders — 3 SSO buttons disabled
  // (visual verbatim per mockup L35-37; mockup-ui Icon names = mockup `shield`/`globe`/`git` set)
  const ssoButtons: Array<{ id: string; icon: "shield" | "globe" | "git"; label: string }> = [
    { id: "saml", icon: "shield", label: t("login.sso.saml") },
    { id: "microsoft", icon: "globe", label: t("login.sso.microsoft") },
    { id: "google", icon: "git", label: t("login.sso.google") },
  ];

  return (
    <AuthShell
      footer={
        <span>
          {t("login.footer")}
        </span>
      }
    >
      <Card>
        <div className="col" style={{ gap: 16 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              {t("login.title")}
            </div>
            <div className="muted" style={{ fontSize: 12.5 }}>
              {t("login.subtitle")}
            </div>
          </div>

          {errorMessage ? <ErrorAlert message={errorMessage} /> : null}

          {ssoButtons.map((sso) => (
            <Button
              key={sso.id}
              variant="outline"
              data-size="lg"
              icon={sso.icon}
              disabled
              aria-disabled="true"
              title={t("login.sso.comingSoonTooltip")}
            >
              {sso.label}
            </Button>
          ))}

          <div className="row" style={{ gap: 8, margin: "4px 0" }}>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
            <span className="subtle" style={{ fontSize: 11 }}>
              {t("login.orDivider")}
            </span>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          </div>

          <Field label={t("login.workEmail")}>
            <input
              id="login-email"
              type="email"
              className="input"
              placeholder={t("login.workEmailPlaceholder")}
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>

          <Button
            type="button"
            variant="primary"
            data-size="lg"
            iconRight="arrow_right"
            onClick={handleLogin}
          >
            {t("login.continue")}
          </Button>

          <div
            className="row subtle"
            style={{ fontSize: 11, justifyContent: "center", gap: 6 }}
          >
            <Icon name="shield" size={11} />
            <span>{t("login.mfaHint")}</span>
          </div>
        </div>
      </Card>

      {/* Sprint 57.23 Day 4 R8 hardening preserved: gate dev-link with DEV flag.
          Sprint 57.35 verbatim re-point: split existing `devLink` i18n string around
          the "dev-login" token to apply the mockup `mono` + var(--warning) accent on it
          (mockup page-extras.jsx:54). Falls back to plain text if the token is absent
          (e.g. translation overrides). */}
      {import.meta.env.DEV &&
        (() => {
          const raw = t("login.devLink");
          const token = "dev-login";
          const idx = raw.indexOf(token);
          const before = idx >= 0 ? raw.slice(0, idx) : raw;
          const after = idx >= 0 ? raw.slice(idx + token.length) : "";
          return (
            <Link
              to="/auth/dev"
              style={{
                fontSize: 11,
                color: "var(--fg-subtle)",
                textAlign: "center",
                textDecoration: "none",
              }}
            >
              {before}
              {idx >= 0 && (
                <span className="mono" style={{ color: "var(--warning)" }}>
                  {token}
                </span>
              )}
              {after}
            </Link>
          );
        })()}
    </AuthShell>
  );
}
