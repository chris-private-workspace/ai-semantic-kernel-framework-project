/**
 * File: frontend/src/pages/auth/password-login/index.tsx
 * Purpose: Local-password sign-in page — tenant_code + email + password (Sprint 57.86 US-4).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.86 (C-12 IAM Block B/C — local credentials)
 *
 * Description:
 *   The main-flow UI consumer for POST /api/v1/auth/password-login: an invited
 *   user who set a password at invite-accept signs back in here without SSO.
 *   Built from the existing AuthShell + mockup-ui primitives (Card/Field/Button/
 *   Icon) reusing existing styles-mockup.css classes — NO new CSS. Mirrors the
 *   dev-login page flow (POST → authStore.bootstrap() → navigate) but posts a
 *   JSON body (creds never in the query string) and surfaces a single generic
 *   error (the backend returns one generic 401 for every failure — no
 *   enumeration). The mockup parent is reference/design-mockups/page-auth-
 *   extras.jsx:AuthPasswordLogin (added the same sprint so fidelity stays honest).
 *
 * Created: 2026-06-06 (Sprint 57.86 US-4)
 * Last Modified: 2026-06-06
 *
 * Modification History:
 *   - 2026-06-06: Initial creation (Sprint 57.86 US-4) — local password-login page
 *
 * Related:
 *   - backend/src/api/v1/auth.py:password_login (POST /api/v1/auth/password-login)
 *   - frontend/src/pages/auth/dev/index.tsx (POST → bootstrap → navigate pattern)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/features/auth/services/authService.ts (fetchWithAuth / consumePostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.passwordLogin.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:AuthPasswordLogin (canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim inline-style literals (avatar circle + error alert oklch tints) copied from the invite/dev auth pages (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule) */

import { type ChangeEvent, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, Field, Icon } from "@/components/mockup-ui";
import { consumePostLoginRedirect, fetchWithAuth } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

export default function PasswordLoginPage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const bootstrap = useAuthStore((s) => s.bootstrap);

  const [tenantCode, setTenantCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth(
        "/api/v1/auth/password-login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tenant_code: tenantCode, email, password }),
        },
        // A wrong password returns 401 — handle it here (show the generic error),
        // do NOT let fetchWithAuth treat it as an expired session + bounce to SSO.
        { redirectOn401: false },
      );
      if (!res.ok) {
        setError(t("passwordLogin.error"));
        return;
      }
      await bootstrap();
      navigate(consumePostLoginRedirect(), { replace: true });
    } catch {
      setError(t("passwordLogin.errorRequest"));
    } finally {
      setBusy(false);
    }
  };

  const footer = (
    <span>
      {t("passwordLogin.foot")}{" "}
      <Link to="/auth/login" style={{ color: "var(--primary)", textDecoration: "none" }}>
        {t("passwordLogin.ssoLink")}
      </Link>
    </span>
  );

  return (
    <AuthShell footer={footer}>
      <Card>
        <form onSubmit={submit} className="col" style={{ gap: 16 }}>
          {/* Header */}
          <div className="col" style={{ gap: 10, alignItems: "center", textAlign: "center" }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "oklch(from var(--primary) l c h / 0.14)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--primary)",
              }}
              aria-hidden
            >
              <Icon name="shield" size={26} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {t("passwordLogin.title")}
              </div>
              <div className="muted" style={{ fontSize: 12.5 }}>
                {t("passwordLogin.subtitle")}
              </div>
            </div>
          </div>

          {/* Error surface (single generic message) */}
          {error && (
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
              <span>{error}</span>
            </div>
          )}

          {/* Fields */}
          <Field label={t("passwordLogin.tenantCode")}>
            <input
              id="pwl-tenant"
              className="input"
              value={tenantCode}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setTenantCode(e.target.value)}
              placeholder="acme-prod"
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>
          <Field label={t("passwordLogin.email")}>
            <input
              id="pwl-email"
              type="email"
              className="input"
              value={email}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              placeholder="you@acme.com"
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>
          <Field label={t("passwordLogin.password")}>
            <input
              id="pwl-password"
              type="password"
              className="input"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>

          <Button
            type="submit"
            variant="primary"
            data-size="lg"
            iconRight="arrow_right"
            disabled={busy || !tenantCode || !email || !password}
          >
            {busy ? t("passwordLogin.submitting") : t("passwordLogin.submit")}
          </Button>
        </form>
      </Card>
    </AuthShell>
  );
}
