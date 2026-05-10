/**
 * File: frontend/src/pages/auth/callback/index.tsx
 * Purpose: OIDC callback landing — bootstrap auth state then navigate to the original page.
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1 → US-B5 (i18n) → US-B9 (AuthShell + Tailwind)
 *
 * Description:
 *   Backend /api/v1/auth/callback does the OIDC code exchange, sets the
 *   httpOnly v2_jwt cookie, then 302s the browser HERE with ?next=<original
 *   page>. This page runs authStore.bootstrap() (GET /auth/me, which the
 *   cookie authenticates) → then navigate(next). On vendor failure the
 *   backend redirects with ?error=<message> instead.
 *
 *   Sprint 57.13 US-B9: wrapped in <AuthShell>; loading = spinner + i18n text;
 *   error = <EmptyState> with a "Back to login" <Button asChild><Link>>; inline
 *   styles dropped.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-10
 *
 * Modification History:
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <EmptyState> error + spinner loading; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A1 — bootstrap-then-navigate via authStore; read ?next; drop dead ?token path
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:callback (302 here with v2_jwt cookie + ?next)
 *   - frontend/src/components/AuthShell.tsx (layout shell for /auth/*)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.* keys)
 */

import { AlertTriangle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, EmptyState } from "@/components/ui";
import { consumePostLoginRedirect } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

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

  return (
    <AuthShell>
      <div className="mx-auto max-w-md py-12">
        {errorMessage ? (
          <div role="alert">
            <EmptyState
              icon={<AlertTriangle size={32} className="text-destructive" />}
              title={t("errorTitle")}
              message={errorMessage}
              action={
                <Button asChild variant="outline">
                  <Link to="/auth/login">{t("backToLogin")}</Link>
                </Button>
              }
            />
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-8 text-muted-foreground" role="status">
            <Loader2 size={24} className="animate-spin" />
            <p>{t("completing")}</p>
          </div>
        )}
      </div>
    </AuthShell>
  );
}
