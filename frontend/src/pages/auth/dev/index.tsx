/**
 * File: frontend/src/pages/auth/dev/index.tsx
 * Purpose: DEV-only dev-login page — verbatim re-point per mockup AuthDev (Sprint 57.35 US-B3).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-B3 (initial extract + mockup-direct HSL-translated) → Sprint 57.35 US-B3 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Sprint 57.35 US-B3 verbatim re-point per `reference/design-mockups/page-extras.jsx:109-152`:
 *     - Drop Tailwind translations of mockup `.hitl-card[data-severity="risk-high"]` + `.hitl-card-bar`
 *       + `.hitl-head` + `.icon-ring` (Sprint 57.23 used `rounded-lg border-destructive/40 bg-destructive/5`
 *       Tailwind translation; verbatim CSS classes already exist in styles-mockup.css L845-869).
 *     - Drop shadcn Card/CardContent/Button/Badge in favour of mockup-ui (Card emits `.card`/`.card-body`).
 *     - 3 fields use mockup-ui Field + `.select` verbatim per mockup L122-144.
 *     - Role badges use mockup-ui Badge with `tone="primary"` for selected (matches mockup L141).
 *     - `.hr` separator class verbatim (L145).
 *     - Continue Button uses mockup-ui `iconRight="arrow_right"`.
 *
 *   Production-build gate (App.tsx route is DEV-only): unchanged.
 *
 *   Behavioral logic preserved (Sprint 57.13 US-A4):
 *     - fetchWithAuth POST with tenant_code + email URLSearchParams
 *     - Cookie set by backend; bootstrap() re-reads via /auth/me
 *     - 404 maps to errorDisabled
 *
 * Created: 2026-05-18 (Sprint 57.23 US-B3)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 US-B3 — verbatim re-point per page-extras.jsx:109-152 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-B3) — extracted from login + mockup-direct AuthDev port
 *
 * Related:
 *   - backend/src/api/v1/auth.py:dev_login (POST /api/v1/auth/dev-login)
 *   - frontend/src/pages/auth/login/index.tsx (links to /auth/dev)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.dev.* namespace)
 *   - reference/design-mockups/page-extras.jsx:109-152 (AuthDev canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals + var(--warning) bridge copied byte-for-byte from mockup page-extras.jsx:109-152 (STYLE.md §1 escape hatch + Sprint 57.31 Hybrid Tailwind+inline color bridge precedent) */

import { type ChangeEvent, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, Field, Icon } from "@/components/mockup-ui";
import {
  consumePostLoginRedirect,
  fetchWithAuth,
} from "@/features/auth/services/authService";
import { useAuthStore } from "@/features/auth/store/authStore";

interface Identity {
  value: string;
  email: string;
  role: "operator" | "compliance" | "admin" | "platform";
}

interface TenantOption {
  value: string;
  label: string;
  code: string;
}

const IDENTITIES: Identity[] = [
  { value: "u_jamie", email: "jamie@acme.com", role: "operator" },
  { value: "u_priya", email: "priya@acme.com", role: "compliance" },
  { value: "u_dan", email: "dan@acme.com", role: "admin" },
  { value: "u_platform", email: "platform@beacon.dev", role: "platform" },
];

const TENANTS: TenantOption[] = [
  { value: "tenant_01h9a2", label: "acme-prod (Pro · ap-east-1)", code: "acme-prod" },
  { value: "tenant_01h7zz", label: "globex-eu (Pro · eu-west-1)", code: "globex-eu" },
  { value: "tenant_01h6kp", label: "initech-jp (Enterprise · ap-northeast-1)", code: "initech-jp" },
];

const ROLES = ["operator", "compliance", "admin", "platform"] as const;

export default function DevLoginPage() {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const bootstrap = useAuthStore((s) => s.bootstrap);

  const [identityValue, setIdentityValue] = useState<string>(IDENTITIES[0].value);
  const [tenantValue, setTenantValue] = useState<string>(TENANTS[0].value);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identity = IDENTITIES.find((i) => i.value === identityValue) ?? IDENTITIES[0];
  const tenant = TENANTS.find((t) => t.value === tenantValue) ?? TENANTS[0];

  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const params = new URLSearchParams({ tenant_code: tenant.code, email: identity.email });
      const res = await fetchWithAuth(`/api/v1/auth/dev-login?${params.toString()}`, {
        method: "POST",
      });
      if (!res.ok) {
        setError(
          res.status === 404
            ? t("dev.errorDisabled")
            : t("dev.errorFailed", { status: res.status }),
        );
        return;
      }
      await bootstrap();
      navigate(consumePostLoginRedirect(), { replace: true });
    } catch {
      setError(t("dev.errorRequest"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      footer={
        <span>
          {t("dev.footer").replace("DEV_LOGIN=true", "")}{" "}
          <span className="mono">DEV_LOGIN=true</span>
        </span>
      }
    >
      {/* Sprint 57.35 verbatim per mockup L111-120: risk-high warning card */}
      <div className="hitl-card" data-severity="risk-high" style={{ margin: 0 }}>
        <div className="hitl-card-bar" />
        <div className="hitl-head">
          <span className="icon-ring">
            <Icon name="warn" size={13} />
          </span>
          {t("dev.warningTitle")}
        </div>
        <div style={{ fontSize: 12.5, color: "var(--fg-muted)" }}>
          {t("dev.warningBody")}
        </div>
      </div>

      <Card>
        <form className="col" style={{ gap: 14 }} onSubmit={submit}>
          {error ? (
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
          ) : null}

          <Field label={t("dev.identityLabel")}>
            <select
              id="dev-identity"
              className="select"
              value={identityValue}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setIdentityValue(e.target.value)}
              style={{ height: 34, fontSize: 13 }}
            >
              {IDENTITIES.map((i) => (
                <option key={i.value} value={i.value}>
                  {i.email} · {i.role}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("dev.tenantLabel")}>
            <select
              id="dev-tenant"
              className="select"
              value={tenantValue}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => setTenantValue(e.target.value)}
              style={{ height: 34, fontSize: 13 }}
            >
              {TENANTS.map((tn) => (
                <option key={tn.value} value={tn.value}>
                  {tn.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label={t("dev.roleLabel")}>
            <div className="row" style={{ gap: 6 }}>
              {ROLES.map((r) => (
                <Badge key={r} tone={r === identity.role ? "primary" : ""}>
                  {r}
                </Badge>
              ))}
            </div>
          </Field>

          <div className="hr" style={{ margin: "2px 0" }} />

          <Button
            type="submit"
            variant="primary"
            data-size="lg"
            iconRight="arrow_right"
            disabled={busy}
          >
            {busy ? t("dev.submitting") : t("dev.continueAs", { email: identity.email })}
          </Button>
        </form>
      </Card>
    </AuthShell>
  );
}
