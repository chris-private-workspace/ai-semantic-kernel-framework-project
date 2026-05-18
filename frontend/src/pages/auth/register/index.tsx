/**
 * File: frontend/src/pages/auth/register/index.tsx
 * Purpose: Self-serve tenant onboarding — 4-step wizard per Sprint 57.23 US-C2 (mockup AuthRegister direct port).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-C2 (NEW route)
 *
 * Description:
 *   Sprint 57.23 US-C2 NEW per `reference/design-mockups/page-auth-extras.jsx:31-188`:
 *     - 4-step wizard: Identity → Organization → Plan → Confirm
 *     - Stepper bar (4 circles + connectors; active/completed/future visual states)
 *     - Step 0 Identity: Work email + Full name + SAML hint
 *     - Step 1 Organization: Company name + Tenant slug (with .ipa.platform suffix) + Region + Size dropdowns
 *     - Step 2 Plan: 3 radio cards (Trial / Pro / Enterprise; Pro defaultChecked)
 *     - Step 3 Confirm: hitl-card-style summary + terms checkbox + email verification hint
 *     - Back/Continue navigation; Create workspace primary on step 3
 *
 *   Backend stub:
 *     - POST /api/v1/tenants/register expected to return 501 NotImplemented this sprint
 *     - AD-Auth-Register-Backend-IAM-Block-B-Phase58 carryover for real implementation
 *     - "Backend wire pending Phase 58+ IAM Block B" demo banner above stepper (AP-2 compliance)
 *
 * Created: 2026-05-18 (Sprint 57.23 US-C2)
 *
 * Modification History:
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-C2) — mockup-direct port of AuthRegister wizard
 *
 * Related:
 *   - backend/src/api/v1/auth.py (or NEW tenants.py) — POST /api/v1/tenants/register stub 501 (AD-IAM-Block-B-Phase58)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.23 mockup full-screen centered)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.register.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:31-188 (AuthRegister canonical visual source)
 */

import { AlertTriangle, ArrowRight, Check, ShieldCheck } from "lucide-react";
import { type ChangeEvent, type FormEvent, type ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, CardContent } from "@/components/ui";
import { fetchWithAuth } from "@/features/auth/services/authService";

type Step = 0 | 1 | 2 | 3;
type Plan = "trial" | "pro" | "enterprise";

interface PlanOption {
  id: Plan;
  name: string;
  price: string;
  period: string;
  desc: string;
}

const PLAN_OPTIONS: PlanOption[] = [
  {
    id: "trial",
    name: "Trial",
    price: "Free",
    period: "14 days",
    desc: "Full Pro features · 1 tenant · 10K loop turns · email support",
  },
  {
    id: "pro",
    name: "Pro",
    price: "$1,200",
    period: "/month",
    desc: "10 tenants · 200K loop turns · Teams + SAML SSO · governance UI",
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "Unlimited tenants · custom region · dedicated CSM · SOC2 + HIPAA",
  },
];

const REGIONS = [
  "ap-east-1 · Hong Kong (data residency)",
  "us-east-1 · N. Virginia",
  "eu-west-1 · Ireland (GDPR)",
  "ap-northeast-1 · Tokyo",
];

const SIZES = [
  "1-50 employees",
  "51-500 employees",
  "500-2000 employees",
  "2000+ enterprise",
];

interface FieldProps {
  label: string;
  help?: string;
  children: ReactNode;
  htmlFor?: string;
}

function Field({ label, help, children, htmlFor }: FieldProps): JSX.Element {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-[12px] font-medium text-fg-muted">
        {label}
      </label>
      {children}
      {help && <div className="text-[11px] text-fg-subtle">{help}</div>}
    </div>
  );
}

