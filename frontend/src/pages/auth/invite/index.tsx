/**
 * File: frontend/src/pages/auth/invite/index.tsx
 * Purpose: Invite acceptance page — accept invite + set password before MFA (mockup AuthInvite direct port).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D1 (NEW route)
 *
 * Description:
 *   Sprint 57.23 US-D1 NEW per `reference/design-mockups/page-auth-extras.jsx:191-246`:
 *     - AuthShell wrapped with footer ("Already a member? Sign in")
 *     - 56×56 primary-alpha user-icon avatar + title "You're invited to acme-prod" + subtitle
 *     - 4-row metadata grid: Tenant / Invited by / Role (Badge primary) / Expires
 *     - Full name + Set password fields with 12+ char hint
 *     - Accept invitation primary button
 *     - MFA notice shield-icon row below button
 *
 *   Backend stub:
 *     - GET /api/v1/invites/:token expected 501; falls back to fixture metadata
 *     - POST /api/v1/invites/:token/accept expected 501; surfaces demo-banner-style error
 *     - AD-Auth-Invite-Backend-IAM-Block-B-Phase58 carryover for real implementation
 *     - "Backend wire pending Phase 58+ IAM Block B" demo banner
 *
 *   On success (Phase 58+): navigate to /auth/mfa (mockup AuthInvite L235 flow continuation).
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D1)
 *
 * Modification History:
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-D1) — mockup-direct port of AuthInvite
 *
 * Related:
 *   - backend/src/api/v1/invites.py (Phase 58+ NEW; AD-IAM-Block-B-Phase58)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.invite.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:191-246 (AuthInvite canonical visual source)
 */

import { AlertTriangle, ArrowRight, ShieldCheck, User } from "lucide-react";
import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, CardContent } from "@/components/ui";
import { fetchWithAuth } from "@/features/auth/services/authService";

interface InviteMetadata {
  tenant: string;
  invitedBy: string;
  role: string;
  expiresIn: string;
}

const FIXTURE_METADATA: InviteMetadata = {
  tenant: "acme-prod · ap-east-1",
  invitedBy: "dan@acme.com",
  role: "operator",
  expiresIn: "in 6 days",
};

export default function InvitePage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();
  const [metadata, setMetadata] = useState<InviteMetadata>(FIXTURE_METADATA);
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadMetadata(): Promise<void> {
      try {
        const res = await fetchWithAuth(`/api/v1/invites/${token ?? ""}`);
        if (cancelled) return;
        if (res.ok) {
          const data = (await res.json()) as Partial<InviteMetadata>;
          setMetadata({ ...FIXTURE_METADATA, ...data });
        }
        // 501 stub → keep fixture (no error surface; demo banner explains)
      } catch {
        // Network error → keep fixture
      }
    }
    void loadMetadata();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const accept = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth(`/api/v1/invites/${token ?? ""}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, password }),
      });
      if (!res.ok) {
        setError(t("invite.errorStubbed"));
        return;
      }
      navigate("/auth/mfa");
    } catch {
      setError(t("invite.errorStubbed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      footer={
        <span>
          {t("invite.foot")}{" "}
          <Link to="/auth/login" className="text-primary hover:underline">
            {t("register.signIn")}
          </Link>
        </span>
      }
    >
      <Card>
        <CardContent className="p-6">
          <form onSubmit={accept} className="flex flex-col gap-4">
            {/* Header (mockup L194-208) */}
            <div className="flex flex-col items-center gap-2.5 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/15 text-primary">
                <User size={26} aria-hidden />
              </div>
              <div>
                <div className="mb-1 text-base font-semibold">{t("invite.title")}</div>
                <div className="text-[12.5px] text-fg-muted">{t("invite.subtitle")}</div>
              </div>
            </div>

            {/* AP-2 demo banner */}
            <div
              role="note"
              className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-[11px] text-warning"
            >
              {t("invite.demoBanner")}
            </div>

            {/* Metadata grid (mockup L210-227) */}
            <div className="flex flex-col rounded-md border border-border bg-bg-1">
              <div className="flex flex-row items-center justify-between border-b border-border px-3 py-2.5 text-[12px]">
                <span className="text-fg-muted">{t("invite.tenant")}</span>
                <span className="font-mono">{metadata.tenant}</span>
              </div>
              <div className="flex flex-row items-center justify-between border-b border-border px-3 py-2.5 text-[12px]">
                <span className="text-fg-muted">{t("invite.invitedBy")}</span>
                <span>{metadata.invitedBy}</span>
              </div>
              <div className="flex flex-row items-center justify-between border-b border-border px-3 py-2.5 text-[12px]">
                <span className="text-fg-muted">{t("invite.role")}</span>
                <Badge>{metadata.role}</Badge>
              </div>
              <div className="flex flex-row items-center justify-between px-3 py-2.5 text-[12px]">
                <span className="text-fg-muted">{t("invite.expires")}</span>
                <span className="font-mono text-fg-subtle">{metadata.expiresIn}</span>
              </div>
            </div>

            {/* Error surface */}
            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
              >
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Fields (mockup L229-234) */}
            <div className="flex flex-col gap-1">
              <label htmlFor="inv-name" className="text-[12px] font-medium text-fg-muted">
                {t("invite.fullName")}
              </label>
              <input
                id="inv-name"
                value={fullName}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
                placeholder="Jamie Liu"
                className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="inv-password" className="text-[12px] font-medium text-fg-muted">
                {t("invite.password")}
              </label>
              <input
                id="inv-password"
                type="password"
                value={password}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <div className="text-[11px] text-fg-subtle">{t("invite.passwordHint")}</div>
            </div>

            {/* Accept button (mockup L236-238) */}
            <Button type="submit" disabled={busy}>
              {busy ? t("invite.accepting") : t("invite.accept")}
              <ArrowRight size={16} className="ml-1" />
            </Button>

            {/* MFA hint (mockup L239-242) */}
            <div className="flex flex-row items-center justify-center gap-1.5 text-[11px] text-fg-subtle">
              <ShieldCheck size={11} aria-hidden />
              <span>{t("invite.mfaHint")}</span>
            </div>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
