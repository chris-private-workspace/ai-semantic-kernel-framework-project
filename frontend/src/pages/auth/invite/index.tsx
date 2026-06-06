/**
 * File: frontend/src/pages/auth/invite/index.tsx
 * Purpose: Invite acceptance page — wired to the real invites backend (Sprint 57.85 US-5).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-D1 (NEW route) → 57.35 US-D1 (verbatim-CSS) → 57.85 US-5 (backend wire)
 *
 * Description:
 *   Verbatim mockup visual per `reference/design-mockups/page-auth-extras.jsx:190-246`
 *   (mockup-ui Card/Button/Badge/Field/Icon; .col/.row/.muted/.subtle/.mono/.spread/.input;
 *   56×56 primary-alpha avatar + 4-row metadata grid, inline-style verbatim).
 *
 *   Sprint 57.85 US-5 (C-12 IAM Block B invites backend now exists):
 *     - Removed the FIXTURE_METADATA fallback + AP-2 demo banner (the interim markers).
 *     - GET /api/v1/invites/{token} drives the metadata; 404 → invalid state, 410 →
 *       expired/used state, 200 → the accept form. POST /accept surfaces a real error
 *       on failure (was the demo "errorStubbed" message). The request body is unchanged
 *       ({full_name, password}); the backend accepts but does not yet store the password
 *       (local credentials are a 57.86 follow-up) — the field stays per the mockup.
 *
 * Created: 2026-05-18 (Sprint 57.23 US-D1)
 * Last Modified: 2026-06-06
 *
 * Modification History:
 *   - 2026-06-06: Sprint 57.85 US-5 — wire real backend (remove fixture + AP-2 banner; 404/410 states)
 *   - 2026-05-24: Sprint 57.35 US-D1 — verbatim re-point per page-auth-extras.jsx:190-246
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-D1) — mockup-direct port of AuthInvite
 *
 * Related:
 *   - backend/src/api/v1/invites.py (GET /invites/{token} + POST /invites/{token}/accept)
 *   - frontend/src/components/AuthShell.tsx + mockup-ui.tsx (Card/Button/Badge/Field/Icon)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.invite.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:190-246 (AuthInvite canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (avatar circle + metadata grid rows + danger note) copied byte-for-byte from mockup page-auth-extras.jsx:190-246 (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule) */

import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, Field, Icon } from "@/components/mockup-ui";
import { fetchWithAuth } from "@/features/auth/services/authService";

interface InviteMetadata {
  tenant: string;
  invitedBy: string;
  role: string;
  expiresIn: string;
}

type LoadState = "loading" | "ok" | "invalid" | "gone";

function DangerNote({ message }: { message: string }): JSX.Element {
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
      <span>{message}</span>
    </div>
  );
}

export default function InvitePage(): JSX.Element {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();
  const [metadata, setMetadata] = useState<InviteMetadata | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
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
          setMetadata((await res.json()) as InviteMetadata);
          setLoadState("ok");
        } else if (res.status === 410) {
          setLoadState("gone");
        } else {
          setLoadState("invalid");
        }
      } catch {
        if (!cancelled) setLoadState("invalid");
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
        setError(t("invite.acceptError"));
        return;
      }
      navigate("/auth/mfa");
    } catch {
      setError(t("invite.acceptError"));
    } finally {
      setBusy(false);
    }
  };

  const footer = (
    <span>
      {t("invite.foot")}{" "}
      <Link to="/auth/login" style={{ color: "var(--primary)", textDecoration: "none" }}>
        {t("register.signIn")}
      </Link>
    </span>
  );

  if (loadState === "loading") {
    return (
      <AuthShell footer={footer}>
        <Card>
          <div
            className="muted"
            style={{ fontSize: 12.5, textAlign: "center", padding: "16px 0" }}
          >
            {t("invite.loading")}
          </div>
        </Card>
      </AuthShell>
    );
  }

  if (loadState !== "ok" || metadata === null) {
    return (
      <AuthShell footer={footer}>
        <Card>
          <DangerNote message={loadState === "gone" ? t("invite.gone") : t("invite.invalid")} />
        </Card>
      </AuthShell>
    );
  }

  return (
    <AuthShell footer={footer}>
      <Card>
        <form onSubmit={accept} className="col" style={{ gap: 16 }}>
          {/* Header — verbatim mockup L194-208 */}
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
              <Icon name="user" size={26} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {t("invite.title")}
              </div>
              <div className="muted" style={{ fontSize: 12.5 }}>
                {t("invite.subtitle")}
              </div>
            </div>
          </div>

          {/* Metadata grid — verbatim mockup L210-227 */}
          <div
            className="col"
            style={{
              gap: 0,
              background: "var(--bg-1)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <div
              className="spread"
              style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}
            >
              <span className="muted">{t("invite.tenant")}</span>
              <span className="mono">{metadata.tenant}</span>
            </div>
            <div
              className="spread"
              style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}
            >
              <span className="muted">{t("invite.invitedBy")}</span>
              <span>{metadata.invitedBy}</span>
            </div>
            <div
              className="spread"
              style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}
            >
              <span className="muted">{t("invite.role")}</span>
              <Badge tone="primary">{metadata.role}</Badge>
            </div>
            <div className="spread" style={{ padding: "10px 12px", fontSize: 12 }}>
              <span className="muted">{t("invite.expires")}</span>
              <span className="mono subtle">{metadata.expiresIn}</span>
            </div>
          </div>

          {/* Error surface */}
          {error && <DangerNote message={error} />}

          {/* Fields — verbatim mockup L229-234 */}
          <Field label={t("invite.fullName")}>
            <input
              id="inv-name"
              className="input"
              value={fullName}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
              placeholder="Jamie Liu"
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>
          <Field label={t("invite.password")} help={t("invite.passwordHint")}>
            <input
              id="inv-password"
              type="password"
              className="input"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{ height: 36, fontSize: 13.5 }}
            />
          </Field>

          {/* Accept button — verbatim mockup L236-238 */}
          <Button type="submit" variant="primary" data-size="lg" iconRight="arrow_right" disabled={busy}>
            {busy ? t("invite.accepting") : t("invite.accept")}
          </Button>

          {/* MFA hint — verbatim mockup L239-242 */}
          <div className="row subtle" style={{ fontSize: 11, justifyContent: "center", gap: 6 }}>
            <Icon name="shield" size={11} />
            <span>{t("invite.mfaHint")}</span>
          </div>
        </form>
      </Card>
    </AuthShell>
  );
}
