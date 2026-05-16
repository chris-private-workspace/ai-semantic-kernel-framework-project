/* global React, ReactDOM, Sidebar, Topbar, ROUTES,
   ChatV2, LoopDebug, Approvals, MemoryPage, AuditPage,
   SlaPage, CostPage, TenantsPage, TenantSettings,
   AuthLogin, AuthCallback, AuthDev, AuthRegister, AuthInvite, AuthMFA, AuthExpired,
   SubagentTree, DevUI, Incidents,
   ToolsAdmin, SSEInspector, VerificationPage, FeatureFlagsPage,
   StateInspector, Compaction, Workflows, ErrorPolicyPage, RBACPage,
   JITRetrieval, CacheManager, RedactionPage, TenantOnboardingPage, PricingPage, DomainDetailPage,
   Orchestrator, SubagentsRegistry, ModelsPage, OverviewPage,
   CommandPalette, NotificationsPanel, UserMenu,
   TweaksPanel, useTweaks, TweakSection, TweakRadio, TweakColor, TweakSelect, TweakSlider
*/
const { useState: useAp, useEffect: useEap } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "variant": "linear",
  "theme": "dark",
  "density": "default",
  "primary_h": 250,
  "locale": "en"
}/*EDITMODE-END*/;

const AUTH_ROUTES = new Set(["auth-login", "auth-callback", "auth-dev", "auth-register", "auth-invite", "auth-mfa", "auth-expired"]);

// Map route id → component. Renamed to align with repo's routes.config.ts
const ROUTE_VIEWS = {
  "overview":        OverviewPage,
  "chat-v2":         ChatV2,
  "cost-dashboard":  CostPage,
  "sla-dashboard":   SlaPage,
  "admin-tenants":   TenantsPage,
  "tenant-settings": TenantSettings,
  "audit-log":       AuditPage,
  "feature-flags":   FeatureFlagsPage,
  "governance":      Approvals,
  "verification":    VerificationPage,
  "loop-debug":      LoopDebug,
  "memory":          MemoryPage,
  // Platform-layer proposals
  "state-inspector": StateInspector,
  "compaction":      Compaction,
  "error-policy":    ErrorPolicyPage,
  "rbac":            RBACPage,
  // Context + tenant + pricing proposals
  "jit-retrieval":   JITRetrieval,
  "cache-manager":   CacheManager,
  "redaction":       RedactionPage,
  "tenant-onboarding": TenantOnboardingPage,
  "pricing":         PricingPage,
  // Domain detail (5 routes share one component)
  "domain-patrol":      DomainDetailPage,
  "domain-correlation": DomainDetailPage,
  "domain-rca":         DomainDetailPage,
  "domain-audit":       DomainDetailPage,
  "domain-incident":    DomainDetailPage,
  // Other proposals
  "incidents":       Incidents,
  "tools":           ToolsAdmin,
  "sse":             SSEInspector,
  "subagent-tree":   SubagentTree,
  "devui":           DevUI,
  // Agent CRUD
  "orchestrator":    Orchestrator,
  "subagents":       SubagentsRegistry,
  "models":          ModelsPage,
};

