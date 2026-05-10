/**
 * File: frontend/src/pages/auth/login/index.tsx
 * Purpose: Login entry — "Login with WorkOS" button (OIDC) + dev fake-login form (DEV builds only).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.7 → US-A4 (dev fake-login) → US-B5 (i18n) → US-B9 (AuthShell + Tailwind)
 *
 * Description:
 *   "Login with ..." → window.location to /api/v1/auth/login (302 → vendor →
 *   IdP → /auth/callback). `?redirect_to=` carries the originally-attempted
 *   page through the round-trip; `?error=` surfaces a callback failure.
 *
 *   DEV-only: a <DevLoginSection> form (tenant_code + email) POSTs to
 *   /api/v1/auth/dev-login (404 in prod), then runs authStore.bootstrap()
 *   (the dev-login cookie authenticates /auth/me) and navigates to the
 *   stashed post-login page. Hidden in production builds via import.meta.env.DEV.
 *
 *   Sprint 57.13 US-B9: wrapped in <AuthShell> + <Card>; all strings via i18n
 *   (auth ns); inline styles replaced with Tailwind utilities; primary actions
 *   use <Button>; the error banner is a role="alert" surface.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <Card> + <Button>; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A4 — add DEV-only <DevLoginSection> (POST /auth/dev-login → bootstrap → navigate)
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:login + dev_login
 *   - frontend/src/components/AuthShell.tsx (layout shell for /auth/*)
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.* keys)
 */

import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, CardContent, CardHeader } from "@/components/ui";
import {
  consumePostLoginRedirect,
  fetchWithAuth,
  setPostLoginRedirect,
} from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

function ErrorAlert({ message }: { message: string }) {
  const { t } = useTranslation("auth");
  return (
    <div
      role="alert"
      className="mb-4 flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
      <span>
        <strong>{t("errorTitle")}:</strong> {message}
      </span>
    </div>
  );
}

/** DEV builds only — fake login without WorkOS (calls POST /api/v1/auth/dev-login). */
function DevLoginSection() {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const bootstrap = useAuthStore((s) => s.bootstrap);
  const [tenantCode, setTenantCode] = useState("dev");
  const [email, setEmail] = useState("dev@local");
  const [busy, setBusy] = useState(false);
  const [devError, setDevError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setDevError(null);
    try {
      const params = new URLSearchParams({ tenant_code: tenantCode, email });
      const res = await fetchWithAuth(`/api/v1/auth/dev-login?${params.toString()}`, {
        method: "POST",
      });
      if (!res.ok) {
        setDevError(
          res.status === 404
            ? t("devSection.errorDisabled")
            : t("devSection.errorFailed", { status: res.status }),
        );
        return;
      }
      // Cookie is set by the response; bootstrap re-reads it via /auth/me.
      await bootstrap();
      navigate(consumePostLoginRedirect(), { replace: true });
    } catch {
      setDevError(t("devSection.errorRequest"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="mt-8 border-t border-dashed border-border pt-6">
      <p className="mb-3 text-sm font-semibold text-muted-foreground">{t("devSection.heading")}</p>
      {devError ? <ErrorAlert message={devError} /> : null}
      <div className="mb-3 flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 text-xs text-muted-foreground" htmlFor="dev-login-tenant-code">
          tenant_code
          <input
            id="dev-login-tenant-code"
            value={tenantCode}
            onChange={(e) => setTenantCode(e.target.value)}
            className="rounded border border-border px-2 py-1 text-sm text-foreground"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground" htmlFor="dev-login-email">
          email
          <input
            id="dev-login-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded border border-border px-2 py-1 text-sm text-foreground"
          />
        </label>
      </div>
      <Button type="submit" variant="secondary" size="sm" disabled={busy}>
        {busy ? t("devSection.submitting") : t("devSection.submit")}
      </Button>
    </form>
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
    const redirectTo = params.get("redirect_to") || "/cost-dashboard";
    setPostLoginRedirect(redirectTo);
    window.location.href = `/api/v1/auth/login?redirect_to=${encodeURIComponent(redirectTo)}`;
  };

  return (
    <AuthShell>
      <div className="mx-auto max-w-md py-12">
        <Card>
          <CardHeader>
            {/* Page-level h1 (the login card is the whole page) — styled like CardTitle. */}
            <h1 className="text-lg font-semibold leading-none tracking-tight">{t("signInTitle")}</h1>
          </CardHeader>
          <CardContent>
            <p className="mb-6 text-sm text-muted-foreground">{t("signInSubtitle")}</p>

            {errorMessage ? <ErrorAlert message={errorMessage} /> : null}

            <Button type="button" onClick={handleLogin} className="w-full">
              {t("loginWithWorkOS")}
            </Button>

            {import.meta.env.DEV ? <DevLoginSection /> : null}
          </CardContent>
        </Card>
      </div>
    </AuthShell>
  );
}
