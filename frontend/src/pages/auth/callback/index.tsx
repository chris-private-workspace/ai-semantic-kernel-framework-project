/**
 * File: frontend/src/pages/auth/callback/index.tsx
 * Purpose: OIDC callback landing — bootstrap auth state then navigate to the original page.
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1
 *
 * Description:
 *   Backend /api/v1/auth/callback does the OIDC code exchange, sets the
 *   httpOnly v2_jwt cookie, then 302s the browser HERE with ?next=<original
 *   page>. This page runs authStore.bootstrap() (GET /auth/me, which the
 *   cookie authenticates) → then navigate(next). On vendor failure the
 *   backend redirects with ?error=<message> instead.
 *
 *   Tailwind-ize + <AuthShell> wrap deferred to Sprint 57.13 US-B9.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace); inline styles unchanged (US-B9)
 *   - 2026-05-10: Sprint 57.13 US-A1 — bootstrap-then-navigate via authStore; read ?next; drop dead ?token path
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:callback (302 here with v2_jwt cookie + ?next)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.* keys)
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { consumePostLoginRedirect } from "../../../features/auth/services/authService";
import { useAuthStore } from "../../../features/auth/store/authStore";

export default function CallbackPage() {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const bootstrap = useAuthStore((s) => s.bootstrap);

  useEffect(() => {
    const error = params.get("error");
    if (error) {
      setErrorMessage(decodeURIComponent(error));
      return;
    }

    let cancelled = false;
    void (async () => {
      await bootstrap();
      if (cancelled) return;
      const next = params.get("next") || consumePostLoginRedirect();
      navigate(next, { replace: true });
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate, params, bootstrap]);

  if (errorMessage) {
    return (
      <div
        style={{
          padding: "4rem 2rem",
          fontFamily: "system-ui, sans-serif",
          maxWidth: "480px",
          margin: "0 auto",
        }}
      >
        <h1>{t("errorTitle")}</h1>
        <div
          role="alert"
          style={{
            padding: "0.75rem 1rem",
            marginTop: "1rem",
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: "4px",
            color: "#900",
          }}
        >
          {errorMessage}
        </div>
        <p style={{ marginTop: "2rem" }}>
          <a href="/auth/login">{t("backToLogin")}</a>
        </p>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "4rem 2rem",
        fontFamily: "system-ui, sans-serif",
        textAlign: "center",
      }}
    >
      <p>{t("completing")}</p>
    </div>
  );
}