function App() {
  const [route, setRoute] = useAp(() => location.hash.replace("#", "") || "overview");

  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  useEap(() => {
    const onHash = () => setRoute(location.hash.replace("#", "") || "overview");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const goto = (r) => { location.hash = r; setRoute(r); };

  useEap(() => {
    document.documentElement.dataset.theme = t.theme;
    document.documentElement.dataset.variant = t.variant;
    document.documentElement.dataset.density = t.density;
    document.documentElement.dataset.locale = t.locale;
    document.documentElement.lang = t.locale === "zh" ? "zh-TW" : "en";
    document.documentElement.style.setProperty("--primary-h", String(t.primary_h));
  }, [t.theme, t.variant, t.density, t.primary_h, t.locale]);

  const openTweaks = () => window.postMessage({ type: "__activate_edit_mode" }, "*");

  const fullbleed = route === "chat-v2" || route === "loop-debug";

  // Auth pages render without app shell
  // Overlay state for topbar icons
  const [cmdkOpen, setCmdkOpen] = useAp(false);
  const [notifsOpen, setNotifsOpen] = useAp(false);
  const [userMenuOpen, setUserMenuOpen] = useAp(false);
  const notifsAnchorRef = React.useRef(null);
  const avatarAnchorRef = React.useRef(null);

  // ⌘K global shortcut
  useEap(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdkOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (AUTH_ROUTES.has(route)) {
    return (
      <>
        {route === "auth-login" && <AuthLogin />}
        {route === "auth-callback" && <AuthCallback />}
        {route === "auth-dev" && <AuthDev />}
        {route === "auth-register" && <AuthRegister />}
        {route === "auth-invite" && <AuthInvite />}
        {route === "auth-mfa" && <AuthMFA />}
        {route === "auth-expired" && <AuthExpired />}
        {renderTweaks(t, setTweak, route, goto)}
      </>
    );
  }

  const View = ROUTE_VIEWS[route];

  return (
    <div className="app" key={t.locale}>
      <Sidebar route={route} onNav={goto} />
      <div className="main">
        <Topbar
          route={route}
          onNav={goto}
          onToggleTweaks={openTweaks}
          onOpenCmdK={() => setCmdkOpen(true)}
          onOpenNotifs={() => { setNotifsOpen(v => !v); setUserMenuOpen(false); }}
          onOpenUserMenu={() => { setUserMenuOpen(v => !v); setNotifsOpen(false); }}
          onToggleLocale={() => setTweak({ locale: t.locale === "en" ? "zh" : "en" })}
          onToggleTheme={() => setTweak({ theme: t.theme === "dark" ? "light" : "dark" })}
          locale={t.locale}
          theme={t.theme}
          notifsAnchorRef={notifsAnchorRef}
          avatarAnchorRef={avatarAnchorRef}
        />
        <div className={`content ${fullbleed ? "fullbleed" : ""}`} data-screen-label={route}>
          {View ? <View onNav={goto} /> : <NotFound route={route} onNav={goto} />}
        </div>
      </div>

      <CommandPalette open={cmdkOpen} onClose={() => setCmdkOpen(false)} onNav={goto} />
      <NotificationsPanel open={notifsOpen} onClose={() => setNotifsOpen(false)} onNav={goto} anchorRef={notifsAnchorRef} />
      <UserMenu open={userMenuOpen} onClose={() => setUserMenuOpen(false)} onNav={goto} anchorRef={avatarAnchorRef} />

      {renderTweaks(t, setTweak, route, goto)}
    </div>
  );
}

function NotFound({ route, onNav }) {
  return (
    <div className="empty" style={{ padding: 60 }}>
      <div style={{ fontSize: 20, fontWeight: 600 }}>404 — {route}</div>
      <div className="muted">This route isn't wired up yet.</div>
      <button className="btn outline" onClick={() => onNav("chat-v2")}>Back to Chat</button>
    </div>
  );
}

function renderTweaks(t, setTweak, route, goto) {
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="Visual variant">
        <TweakSelect
          value={t.variant}
          onChange={(v) => setTweak({ variant: v })}
          options={[
            { value: "linear",  label: "Linear · Vercel dark-dense" },
            { value: "strict",  label: "Strict · shadcn defaults" },
            { value: "refined", label: "Refined · motion + texture" },
            { value: "shadcn",  label: "shadcn-slate · repo tokens" },
          ]}
        />
        <div style={{ fontSize: 10.5, color: "#888", marginTop: 6, lineHeight: 1.55 }}>
          <b>shadcn-slate</b> uses the exact HSL tokens from your repo's <code>src/index.css</code> (slate base · 0.5rem radius).
        </div>
      </TweakSection>

      <TweakSection label="Theme">
        <TweakRadio
          value={t.theme}
          onChange={(v) => setTweak({ theme: v })}
          options={[{ value: "dark", label: "Dark" }, { value: "light", label: "Light" }]}
        />
      </TweakSection>

      <TweakSection label="Locale">
        <TweakRadio
          value={t.locale}
          onChange={(v) => setTweak({ locale: v })}
          options={[{ value: "en", label: "English" }, { value: "zh", label: "繁體中文" }]}
        />
      </TweakSection>

      <TweakSection label="Density">
        <TweakSelect
          value={t.density}
          onChange={(v) => setTweak({ density: v })}
          options={[
            { value: "compact", label: "Compact" },
            { value: "default", label: "Default" },
            { value: "comfortable", label: "Comfortable" },
          ]}
        />
      </TweakSection>

      <TweakSection label="Primary hue">
        <TweakSlider
          label="hue"
          value={t.primary_h}
          min={180}
          max={310}
          step={5}
          onChange={(v) => setTweak({ primary_h: v })}
        />
        <div style={{ fontSize: 10.5, color: "#888", marginTop: 4 }}>
          Brand primary (cool-only). The <b>shadcn-slate</b> variant keeps slate as background but this hue still drives semantic accent.
        </div>
      </TweakSection>

      <TweakSection label="Quick nav · registry routes">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 10.5, fontFamily: "ui-monospace, monospace" }}>
          {ROUTES.filter(r => r.category !== "proposals" && r.active).map(r => (
            <button key={r.id}
              onClick={() => goto(r.id)}
              style={{
                cursor: "pointer", textAlign: "left", padding: "4px 7px",
                background: route === r.id ? "rgba(99,102,241,0.18)" : "rgba(255,255,255,0.04)",
                border: route === r.id ? "1px solid #6366f1" : "1px solid rgba(255,255,255,0.08)",
                color: route === r.id ? "#a5b4fc" : "#bbb",
                borderRadius: 4,
              }}>
              {r.path}
            </button>
          ))}
        </div>
      </TweakSection>

      <TweakSection label="Quick nav · proposals">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 10.5, fontFamily: "ui-monospace, monospace" }}>
          {ROUTES.filter(r => r.category === "proposals").map(r => (
            <button key={r.id}
              onClick={() => goto(r.id)}
              style={{
                cursor: "pointer", textAlign: "left", padding: "4px 7px",
                background: route === r.id ? "rgba(139,92,246,0.22)" : "rgba(139,92,246,0.06)",
                border: route === r.id ? "1px solid #8b5cf6" : "1px solid rgba(139,92,246,0.18)",
                color: route === r.id ? "#c4b5fd" : "#a78bfa",
                borderRadius: 4,
              }}>
              {r.path}
            </button>
          ))}
        </div>
      </TweakSection>

      <TweakSection label="Auth flows">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 10.5, fontFamily: "ui-monospace, monospace" }}>
          {[
            ["auth-login", "/auth/login"],
            ["auth-callback", "/auth/callback"],
            ["auth-dev", "/auth/dev-login"],
            ["auth-register", "/auth/register"],
            ["auth-invite", "/auth/invite"],
            ["auth-mfa", "/auth/mfa"],
            ["auth-expired", "/auth/expired"],
          ].map(([r, l]) => (
            <button key={r}
              onClick={() => goto(r)}
              style={{
                cursor: "pointer", textAlign: "left", padding: "4px 7px",
                background: route === r ? "rgba(99,102,241,0.18)" : "rgba(255,255,255,0.04)",
                border: route === r ? "1px solid #6366f1" : "1px solid rgba(255,255,255,0.08)",
                color: route === r ? "#a5b4fc" : "#bbb",
                borderRadius: 4,
              }}>
              {l}
            </button>
          ))}
        </div>
      </TweakSection>
    </TweaksPanel>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
