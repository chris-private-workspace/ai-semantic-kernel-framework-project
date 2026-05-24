/**
 * File: frontend/src/pages/auth/register/index.tsx
 * Purpose: Self-serve tenant onboarding — verbatim re-point per mockup AuthRegister (Sprint 57.35 US-C2).
 * Category: Frontend / pages / auth
 * Scope: Phase 57 / Sprint 57.23 US-C2 (initial NEW route) → Sprint 57.35 US-C2 (Phase-2 verbatim-CSS re-point)
 *
 * Description:
 *   Sprint 57.35 US-C2 verbatim re-point per `reference/design-mockups/page-auth-extras.jsx:31-188`:
 *     - Drop shadcn Card/CardContent/Button/Badge + lucide-react Check/AlertTriangle/ShieldCheck/ArrowRight
 *     - Drop local <Field> in favour of mockup-ui Field (.field/.field-label)
 *     - Use mockup-ui Card + Button + Badge + Icon (check/warn/shield/bolt)
 *     - Verbatim .col + .row + .muted + .subtle + .mono + .input + .select + .hr + .spread classes
 *     - Step circles use inline-style literals per mockup L55-65 (var(--primary) fill / var(--bg-3) muted)
 *     - Step 2 Plan radio cards use inline-style literals per mockup L126-132
 *     - Step 3 Confirm uses .hitl-card[data-severity="risk-low"] + .hitl-card-bar + .hitl-head verbatim
 *     - Continue / Create buttons use mockup-ui iconRight="arrow_right" / icon="bolt"
 *
 *   Backend behavior preserved (Sprint 57.23 US-C2):
 *     - POST /api/v1/tenants/register expected 501 NotImplemented this sprint
 *     - AD-Auth-Register-Backend-IAM-Block-B-Phase58 carryover
 *     - Demo banner above stepper (AP-2 compliance) — re-cast as .hitl-card[risk-medium] visual style
 *
 * Created: 2026-05-18 (Sprint 57.23 US-C2)
 * Last Modified: 2026-05-24
 *
 * Modification History:
 *   - 2026-05-24: Sprint 57.35 US-C2 — verbatim re-point per page-auth-extras.jsx:31-188 (closes Sprint 57.23 vintage HSL-translation drift)
 *   - 2026-05-18: Initial creation (Sprint 57.23 US-C2) — mockup-direct port of AuthRegister wizard
 *
 * Related:
 *   - backend/src/api/v1/auth.py (or NEW tenants.py) — POST /api/v1/tenants/register stub 501 (AD-IAM-Block-B-Phase58)
 *   - frontend/src/components/AuthShell.tsx (Sprint 57.35 verbatim re-point)
 *   - frontend/src/components/mockup-ui.tsx (Card/Button/Badge/Field/Icon)
 *   - frontend/src/i18n/locales/{en,zh-TW}/auth.json (auth.register.* namespace)
 *   - reference/design-mockups/page-auth-extras.jsx:31-188 (AuthRegister canonical visual source)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (stepper circles + plan radio cards + container) copied byte-for-byte from mockup page-auth-extras.jsx:31-188 (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md verbatim-CSS rule) */

