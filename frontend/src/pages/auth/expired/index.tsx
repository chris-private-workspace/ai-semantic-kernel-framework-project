/**
 * File: frontend/src/pages/auth/expired/index.tsx
 * Purpose: Session-expired splash — surfaces last-activity / session_id / reason + 2 recovery CTAs (mockup AuthExpired direct port).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D3 (NEW route)
 *
 * Description:
 *   Sprint 57.23 US-D3 NEW per `reference/design-mockups/page-auth-extras.jsx:374-416`:
 *     - AuthShell wrapped (no footer per mockup L375 — AuthShellX with empty footer slot)
 *     - 56×56 warning-alpha clock-icon avatar + title "Your session expired" + subtitle (320px max)
 *     - 3-row metadata grid: Last activity / Session ID / Reason (Badge tone=warning)
 *     - 2 buttons row: "Sign in again" (outline) + "Resume session" (primary with arrow)
 *     - Data-preservation hint below (11px subtle, 320px max)
 *
 *   Query param contract (consumed via useSearchParams):
 *     - ?session_id=<id>  → displayed in metadata grid; falls back to fixture sess_8a2f1c3
 *     - ?reason=<reason>  → displayed in Badge; falls back to fixture jwt_expired · 24h max
 *     - ?next=<path>      → forwarded to /auth/callback?next= on "Resume session" click
 *
 *   Backend invariants:
 *     - This page is purely client-side splash. JWT expiry is the trigger; backend has already
 *       returned 401 from a previous request. No fetch on mount.
 *     - "Sign in again" → /auth/login (forces fresh SAML / OIDC flow)
 *     - "Resume session" → /auth/callback?next=<original> (attempts silent refresh via existing
 *       authBootstrap mechanism, then restores original path if successful)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D3)
 *
 * Modification History:
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-D3) — mockup-direct port of AuthExpired
 *
 * Related:
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.expired.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:374-416 (AuthExpired canonical visual source)
 */

import { ArrowRight, Clock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, CardContent } from "@/components/ui";

const FIXTURE_LAST_ACTIVITY = "14h 02m ago";
const FIXTURE_SESSION_ID = "sess_8a2f1c3";
const FIXTURE_REASON = "jwt_expired · 24h max";

export default function ExpiredPage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const sessionId = searchParams.get("session_id") ?? FIXTURE_SESSION_ID;
  const reason = searchParams.get("reason") ?? FIXTURE_REASON;
  const next = searchParams.get("next");

  const signInAgain = (): void => navigate("/auth/login");
  const resume = (): void => {
    const target = next ? `/auth/callback?next=${encodeURIComponent(next)}` : "/auth/callback";
    navigate(target);
  };

  return (
    <AuthShell>
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col items-center gap-4 p-2 text-center">
            {/* Icon (mockup L378-384) */}
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-warning/15 text-warning">
              <Clock size={26} aria-hidden />
            </div>

            {/* Title + subtitle (mockup L385-388) */}
            <div>
              <div className="mb-1.5 text-[17px] font-semibold">{t("expired.title")}</div>
              <div className="mx-auto max-w-[320px] text-[13px] leading-[1.5] text-fg-muted">
                {t("expired.subtitle")}
              </div>
            </div>

            {/* Metadata grid (mockup L390-403) */}
            <div className="flex w-full flex-col rounded-md border border-border bg-bg-1">
              <div className="flex flex-row items-center justify-between border-b border-border px-3 py-2 text-[11.5px]">
                <span className="text-fg-muted">{t("expired.lastActivity")}</span>
                <span className="font-mono">{FIXTURE_LAST_ACTIVITY}</span>
              </div>
              <div className="flex flex-row items-center justify-between border-b border-border px-3 py-2 text-[11.5px]">
                <span className="text-fg-muted">{t("expired.sessionId")}</span>
                <span className="font-mono text-fg-subtle">{sessionId}</span>
              </div>
              <div className="flex flex-row items-center justify-between px-3 py-2 text-[11.5px]">
                <span className="text-fg-muted">{t("expired.reason")}</span>
                <Badge>{reason}</Badge>
              </div>
            </div>

            {/* Buttons row (mockup L405-408) */}
            <div className="mt-1 flex w-full flex-row gap-2">
              <Button variant="outline" onClick={signInAgain} className="flex-1">
                {t("expired.signInAgain")}
              </Button>
              <Button onClick={resume} className="flex-1">
                {t("expired.resume")}
                <ArrowRight size={16} className="ml-1" />
              </Button>
            </div>

            {/* Data hint (mockup L410-412) */}
            <div className="mx-auto mt-0.5 max-w-[320px] text-[11px] leading-[1.5] text-fg-muted">
              {t("expired.dataHint")}
            </div>
          </div>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
