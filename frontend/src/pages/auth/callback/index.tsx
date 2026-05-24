/**
 * File: frontend/src/pages/auth/callback/index.tsx
 * Purpose: OIDC callback landing — verbatim re-point per mockup AuthCallback (Sprint 57.35 US-C1).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.13 US-A1 → Sprint 57.23 US-C1 (timed 3-step progress) → Sprint 57.35 US-C1 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Sprint 57.35 US-C1 verbatim re-point per `reference/design-mockups/page-extras.jsx:59-107`:
 *     - Drop shadcn Card/CardContent/Button/EmptyState + lucide-react Check/AlertTriangle
 *     - Use mockup-ui Card + Button + Icon (check + warn)
 *     - Verbatim .col + .row + .muted + .mono classes
 *     - Conic-gradient spinning ring + inline-style step badges per mockup L76-100
 *     - Preserved: timed 3-step transitions (800/1800/2800ms) + parallel bootstrap +
 *       min 2800ms enforced + ?error= short-circuit + ?next= navigation
 *
 *   Backend bootstrap runs in parallel with timed UI; min 2800ms enforced.
 *   AD-Auth-Callback-Loading-UX-Phase58 will swap simulation for real SSE per-step feed.
 *
 * Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 US-C1 — verbatim re-point per page-extras.jsx:59-107 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-18: Sprint 57.23 US-C1 — mockup-direct rewrite with timed 3-step progress + parallel bootstrap (min 2800ms)
 *   - 2026-05-10: Sprint 57.13 US-B9 — <AuthShell> + <EmptyState> error + spinner loading; drop inline styles
 *   - 2026-05-10: Sprint 57.13 US-B5 — i18n the strings (auth namespace)
 *   - 2026-05-10: Sprint 57.13 US-A1 — bootstrap-then-navigate via authStore; read ?next; drop dead ?token path
 *   - 2026-05-09: Initial skeleton (Sprint 57.7 US-A2 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/auth.py:callback (302 here with v2_jwt cookie + ?next)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.35 verbatim re-point)
 *   - frontend/src/components/mockup-ui.tsx (Card / Button / Icon primitives)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.callback.* / errorTitle / backToLogin)
 *   - reference/design-mockups/page-extras.jsx:59-107 (AuthCallback canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (conic-gradient spinner + step badges + container) copied byte-for-byte from mockup page-extras.jsx:73-105 (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule) */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Button, Card, Icon } from "@/components/mockup-ui";
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

  // Sprint 57.23 US-C1 / 57.35 US-C1 verbatim: 3 progress steps per mockup AuthCallback L67-71
  const steps = [
    { key: "verifySaml", label: t("callback.steps.verifySaml"), done: step > 0 },
    { key: "resolveTenant", label: t("callback.steps.resolveTenant"), done: step > 1 },
    { key: "loadFlags", label: t("callback.steps.loadFlags"), done: step > 2 },
  ];

  if (errorMessage) {
    return (
      <AuthShell>
        <Card>
          <div
            role="alert"
            className="col"
            style={{ gap: 14, alignItems: "center", textAlign: "center", padding: 8 }}
          >
            <Icon name="warn" size={32} style={{ color: "var(--danger)" }} />
            <div>
              <div style={{ fontSize: 15, fontWeight: 600 }}>{t("errorTitle")}</div>
              <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>{errorMessage}</div>
            </div>
            <Button variant="outline" data-size="lg">
              <Link
                to="/auth/login"
                style={{ color: "inherit", textDecoration: "none" }}
              >
                {t("backToLogin")}
              </Link>
            </Button>
          </div>
        </Card>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <Card>
        <div
          role="status"
          className="col"
          style={{ gap: 18, alignItems: "center", textAlign: "center", padding: 8 }}
        >
          {/* Conic-gradient spinning ring — mockup L76-83 */}
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: "50%",
              background:
                "conic-gradient(from 0deg, var(--primary), transparent 70%)",
              animation: "spin 1.2s linear infinite",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            aria-hidden
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                background: "var(--bg-1)",
              }}
            />
          </div>

          <div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{t("completing")}</div>
            <div className="muted mono" style={{ fontSize: 11.5, marginTop: 4 }}>
              {t("callback.callbackUrlPrefix")}={t("callback.callbackUrlHost")}
            </div>
          </div>

          <div className="col" style={{ gap: 8, alignSelf: "stretch", marginTop: 8 }}>
            {steps.map((s) => (
              <div key={s.key} className="row" style={{ gap: 8, fontSize: 12 }}>
                <span
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: "50%",
                    background: s.done ? "var(--success)" : "var(--bg-3)",
                    border: s.done ? "none" : "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  aria-hidden
                >
                  {s.done && <Icon name="check" size={9} style={{ color: "white" }} />}
                </span>
                <span style={{ color: s.done ? "var(--fg)" : "var(--fg-muted)" }}>
                  {s.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </AuthShell>
  );
}