export default function RegisterPage(): JSX.Element {
  const { t } = useTranslation("auth");
  const [step, setStep] = useState<Step>(0);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [tenantSlug, setTenantSlug] = useState("");
  const [region, setRegion] = useState(REGIONS[0]);
  const [size, setSize] = useState(SIZES[2]);
  const [plan, setPlan] = useState<Plan>("pro");
  const [termsAccepted, setTermsAccepted] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const steps: Array<{ k: string; label: string }> = [
    { k: "identity", label: t("register.step1") },
    { k: "org", label: t("register.step2") },
    { k: "plan", label: t("register.step3") },
    { k: "verify", label: t("register.step4") },
  ];

  const next = (): void => setStep((s) => (Math.min(3, s + 1) as Step));
  const back = (): void => setStep((s) => (Math.max(0, s - 1) as Step));

  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    if (!termsAccepted) {
      setError(t("register.errorRequired"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetchWithAuth("/api/v1/tenants/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          full_name: fullName,
          company_name: companyName,
          tenant_slug: tenantSlug,
          region: region.split(" ·")[0],
          size,
          plan,
        }),
      });
      if (!res.ok) {
        // Sprint 57.23: backend stub 501; show demo-banner-style error per Q2 frontend-only decision
        setError(t("register.errorStubbed"));
        return;
      }
      // Phase 58+ IAM Block B: on success, redirect to /auth/callback for JWT mint
      window.location.href = "/auth/callback";
    } catch {
      setError(t("register.errorStubbed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      footer={
        <span>
          {t("register.alreadyHave")}{" "}
          <Link to="/auth/login" className="text-primary hover:underline">
            {t("register.signIn")}
          </Link>
        </span>
      }
    >
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col gap-4">
            {/* Header */}
            <div>
              <div className="mb-1 text-lg font-semibold">{t("register.title")}</div>
              <div className="text-[12.5px] text-fg-muted">{t("register.subtitle")}</div>
            </div>

            {/* AP-2 demo banner */}
            <div
              role="note"
              className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-[11px] text-warning"
            >
              {t("register.demoBanner")}
            </div>

            {/* Stepper bar (mockup L51-70) */}
            <div className="flex flex-row items-center gap-1">
              {steps.map((s, i) => (
                <div key={s.k} className="flex flex-row items-center gap-1">
                  <div className="flex flex-row items-center gap-1.5">
                    <span
                      className={
                        i <= step
                          ? "flex h-[18px] w-[18px] items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground"
                          : "flex h-[18px] w-[18px] items-center justify-center rounded-full border border-border bg-bg-3 text-[10px] font-semibold text-fg-subtle"
                      }
                    >
                      {i < step ? <Check size={9} /> : i + 1}
                    </span>
                    <span
                      className={
                        i === step
                          ? "text-[11px] text-foreground"
                          : "text-[11px] text-fg-subtle"
                      }
                    >
                      {s.label}
                    </span>
                  </div>
                  {i < steps.length - 1 && <div className="h-px flex-1 bg-border" aria-hidden />}
                </div>
              ))}
            </div>

            <div className="h-px bg-border" aria-hidden />

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

            <form onSubmit={submit} className="flex flex-col gap-3">
              {/* Step 0 — Identity (mockup L75-86) */}
              {step === 0 && (
                <div className="flex flex-col gap-3">
                  <Field label={t("register.workEmail")} htmlFor="reg-email">
                    <input
                      id="reg-email"
                      type="email"
                      value={email}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                      placeholder="founder@yourco.com"
                      className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    />
                  </Field>
                  <Field label={t("register.fullName")} htmlFor="reg-name">
                    <input
                      id="reg-name"
                      value={fullName}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
                      placeholder="Alex Chen"
                      className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    />
                  </Field>
                  <div className="flex flex-row items-center gap-1.5 text-[11px] text-fg-muted">
                    <ShieldCheck size={11} aria-hidden />
                    <span>{t("register.ssoHint")}</span>
                  </div>
                </div>
              )}

              {/* Step 1 — Organization (mockup L89-117) */}
              {step === 1 && (
                <div className="flex flex-col gap-3">
                  <Field label={t("register.companyName")} htmlFor="reg-company">
                    <input
                      id="reg-company"
                      value={companyName}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setCompanyName(e.target.value)}
                      placeholder="Acme Corp"
                      className="h-9 rounded-md border border-border bg-background px-3 text-[13.5px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    />
                  </Field>
                  <Field label={t("register.tenantSlug")} help={t("register.tenantSlugHelp")} htmlFor="reg-slug">
                    <div className="flex flex-row items-center gap-1">
                      <input
                        id="reg-slug"
                        value={tenantSlug}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setTenantSlug(e.target.value)}
                        placeholder="acme"
                        className="h-9 flex-1 rounded-md border border-border bg-background px-3 font-mono text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      />
                      <span className="self-center font-mono text-[12px] text-fg-subtle">.ipa.platform</span>
                    </div>
                  </Field>
                  <Field label={t("register.region")} htmlFor="reg-region">
                    <select
                      id="reg-region"
                      value={region}
                      onChange={(e: ChangeEvent<HTMLSelectElement>) => setRegion(e.target.value)}
                      className="h-9 rounded-md border border-border bg-background px-2 text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {REGIONS.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <Field label={t("register.size")} htmlFor="reg-size">
                    <select
                      id="reg-size"
                      value={size}
                      onChange={(e: ChangeEvent<HTMLSelectElement>) => setSize(e.target.value)}
                      className="h-9 rounded-md border border-border bg-background px-2 text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {SIZES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </Field>
                </div>
              )}

              {/* Step 2 — Plan (mockup L120-145) */}
              {step === 2 && (
                <div className="flex flex-col gap-2.5">
                  {PLAN_OPTIONS.map((p) => {
                    const active = plan === p.id;
                    return (
                      <label
                        key={p.id}
                        htmlFor={`reg-plan-${p.id}`}
                        aria-label={`${p.name} · ${p.price} ${p.period}`}
                        className={
                          active
                            ? "flex cursor-pointer flex-row gap-2.5 rounded-md border border-primary bg-primary/[0.08] p-3"
                            : "flex cursor-pointer flex-row gap-2.5 rounded-md border border-border bg-bg-1 p-3"
                        }
                      >
                        <input
                          id={`reg-plan-${p.id}`}
                          type="radio"
                          name="plan"
                          value={p.id}
                          checked={active}
                          onChange={() => setPlan(p.id)}
                          className="accent-primary"
                        />
                        <div className="flex grow flex-col gap-1">
                          <div className="flex flex-row items-baseline gap-2">
                            <span className="text-[13.5px] font-semibold">{p.name}</span>
                            <span className="font-mono text-[12px]">{p.price}</span>
                            <span className="font-mono text-[11px] text-fg-subtle">{p.period}</span>
                          </div>
                          <div className="text-[11.5px] leading-relaxed text-fg-muted">{p.desc}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Step 3 — Confirm (mockup L148-171) */}
              {step === 3 && (
                <div className="flex flex-col gap-3.5">
                  <div
                    data-severity="risk-low"
                    className="relative rounded-lg border border-success/40 bg-success/5 p-4"
                  >
                    <div className="absolute left-0 top-0 bottom-0 w-0.5 rounded-l-lg bg-success" aria-hidden />
                    <div className="mb-2 flex flex-row items-center gap-2 text-[13.5px] font-semibold text-success">
                      <Check size={13} aria-hidden />
                      {t("register.almostDone")}
                    </div>
                    <div className="flex flex-col gap-1.5 text-[12px] text-fg-muted">
                      <div className="flex flex-row justify-between">
                        <span>{t("register.workEmail")}</span>
                        <span className="font-mono">{email || "founder@yourco.com"}</span>
                      </div>
                      <div className="flex flex-row justify-between">
                        <span>{t("register.companyName")}</span>
                        <span>{companyName || "—"}</span>
                      </div>
                      <div className="flex flex-row justify-between">
                        <span>{t("register.tenantSlug")}</span>
                        <span className="font-mono">{tenantSlug || "acme"}.ipa.platform</span>
                      </div>
                      <div className="flex flex-row justify-between">
                        <span>{t("register.region")}</span>
                        <span className="font-mono">{region.split(" ·")[0]}</span>
                      </div>
                      <div className="flex flex-row items-center justify-between">
                        <span>Plan</span>
                        <Badge>
                          {PLAN_OPTIONS.find((p) => p.id === plan)?.name} ·{" "}
                          {PLAN_OPTIONS.find((p) => p.id === plan)?.price}
                          {PLAN_OPTIONS.find((p) => p.id === plan)?.period}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <label
                    htmlFor="reg-terms"
                    className="flex flex-row items-center gap-2 text-[12px] text-fg-muted"
                  >
                    <input
                      id="reg-terms"
                      type="checkbox"
                      checked={termsAccepted}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setTermsAccepted(e.target.checked)}
                      className="accent-primary"
                    />
                    <span>{t("register.terms")}</span>
                  </label>
                  <div className="flex flex-row items-start gap-1.5 text-[11px] text-fg-muted">
                    <AlertTriangle size={11} className="mt-0.5 shrink-0 text-warning" aria-hidden />
                    <span className="leading-relaxed">{t("register.verifyHint")}</span>
                  </div>
                </div>
              )}

              {/* Navigation (mockup L174-184) */}
              <div className="mt-1 flex flex-row gap-2">
                {step > 0 && (
                  <Button type="button" variant="ghost" onClick={back} disabled={busy}>
                    {t("register.back")}
                  </Button>
                )}
                <div className="grow" />
                {step < 3 ? (
                  <Button type="button" onClick={next} disabled={busy}>
                    {t("register.continue")}
                    <ArrowRight size={16} className="ml-1" />
                  </Button>
                ) : (
                  <Button type="submit" disabled={busy || !termsAccepted}>
                    {busy ? t("register.submitting") : t("register.create")}
                    <ArrowRight size={16} className="ml-1" />
                  </Button>
                )}
              </div>
            </form>
          </div>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
