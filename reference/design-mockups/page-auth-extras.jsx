/* global React, Icon, Button, Badge, Card, Field, RiskBadge, t */
const { useState: useAux, useEffect: useEffAux } = React;

// AuthShell re-export (same as page-extras.jsx but local for clarity)
const AuthShellX = ({ children, footer }) => (
  <div style={{
    minHeight: "100vh",
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: 40,
    background:
      "radial-gradient(ellipse 800px 600px at 50% -10%, oklch(from var(--primary) l c h / 0.12) 0%, transparent 60%), var(--bg)",
  }}>
    <div style={{ width: 420, display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="row" style={{ gap: 10, marginBottom: 4, justifyContent: "center" }}>
        <div className="brand-mark" style={{ width: 32, height: 32 }} />
        <div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>IPA Platform</div>
          <div style={{ fontSize: 10.5, color: "var(--fg-subtle)", fontFamily: "var(--font-mono)", letterSpacing: "0.04em", textTransform: "uppercase" }}>V2 · loop-first</div>
        </div>
      </div>
      {children}
      {footer && <div style={{ fontSize: 11, color: "var(--fg-subtle)", textAlign: "center", marginTop: 4 }}>{footer}</div>}
    </div>
  </div>
);

// ===================== /auth/register — tenant self-signup =====================
// Multi-step wizard: identity → org → plan → confirm.
// New companies self-onboard. Goes to tenant-onboarding wizard afterwards
// (which is admin-initiated for additional setup).
const AuthRegister = () => {
  const [step, setStep] = useAux(0);
  const steps = [
    { k: "identity", label: t("auth.register.step1") },
    { k: "org",      label: t("auth.register.step2") },
    { k: "plan",     label: t("auth.register.step3") },
    { k: "verify",   label: t("auth.register.step4") },
  ];
  const next = () => setStep(s => Math.min(steps.length - 1, s + 1));
  const back = () => setStep(s => Math.max(0, s - 1));
  return (
    <AuthShellX footer={<span>{t("auth.register.alreadyHave")} <a href="#auth-login" style={{ color: "var(--primary)" }}>{t("auth.register.signIn")}</a></span>}>
      <Card>
        <div className="col" style={{ gap: 16 }}>
          {/* header */}
          <div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>{t("auth.register.title")}</div>
            <div className="muted" style={{ fontSize: 12.5 }}>{t("auth.register.subtitle")}</div>
          </div>
          {/* stepper */}
          <div className="row" style={{ gap: 4, alignItems: "center" }}>
            {steps.map((s, i) => (
              <React.Fragment key={s.k}>
                <div className="row" style={{ gap: 6, alignItems: "center" }}>
                  <span style={{
                    width: 18, height: 18, borderRadius: "50%",
                    background: i <= step ? "var(--primary)" : "var(--bg-3)",
                    border: i <= step ? "none" : "1px solid var(--border)",
                    color: i <= step ? "white" : "var(--fg-subtle)",
                    fontSize: 10, fontWeight: 600,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    {i < step ? <Icon name="check" size={9} /> : i + 1}
                  </span>
                  <span style={{ fontSize: 11, color: i === step ? "var(--fg)" : "var(--fg-subtle)" }}>{s.label}</span>
                </div>
                {i < steps.length - 1 && <div style={{ flex: 1, height: 1, background: "var(--border)" }} />}
              </React.Fragment>
            ))}
          </div>
          <div className="hr" style={{ margin: "0" }} />

          {/* step body */}
          {step === 0 && (
            <div className="col" style={{ gap: 12 }}>
              <Field label={t("auth.register.workEmail")}>
                <input className="input" placeholder="founder@yourco.com" style={{ height: 36, fontSize: 13.5 }} />
              </Field>
              <Field label={t("auth.register.fullName")}>
                <input className="input" placeholder="Alex Chen" style={{ height: 36, fontSize: 13.5 }} />
              </Field>
              <div className="muted" style={{ fontSize: 11, lineHeight: 1.5 }}>
                <Icon name="shield" size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
                {t("auth.register.ssoHint")}
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="col" style={{ gap: 12 }}>
              <Field label={t("auth.register.companyName")}>
                <input className="input" placeholder="Acme Corp" style={{ height: 36, fontSize: 13.5 }} />
              </Field>
              <Field label={t("auth.register.tenantSlug")} help={t("auth.register.tenantSlugHelp")}>
                <div className="row" style={{ gap: 4 }}>
                  <input className="input mono" placeholder="acme" style={{ flex: 1, height: 36, fontSize: 13 }} />
                  <span className="mono subtle" style={{ alignSelf: "center", fontSize: 12 }}>.ipa.platform</span>
                </div>
              </Field>
              <Field label={t("auth.register.region")}>
                <select className="select" defaultValue="ap-east-1" style={{ height: 34, fontSize: 13 }}>
                  <option value="ap-east-1">ap-east-1 · Hong Kong (data residency)</option>
                  <option value="us-east-1">us-east-1 · N. Virginia</option>
                  <option value="eu-west-1">eu-west-1 · Ireland (GDPR)</option>
                  <option value="ap-northeast-1">ap-northeast-1 · Tokyo</option>
                </select>
              </Field>
              <Field label={t("auth.register.size")}>
                <select className="select" defaultValue="500-2000" style={{ height: 34, fontSize: 13 }}>
                  <option>1-50 employees</option>
                  <option>51-500 employees</option>
                  <option value="500-2000">500-2000 employees</option>
                  <option>2000+ enterprise</option>
                </select>
              </Field>
            </div>
          )}

          {step === 2 && (
            <div className="col" style={{ gap: 10 }}>
              {[
                { name: "Trial",       price: "Free",         period: "14 days", desc: "Full Pro features · 1 tenant · 10K loop turns · email support",       active: false },
                { name: "Pro",         price: "$1,200",       period: "/month",  desc: "10 tenants · 200K loop turns · Teams + SAML SSO · governance UI",     active: true  },
                { name: "Enterprise",  price: "Custom",       period: "",        desc: "Unlimited tenants · custom region · dedicated CSM · SOC2 + HIPAA",     active: false },
              ].map(p => (
                <label key={p.name} className="row" style={{
                  gap: 10, padding: 12,
                  background: p.active ? "oklch(from var(--primary) l c h / 0.08)" : "var(--bg-1)",
                  border: `1px solid ${p.active ? "var(--primary)" : "var(--border)"}`,
                  borderRadius: "var(--radius-sm)",
                  cursor: "pointer",
                }}>
                  <input type="radio" name="plan" defaultChecked={p.active} style={{ accentColor: "var(--primary)" }} />
                  <div className="col grow" style={{ gap: 4 }}>
                    <div className="row" style={{ gap: 8, alignItems: "baseline" }}>
                      <span style={{ fontWeight: 600, fontSize: 13.5 }}>{p.name}</span>
                      <span className="mono" style={{ fontSize: 12 }}>{p.price}</span>
                      <span className="mono subtle" style={{ fontSize: 11 }}>{p.period}</span>
                    </div>
                    <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.5 }}>{p.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {step === 3 && (
            <div className="col" style={{ gap: 14 }}>
              <div className="hitl-card" data-severity="risk-low" style={{ margin: 0 }}>
                <div className="hitl-card-bar" />
                <div className="hitl-head">
                  <span className="icon-ring"><Icon name="checkcheck" size={13} /></span>
                  {t("auth.register.almostDone")}
                </div>
                <div className="col" style={{ gap: 6, fontSize: 12, color: "var(--fg-muted)" }}>
                  <div className="spread"><span className="muted">{t("auth.register.workEmail")}</span><span className="mono">founder@yourco.com</span></div>
                  <div className="spread"><span className="muted">{t("auth.register.companyName")}</span><span>Acme Corp</span></div>
                  <div className="spread"><span className="muted">{t("auth.register.tenantSlug")}</span><span className="mono">acme.ipa.platform</span></div>
                  <div className="spread"><span className="muted">{t("auth.register.region")}</span><span className="mono">ap-east-1</span></div>
                  <div className="spread"><span className="muted">Plan</span><Badge tone="primary">Pro · $1,200/mo</Badge></div>
                </div>
              </div>
              <label className="row" style={{ gap: 8, fontSize: 12, color: "var(--fg-muted)" }}>
                <input type="checkbox" defaultChecked style={{ accentColor: "var(--primary)" }} />
                <span>{t("auth.register.terms")}</span>
              </label>
              <div className="muted" style={{ fontSize: 11, lineHeight: 1.5 }}>
                <Icon name="warn" size={11} style={{ verticalAlign: -1, marginRight: 4, color: "var(--warning)" }} />
                {t("auth.register.verifyHint")}
              </div>
            </div>
          )}

          {/* nav */}
          <div className="row" style={{ gap: 8, marginTop: 4 }}>
            {step > 0 && <Button variant="ghost" onClick={back}>{t("auth.back")}</Button>}
            <div className="grow" />
            {step < steps.length - 1 ? (
              <Button variant="primary" iconRight="arrow_right" onClick={next}>{t("auth.continue")}</Button>
            ) : (
              <Button variant="primary" icon="bolt" onClick={() => { location.hash = "auth-callback"; }}>{t("auth.register.create")}</Button>
            )}
          </div>
        </div>
      </Card>
    </AuthShellX>
  );
};

// ===================== /auth/invite — accept invitation from email link =====================
const AuthInvite = () => (
  <AuthShellX footer={<span>{t("auth.invite.foot")}</span>}>
    <Card>
      <div className="col" style={{ gap: 16 }}>
        <div className="col" style={{ gap: 10, alignItems: "center", textAlign: "center" }}>
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            background: "oklch(from var(--primary) l c h / 0.14)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--primary)",
          }}>
            <Icon name="user" size={26} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{t("auth.invite.title")}</div>
            <div className="muted" style={{ fontSize: 12.5 }}>{t("auth.invite.subtitle")}</div>
          </div>
        </div>

        <div className="col" style={{ gap: 0, background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
          <div className="spread" style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span className="muted">Tenant</span>
            <span className="mono">acme-prod · ap-east-1</span>
          </div>
          <div className="spread" style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span className="muted">Invited by</span>
            <span>dan@acme.com</span>
          </div>
          <div className="spread" style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span className="muted">Role</span>
            <Badge tone="primary">operator</Badge>
          </div>
          <div className="spread" style={{ padding: "10px 12px", fontSize: 12 }}>
            <span className="muted">Expires</span>
            <span className="mono subtle">in 6 days</span>
          </div>
        </div>

        <Field label={t("auth.invite.fullName")}>
          <input className="input" placeholder="Jamie Liu" style={{ height: 36, fontSize: 13.5 }} />
        </Field>
        <Field label={t("auth.invite.password")} help={t("auth.invite.passwordHint")}>
          <input type="password" className="input" placeholder="••••••••••••" style={{ height: 36, fontSize: 13.5 }} />
        </Field>

        <Button variant="primary" size="lg" iconRight="arrow_right" onClick={() => { location.hash = "auth-mfa"; }}>
          {t("auth.invite.accept")}
        </Button>
        <div className="row subtle" style={{ fontSize: 11, justifyContent: "center", gap: 6 }}>
          <Icon name="shield" size={11} />
          <span>{t("auth.invite.mfaHint")}</span>
        </div>
      </div>
    </Card>
  </AuthShellX>
);

// ===================== /auth/mfa — TOTP / WebAuthn challenge =====================
const AuthMFA = () => {
  const [code, setCode] = useAux(["", "", "", "", "", ""]);
  const [method, setMethod] = useAux("totp");
  const refs = code.map(() => React.useRef(null));
  const update = (i, v) => {
    if (!/^\d?$/.test(v)) return;
    const next = [...code];
    next[i] = v;
    setCode(next);
    if (v && i < 5) refs[i + 1].current?.focus();
  };
  const filled = code.every(v => v !== "");
  return (
    <AuthShellX footer={<span>{t("auth.mfa.foot")} <a href="#" style={{ color: "var(--primary)" }}>{t("auth.mfa.help")}</a></span>}>
      <Card>
        <div className="col" style={{ gap: 16 }}>
          <div className="col" style={{ gap: 8, alignItems: "center", textAlign: "center" }}>
            <div style={{
              width: 48, height: 48, borderRadius: "50%",
              background: "oklch(from var(--warning) l c h / 0.14)",
              display: "flex", alignItems: "center", justifyContent: "center", color: "var(--warning)",
            }}>
              <Icon name="keys" size={22} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{t("auth.mfa.title")}</div>
              <div className="muted" style={{ fontSize: 12.5 }}>
                {method === "totp" ? t("auth.mfa.totpSub") : t("auth.mfa.webauthnSub")}
              </div>
            </div>
          </div>

          <div className="row" style={{ gap: 6, padding: 4, background: "var(--bg-2)", borderRadius: "var(--radius-sm)" }}>
            <button
              onClick={() => setMethod("totp")}
              style={{
                flex: 1, padding: "6px 10px", borderRadius: 4,
                background: method === "totp" ? "var(--bg)" : "transparent",
                border: "none", cursor: "pointer", color: "var(--fg)",
                fontSize: 12, fontWeight: method === "totp" ? 500 : 400,
              }}>
              <Icon name="keys" size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
              Authenticator
            </button>
            <button
              onClick={() => setMethod("webauthn")}
              style={{
                flex: 1, padding: "6px 10px", borderRadius: 4,
                background: method === "webauthn" ? "var(--bg)" : "transparent",
                border: "none", cursor: "pointer", color: "var(--fg)",
                fontSize: 12, fontWeight: method === "webauthn" ? 500 : 400,
              }}>
              <Icon name="shield" size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
              Security Key
            </button>
          </div>

          {method === "totp" && (
            <div className="col" style={{ gap: 12 }}>
              <div className="row" style={{ gap: 6, justifyContent: "center" }}>
                {code.map((v, i) => (
                  <input
                    key={i}
                    ref={refs[i]}
                    value={v}
                    onChange={(e) => update(i, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Backspace" && !code[i] && i > 0) refs[i - 1].current?.focus();
                    }}
                    inputMode="numeric"
                    maxLength={1}
                    className="input mono"
                    style={{
                      width: 44, height: 52, textAlign: "center", fontSize: 22, fontWeight: 500,
                      background: v ? "oklch(from var(--primary) l c h / 0.10)" : "var(--bg-1)",
                      borderColor: v ? "var(--primary)" : "var(--border)",
                    }}
                  />
                ))}
              </div>
              <div className="row" style={{ justifyContent: "center", fontSize: 11, color: "var(--fg-subtle)", gap: 4 }}>
                <Icon name="clock" size={11} />
                <span className="mono">code refreshes in 23s</span>
              </div>
              <Button variant="primary" size="lg" disabled={!filled} iconRight="arrow_right" onClick={() => { location.hash = "auth-callback"; }}>
                {t("auth.mfa.verify")}
              </Button>
            </div>
          )}

          {method === "webauthn" && (
            <div className="col" style={{ gap: 12, alignItems: "center", padding: "16px 0" }}>
              <div style={{
                width: 88, height: 88, borderRadius: "50%",
                background: "conic-gradient(from 0deg, var(--primary), oklch(from var(--primary) l c h / 0.3))",
                animation: "spin 2.5s linear infinite",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <div style={{
                  width: 76, height: 76, borderRadius: "50%",
                  background: "var(--bg-1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "var(--primary)",
                }}>
                  <Icon name="shield" size={32} />
                </div>
              </div>
              <div className="muted" style={{ fontSize: 12, textAlign: "center", maxWidth: 280 }}>
                {t("auth.mfa.webauthnHint")}
              </div>
              <Button variant="ghost" size="sm" onClick={() => { location.hash = "auth-callback"; }}>{t("auth.mfa.simulate")}</Button>
            </div>
          )}

          <div className="hr" style={{ margin: "0" }} />
          <div className="row" style={{ justifyContent: "center", fontSize: 11.5 }}>
            <a href="#" style={{ color: "var(--fg-subtle)" }}>{t("auth.mfa.recoveryCode")}</a>
          </div>
        </div>
      </Card>
    </AuthShellX>
  );
};

// ===================== /auth/expired — session expired =====================
const AuthExpired = () => (
  <AuthShellX>
    <Card>
      <div className="col" style={{ gap: 16, alignItems: "center", textAlign: "center", padding: 8 }}>
        <div style={{
          width: 56, height: 56, borderRadius: "50%",
          background: "oklch(from var(--warning) l c h / 0.14)",
          display: "flex", alignItems: "center", justifyContent: "center", color: "var(--warning)",
        }}>
          <Icon name="clock" size={26} />
        </div>
        <div>
          <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 6 }}>{t("auth.expired.title")}</div>
          <div className="muted" style={{ fontSize: 13, maxWidth: 320, lineHeight: 1.5 }}>{t("auth.expired.subtitle")}</div>
        </div>

        <div className="col" style={{ gap: 0, alignSelf: "stretch", background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)" }}>
          <div className="spread" style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 11.5 }}>
            <span className="muted">Last activity</span>
            <span className="mono">14h 02m ago</span>
          </div>
          <div className="spread" style={{ padding: "8px 12px", borderBottom: "1px solid var(--border)", fontSize: 11.5 }}>
            <span className="muted">Session ID</span>
            <span className="mono subtle">sess_8a2f1c3</span>
          </div>
          <div className="spread" style={{ padding: "8px 12px", fontSize: 11.5 }}>
            <span className="muted">Reason</span>
            <Badge tone="warning">jwt_expired · 24h max</Badge>
          </div>
        </div>

        <div className="row" style={{ gap: 8, alignSelf: "stretch", marginTop: 4 }}>
          <Button variant="outline" onClick={() => { location.hash = "auth-login"; }}>{t("auth.expired.signInAgain")}</Button>
          <Button variant="primary" iconRight="arrow_right" onClick={() => { location.hash = "auth-callback"; }}>{t("auth.expired.resume")}</Button>
        </div>

        <div className="muted" style={{ fontSize: 11, marginTop: 2, maxWidth: 320, lineHeight: 1.5 }}>
          {t("auth.expired.dataHint")}
        </div>
      </div>
    </Card>
  </AuthShellX>
);

Object.assign(window, { AuthRegister, AuthInvite, AuthMFA, AuthExpired });
