/**
 * File: frontend/src/pages/auth/callback/index.tsx
 * Purpose: OIDC callback landing — mockup-direct rewrite with timed 3-step progress UI + parallel bootstrap.
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1 → Sprint 57.23 US-C1 (timed 3-step progress per mockup AuthCallback)
 *
 * Description:
 *   Sprint 57.23 US-C1 rewrite per `reference/design-mockups/page-extras.jsx:59-107`:
 *     - Conic-gradient spinning ring (animation: spin 1.2s linear infinite)
 *     - "Completing sign-in…" + `callback=acme.workos.com` mono subtitle
 *     - 3-step progress list with timed setTimeout transitions (800/1800/2800ms):
 *       1. Verifying SAML assertion
 *       2. Resolving tenant + RLS context
 *       3. Loading feature flags + memory scopes
 *     - Steps show success-token-tinted check icon when `step > index`; else outline placeholder
 *
 *   Backend bootstrap runs in parallel with timed UI; min 2800ms enforced so all 3
 *   steps render before navigate (UX consistency — silent-redirect on fast vendor
 *   would skip the progress affordance). When real backend SSE per-step status
 *   emission arrives (AD-Auth-Callback-Loading-UX-Phase58), this frontend
 *   simulation will swap for real status feed.
 *
 *   Preserved Sprint 57.13 logic:
 *     - `?error=` short-circuits before everything → EmptyState + Back to login
 *     - `useAuthStore.bootstrap()` runs after timed UI starts
 *     - `?next=` param OR `consumePostLoginRedirect()` post-bootstrap navigation
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-18
 *
 * Modification History:
 *   - 2026-05-18: Sprint 57.23 US-C1 — mockup-direct rewrite with timed 3-step progress + parallel bootstrap (min 2800ms)
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <EmptyState> error + spinner loading; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A1 — bootstrap-then-navigate via authStore; read ?next; drop dead ?token path
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:callback (302 here with v2_jwt cookie + ?next)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.callback.* / errorTitle / backToLogin)
 *   - reference/design-mockups/page-extras.jsx:59-107 (AuthCallback canonical visual source)
 */

import { AlertTriangle, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, CardContent, EmptyState } from "@/components/ui";
import { consumePostLoginRedirect } from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

const MIN_DURATION_MS = 2800;

export default function CallbackPage() {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const bootstrap = useAuthStore((s) => s.bootstrap);

  useEffect(() => {
    const error = params.get("error");
    if (error) {
      setErrorMessage(decodeURIComponent(error));
      return;
    }

    let cancelled = false;
    const startTime = Date.now();

    // Mockup AuthCallback timed step transitions (page-extras.jsx:60-65)
    const t1 = setTimeout(() => !cancelled && setStep(1), 800);
    const t2 = setTimeout(() => !cancelled && setStep(2), 1800);
    const t3 = setTimeout(() => !cancelled && setStep(3), 2800);

    // Bootstrap runs in parallel with timed UI; enforce min duration so all 3 steps render
    void (async () => {
      await bootstrap();
      if (cancelled) return;
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, MIN_DURATION_MS - elapsed);
      setTimeout(() => {
        if (cancelled) return;
        const next = params.get("next") || consumePostLoginRedirect();
        navigate(next, { replace: true });
      }, remaining);
    })();

    return () => {
      cancelled = true;
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [navigate, params, bootstrap]);

  // Sprint 57.23 US-C1: 3 progress steps per mockup AuthCallback L67-71
  const steps = [
    { key: "verifySaml", label: t("callback.steps.verifySaml"), done: step > 0 },
    { key: "resolveTenant", label: t("callback.steps.resolveTenant"), done: step > 1 },
    { key: "loadFlags", label: t("callback.steps.loadFlags"), done: step > 2 },
  ];

  if (errorMessage) {
    return (
      <AuthShell>
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
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <Card>
        <CardContent className="p-6">
          <div role="status" className="flex flex-col items-center gap-[18px] p-2 text-center">
            {/* Conic-gradient spinning ring (mockup AuthCallback L76-83) */}
            <div
              className="flex h-12 w-12 items-center justify-center rounded-full"
              // eslint-disable-next-line no-restricted-syntax -- STYLE.md §3 escape hatch: conic-gradient + custom animation duration (mockup 1.2s vs Tailwind animate-spin 2s default)
              style={{
                background:
                  "conic-gradient(from 0deg, var(--primary), transparent 70%)",
                animation: "spin 1.2s linear infinite",
              }}
              aria-hidden
            >
              <div className="h-9 w-9 rounded-full bg-bg-1" />
            </div>

            <div>
              <div className="text-[15px] font-semibold">{t("completing")}</div>
              <div className="mt-1 font-mono text-[11.5px] text-fg-muted">
                {t("callback.callbackUrlPrefix")}={t("callback.callbackUrlHost")}
              </div>
            </div>

            <div className="mt-2 flex flex-col items-stretch gap-2 self-stretch">
              {steps.map((s) => (
                <div key={s.key} className="flex flex-row items-center gap-2 text-[12px]">
                  <span
                    className={
                      s.done
                        ? "flex h-3.5 w-3.5 items-center justify-center rounded-full bg-success"
                        : "flex h-3.5 w-3.5 items-center justify-center rounded-full border border-border bg-bg-3"
                    }
                    aria-hidden
                  >
                    {s.done ? <Check size={9} className="text-white" /> : null}
                  </span>
                  <span className={s.done ? "text-foreground" : "text-fg-muted"}>{s.label}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
