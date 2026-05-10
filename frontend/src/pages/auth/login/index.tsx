/**
 * File: frontend/src/pages/auth/login/index.tsx
 * Purpose: Login entry — "Login with WorkOS" button (OIDC) + dev fake-login form (DEV builds only).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.7 → Sprint 57.13 US-A4 (dev fake-login)
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
 *   Tailwind-ize the inline styles + <AuthShell> wrap: Sprint 57.13 US-B9.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace); inline styles unchanged (US-B9)
 *   - 2026-05-10: Sprint 57.13 US-A4 — add DEV-only <DevLoginSection> (POST /auth/dev-login → bootstrap → navigate)
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:login + dev_login
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.* keys)
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  consumePostLoginRedirect,
  fetchWithAuth,
  setPostLoginRedirect,
} from "../../../features/auth/services/authService";
import { useAuthStore } from "../../../features/auth/store/authStore";

function ErrorBanner({ message }: { message: string }) {
  const { t } = useTranslation("auth");
  return (
    <div
      role="alert"
      style={{
        padding: "0.75rem 1rem",
        marginBottom: "1.5rem",
        backgroundColor: "#fee",
        border: "1px solid #fcc",
        borderRadius: "4px",
        color: "#900",
      }}
    >
      <strong>{t("errorTitle")}:</strong> {message}
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
        const detail =
          res.status === 404
            ? t("devSection.errorDisabled")
            : t("devSection.errorFailed", { status: res.status });
        setDevError(detail);
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
    <form
      onSubmit={submit}
      style={{
        marginTop: "2.5rem",
        paddingTop: "1.5rem",
        borderTop: "1px dashed #ccc",
      }}
    >
      <p style={{ fontSize: "0.85rem", fontWeight: 600, color: "#555", marginBottom: "0.75rem" }}>
        {t("devSection.heading")}
      </p>
      {devError ? <ErrorBanner message={devError} /> : null}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
        <label style={{ display: "flex", flexDirection: "column", fontSize: "0.8rem", color: "#666" }}>
          tenant_code
          <input
            value={tenantCode}
            onChange={(e) => setTenantCode(e.target.value)}
            style={{ padding: "0.4rem", border: "1px solid #ccc", borderRadius: "4px" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", fontSize: "0.8rem", color: "#666" }}>
          email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ padding: "0.4rem", border: "1px solid #ccc", borderRadius: "4px" }}
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={busy}
        style={{
          padding: "0.5rem 1rem",
          fontSize: "0.9rem",
          backgroundColor: busy ? "#999" : "#444",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: busy ? "default" : "pointer",
        }}
      >
        {busy ? t("devSection.submitting") : t("devSection.submit")}
      </button>
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
    <div
      style={{
        padding: "4rem 2rem",
        fontFamily: "system-ui, sans-serif",
        maxWidth: "480px",
        margin: "0 auto",
      }}
    >
      <h1 style={{ marginBottom: "1rem" }}>{t("signInTitle")}</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>{t("signInSubtitle")}</p>

      {errorMessage ? <ErrorBanner message={errorMessage} /> : null}

      <button
        type="button"
        onClick={handleLogin}
        style={{
          padding: "0.75rem 1.5rem",
          fontSize: "1rem",
          fontWeight: 600,
          backgroundColor: "#0078d4",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        {t("loginWithWorkOS")}
      </button>

      {import.meta.env.DEV ? <DevLoginSection /> : null}
    </div>
  );
}
