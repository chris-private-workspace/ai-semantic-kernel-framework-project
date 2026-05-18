/**
 * File: frontend/src/pages/auth/dev/index.tsx
 * Purpose: DEV-only dev-login page extracted from prior login DevLoginSection (Sprint 57.23 US-B3).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-B3 (extract from login + mockup-direct rebuild)
 *
 * Description:
 *   Sprint 57.23 US-B3 NEW per `reference/design-mockups/page-extras.jsx:109-152`:
 *     - risk-high warning card at top (banner pattern matches HITL severity card visual)
 *     - Card with 3 fields: Assume identity (select 4 fixtures) + Tenant (select 3 fixtures) + Role (4 read-only badges)
 *     - Continue-as primary button → POST /api/v1/auth/dev-login (tenant_code + email)
 *     - On success: useAuthStore.bootstrap() → consumePostLoginRedirect()
 *
 *   Production-build gate: App.tsx wraps `<Route>` in `{import.meta.env.DEV && ...}` so
 *   production bundle excludes route entirely. `npm run build && grep "auth/dev" dist/`
 *   should return 0 lines (R8 mitigation; verified Day 4 closeout).
 *
 *   Behavioral logic preserved from prior login DevLoginSection (Sprint 57.13 US-A4):
 *     - fetchWithAuth POST with tenant_code + email URLSearchParams
 *     - Cookie set by backend; bootstrap() re-reads via /auth/me
 *     - 404 maps to errorDisabled (DEV_LOGIN=true gating at backend)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-B3)
 *
 * Modification History:
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-B3) — extracted from login + mockup-direct AuthDev port
 *
 * Related:
 *   - backend/src/api/v1/auth.py:dev_login (POST /api/v1/auth/dev-login)
 *   - frontend/src/pages/auth/login/index.tsx (Sprint 57.23 US-B2 — removed embedded DevLoginSection; links to /auth/dev)
 *   - frontend/src/features/auth/store/authStore.ts (bootstrap)
 *   - frontend/src/features/auth/services/authService.ts (consumePostLoginRedirect)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.dev.* namespace)
 *   - reference/design-mockups/page-extras.jsx:109-152 (AuthDev canonical visual source)
 */

import { AlertTriangle, ArrowRight, ShieldAlert } from "lucide-react";
import { type ChangeEvent, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, CardContent } from "@/components/ui";
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
          <span className="font-mono">DEV_LOGIN=true</span>
        </span>
      }
    >
      {/* Sprint 57.23 mockup AuthDev L111-120: risk-high warning card */}
      <div
        data-severity="risk-high"
        className="relative rounded-lg border border-destructive/40 bg-destructive/5 p-4"
      >
        <div className="absolute left-0 top-0 bottom-0 w-0.5 rounded-l-lg bg-destructive" aria-hidden />
        <div className="mb-2 flex flex-row items-center gap-2 text-[13.5px] font-semibold text-destructive">
          <ShieldAlert size={13} aria-hidden />
          {t("dev.warningTitle")}
        </div>
        <div className="text-[12.5px] text-fg-muted">{t("dev.warningBody")}</div>
      </div>

      <Card>
        <CardContent className="p-6">
          <form className="flex flex-col gap-[14px]" onSubmit={submit}>
            {error ? (
              <div
                role="alert"
                className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
              >
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}

            <div className="flex flex-col gap-1">
              <label htmlFor="dev-identity" className="text-[12px] font-medium text-fg-muted">
                {t("dev.identityLabel")}
              </label>
              <select
                id="dev-identity"
                value={identityValue}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setIdentityValue(e.target.value)}
                className="h-9 rounded-md border border-border bg-background px-2 text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {IDENTITIES.map((i) => (
                  <option key={i.value} value={i.value}>
                    {i.email} · {i.role}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="dev-tenant" className="text-[12px] font-medium text-fg-muted">
                {t("dev.tenantLabel")}
              </label>
              <select
                id="dev-tenant"
                value={tenantValue}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setTenantValue(e.target.value)}
                className="h-9 rounded-md border border-border bg-background px-2 text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {TENANTS.map((tn) => (
                  <option key={tn.value} value={tn.value}>
                    {tn.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-[12px] font-medium text-fg-muted">{t("dev.roleLabel")}</span>
              <div className="flex flex-row gap-1.5">
                {ROLES.map((r) => (
                  <Badge
                    key={r}
                    variant={r === identity.role ? "default" : "secondary"}
                    aria-pressed={r === identity.role}
                  >
                    {r}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="my-0.5 h-px bg-border" aria-hidden />

            <Button type="submit" size="lg" disabled={busy} className="w-full text-[13.5px]">
              {busy ? t("dev.submitting") : t("dev.continueAs", { email: identity.email })}
              <ArrowRight size={16} className="ml-1" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