import { type ChangeEvent, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { AuthShell } from "@/components/AuthShell";
import { Badge, Button, Card, Field, Icon } from "@/components/mockup-ui";
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
        setError(t("register.errorStubbed"));
        return;
      }
      window.location.href = "/auth/callback";
    } catch {
      setError(t("register.errorStubbed"));
    } finally {
      setBusy(false);
    }
  };

  const selectedPlan = PLAN_OPTIONS.find((p) => p.id === plan);

  return (
    <AuthShell
      footer={
        <span>
          {t("register.alreadyHave")}{" "}
          <Link to="/auth/login" style={{ color: "var(--primary)", textDecoration: "none" }}>
            {t("register.signIn")}
          </Link>
        </span>
      }
    >
      <Card>
        <div className="col" style={{ gap: 16 }}>
          {/* header */}
          <div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              {t("register.title")}
            </div>
            <div className="muted" style={{ fontSize: 12.5 }}>
              {t("register.subtitle")}
            </div>
          </div>

          {/* AP-2 demo banner — verbatim per .hitl-card[data-severity="risk-medium"] pattern */}
          <div className="hitl-card" data-severity="risk-medium" style={{ margin: 0 }} role="note">
            <div className="hitl-card-bar" />
            <div className="hitl-head">
              <span className="icon-ring">
                <Icon name="warn" size={13} />
              </span>
              {t("register.demoBanner")}
            </div>
          </div>

          {/* stepper — verbatim mockup L51-70 */}
          <div className="row" style={{ gap: 4, alignItems: "center" }}>
            {steps.map((s, i) => (
              <div
                key={s.k}
                className="row"
                style={{ gap: 4, alignItems: "center", flex: i < steps.length - 1 ? 1 : "initial" }}
              >
                <div className="row" style={{ gap: 6, alignItems: "center" }}>
                  <span
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: "50%",
                      background: i <= step ? "var(--primary)" : "var(--bg-3)",
                      border: i <= step ? "none" : "1px solid var(--border)",
                      color: i <= step ? "white" : "var(--fg-subtle)",
                      fontSize: 10,
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {i < step ? <Icon name="check" size={9} /> : i + 1}
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      color: i === step ? "var(--fg)" : "var(--fg-subtle)",
                    }}
                  >
                    {s.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div
                    style={{ flex: 1, height: 1, background: "var(--border)" }}
                    aria-hidden
                  />
                )}
              </div>
            ))}
          </div>

          <div className="hr" style={{ margin: 0 }} />

          {/* Error surface */}
          {error && (
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
          )}

          <form onSubmit={submit} className="col" style={{ gap: 12 }}>
            {/* Step 0 — Identity (mockup L75-86) */}
            {step === 0 && (
              <div className="col" style={{ gap: 12 }}>
                <Field label={t("register.workEmail")}>
                  <input
                    id="reg-email"
                    type="email"
                    className="input"
                    value={email}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                    placeholder="founder@yourco.com"
                    style={{ height: 36, fontSize: 13.5 }}
                  />
                </Field>
                <Field label={t("register.fullName")}>
                  <input
                    id="reg-name"
                    className="input"
                    value={fullName}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
                    placeholder="Alex Chen"
                    style={{ height: 36, fontSize: 13.5 }}
                  />
                </Field>
                <div className="muted" style={{ fontSize: 11, lineHeight: 1.5 }}>
                  <Icon
                    name="shield"
                    size={11}
                    style={{ verticalAlign: -1, marginRight: 4 }}
                  />
                  {t("register.ssoHint")}
                </div>
              </div>
            )}

            {/* Step 1 — Organization (mockup L89-117) */}
            {step === 1 && (
              <div className="col" style={{ gap: 12 }}>
                <Field label={t("register.companyName")}>
                  <input
                    id="reg-company"
                    className="input"
                    value={companyName}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setCompanyName(e.target.value)}
                    placeholder="Acme Corp"
                    style={{ height: 36, fontSize: 13.5 }}
                  />
                </Field>
                <Field label={t("register.tenantSlug")} help={t("register.tenantSlugHelp")}>
                  <div className="row" style={{ gap: 4 }}>
                    <input
                      id="reg-slug"
                      className="input mono"
                      value={tenantSlug}
                      onChange={(e: ChangeEvent<HTMLInputElement>) =>
                        setTenantSlug(e.target.value)
                      }
                      placeholder="acme"
                      style={{ flex: 1, height: 36, fontSize: 13 }}
                    />
                    <span className="mono subtle" style={{ alignSelf: "center", fontSize: 12 }}>
                      .ipa.platform
                    </span>
                  </div>
                </Field>
                <Field label={t("register.region")}>
                  <select
                    id="reg-region"
                    className="select"
                    value={region}
                    onChange={(e: ChangeEvent<HTMLSelectElement>) => setRegion(e.target.value)}
                    style={{ height: 34, fontSize: 13 }}
                  >
                    {REGIONS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label={t("register.size")}>
                  <select
                    id="reg-size"
                    className="select"
                    value={size}
                    onChange={(e: ChangeEvent<HTMLSelectElement>) => setSize(e.target.value)}
                    style={{ height: 34, fontSize: 13 }}
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
              <div className="col" style={{ gap: 10 }}>
                {PLAN_OPTIONS.map((p) => {
                  const active = plan === p.id;
                  return (
                    <label
                      key={p.id}
                      htmlFor={`reg-plan-${p.id}`}
                      aria-label={`${p.name} · ${p.price} ${p.period}`}
                      className="row"
                      style={{
                        gap: 10,
                        padding: 12,
                        background: active
                          ? "oklch(from var(--primary) l c h / 0.08)"
                          : "var(--bg-1)",
                        border: `1px solid ${active ? "var(--primary)" : "var(--border)"}`,
                        borderRadius: "var(--radius-sm)",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        id={`reg-plan-${p.id}`}
                        type="radio"
                        name="plan"
                        value={p.id}
                        checked={active}
                        onChange={() => setPlan(p.id)}
                        style={{ accentColor: "var(--primary)" }}
                      />
                      <div className="col grow" style={{ gap: 4 }}>
                        <div className="row" style={{ gap: 8, alignItems: "baseline" }}>
                          <span style={{ fontWeight: 600, fontSize: 13.5 }}>{p.name}</span>
                          <span className="mono" style={{ fontSize: 12 }}>
                            {p.price}
                          </span>
                          <span className="mono subtle" style={{ fontSize: 11 }}>
                            {p.period}
                          </span>
                        </div>
                        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.5 }}>
                          {p.desc}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            )}

            {/* Step 3 — Confirm (mockup L148-171) */}
            {step === 3 && (
              <div className="col" style={{ gap: 14 }}>
                <div
                  className="hitl-card"
                  data-severity="risk-low"
                  style={{ margin: 0 }}
                >
                  <div className="hitl-card-bar" />
                  <div className="hitl-head">
                    <span className="icon-ring">
                      <Icon name="checkcheck" size={13} />
                    </span>
                    {t("register.almostDone")}
                  </div>
                  <div
                    className="col"
                    style={{ gap: 6, fontSize: 12, color: "var(--fg-muted)" }}
                  >
                    <div className="spread">
                      <span className="muted">{t("register.workEmail")}</span>
                      <span className="mono">{email || "founder@yourco.com"}</span>
                    </div>
                    <div className="spread">
                      <span className="muted">{t("register.companyName")}</span>
                      <span>{companyName || "—"}</span>
                    </div>
                    <div className="spread">
                      <span className="muted">{t("register.tenantSlug")}</span>
                      <span className="mono">{tenantSlug || "acme"}.ipa.platform</span>
                    </div>
                    <div className="spread">
                      <span className="muted">{t("register.region")}</span>
                      <span className="mono">{region.split(" ·")[0]}</span>
                    </div>
                    <div className="spread">
                      <span className="muted">Plan</span>
                      <Badge tone="primary">
                        {selectedPlan?.name} · {selectedPlan?.price}
                        {selectedPlan?.period}
                      </Badge>
                    </div>
                  </div>
                </div>
                <label
                  htmlFor="reg-terms"
                  className="row"
                  style={{ gap: 8, fontSize: 12, color: "var(--fg-muted)" }}
                >
                  <input
                    id="reg-terms"
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setTermsAccepted(e.target.checked)
                    }
                    style={{ accentColor: "var(--primary)" }}
                  />
                  <span>{t("register.terms")}</span>
                </label>
                <div className="muted" style={{ fontSize: 11, lineHeight: 1.5 }}>
                  <Icon
                    name="warn"
                    size={11}
                    style={{ verticalAlign: -1, marginRight: 4, color: "var(--warning)" }}
                  />
                  {t("register.verifyHint")}
                </div>
              </div>
            )}

            {/* nav — verbatim mockup L174-184 */}
            <div className="row" style={{ gap: 8, marginTop: 4 }}>
              {step > 0 && (
                <Button type="button" variant="ghost" onClick={back} disabled={busy}>
                  {t("register.back")}
                </Button>
              )}
              <div className="grow" />
              {step < 3 ? (
                <Button
                  type="button"
                  variant="primary"
                  iconRight="arrow_right"
                  onClick={next}
                  disabled={busy}
                >
                  {t("register.continue")}
                </Button>
              ) : (
                <Button
                  type="submit"
                  variant="primary"
                  icon="bolt"
                  disabled={busy || !termsAccepted}
                >
                  {busy ? t("register.submitting") : t("register.create")}
                </Button>
              )}
            </div>
          </form>
        </div>
      </Card>
    </AuthShell>
  );
}
