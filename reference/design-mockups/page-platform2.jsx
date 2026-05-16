/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, SevDot, Stat, Spark, Spark */
const { useState: usePf2, useMemo: useMPf2 } = React;

// ===================================================================
// /jit-retrieval — Just-In-Time memory retrieval pipeline
// Backed by backend/src/agent_harness/context_mgmt/jit_retrieval.py
// ===================================================================
const JIT_PIPELINE = [
  { stage: "query.incoming",      desc: "Tool requests recent context for k8s.set_env",         ms: 0,    tone: "var(--primary)" },
  { stage: "embed.query",         desc: "voyage-3-large · 1024d",                               ms: 12,   tone: "var(--memory)" },
  { stage: "candidates.fetch",    desc: "pgvector cosine search · top_k=24",                    ms: 42,   tone: "var(--info)" },
  { stage: "filter.tenant_rls",   desc: "RLS scope: tenant=acme-prod · session+user",           ms: 4,    tone: "var(--warning)" },
  { stage: "rerank.cohere",       desc: "Cross-encoder re-rank · keep top_k=5",                 ms: 88,   tone: "var(--thinking)" },
  { stage: "inject.context",      desc: "5 chunks · 2,140 tokens · respect budget",             ms: 6,    tone: "var(--success)" },
];

const JIT_RECENT = [
  { id: "jit_4tk2p_1", query: "pgbouncer pool history INC-4012", kept: 5, k: 24, scores: [0.92, 0.88, 0.81, 0.74, 0.69], ms: 152, at: "now" },
  { id: "jit_4tk2p_2", query: "kubernetes deployment env var precedence", kept: 4, k: 18, scores: [0.94, 0.87, 0.71, 0.62], ms: 138, at: "1m ago" },
  { id: "jit_91kxu_3", query: "PCI scope ports definition", kept: 6, k: 32, scores: [0.96, 0.93, 0.88, 0.84, 0.79, 0.71], ms: 218, at: "8m ago" },
  { id: "jit_88vqc_4", query: "redis eviction policy noeviction vs allkeys-lru", kept: 3, k: 12, scores: [0.91, 0.74, 0.62], ms: 104, at: "12m ago" },
  { id: "jit_2afpw_5", query: "apac latency sla breach playbook", kept: 5, k: 20, scores: [0.88, 0.82, 0.76, 0.7, 0.65], ms: 168, at: "31m ago" },
];

const JITRetrieval = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">JIT Retrieval</div>
        <div className="page-sub">
          Range 3 · Just-in-time memory injection · pgvector + cohere re-rank
          <span className="route-pill">/jit-retrieval</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="play">Test query</Button>
        <Button variant="outline" size="sm" icon="download">Export traces</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Retrievals · 1h" value="1,820" delta="+82" deltaDir="up" />
      <Stat label="Avg latency" value="152" unit="ms" delta="-12ms" deltaDir="up" />
      <Stat label="Avg relevance" value="0.81" delta="+0.04" deltaDir="up" />
      <Stat label="Rerank hit-rate" value="84" unit="%" delta="+3pp" deltaDir="up" />
    </div>

    <div className="grid-main">
      <Card title="Retrieval pipeline" subtitle="6 stages · context-budget aware">
        <div style={{ position: "relative", paddingLeft: 22 }}>
          <div style={{ position: "absolute", left: 14, top: 8, bottom: 8, width: 2, background: "linear-gradient(180deg, var(--primary), var(--success))", borderRadius: 1 }} />
          {JIT_PIPELINE.map((p, i) => (
            <div key={p.stage} style={{ position: "relative", display: "grid", gridTemplateColumns: "1fr auto", gap: 8, alignItems: "center", padding: "8px 0" }}>
              <span style={{
                position: "absolute", left: -22, top: 14, width: 20, height: 20, borderRadius: 4,
                background: `oklch(from ${p.tone} l c h / 0.16)`,
                border: `1.5px solid ${p.tone}`,
                color: p.tone, fontSize: 10, fontWeight: 600, fontFamily: "var(--font-mono)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>{i + 1}</span>
              <div style={{ marginLeft: 8 }}>
                <div className="row" style={{ gap: 6 }}>
                  <span className="mono" style={{ fontSize: 12.5, fontWeight: 600, color: p.tone }}>{p.stage}</span>
                </div>
                <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>{p.desc}</div>
              </div>
              <span className="mono tnum subtle" style={{ fontSize: 11 }}>+{p.ms}ms</span>
            </div>
          ))}
        </div>
        <div className="thin-rule" />
        <div className="row subtle" style={{ fontSize: 11, gap: 6 }}>
          <Icon name="clock" size={11} />
          Total <span className="mono">152ms</span> · budget 300ms · 49% used
        </div>
      </Card>

      <Card title="Score distribution" subtitle="Top-K relevance · last 1h">
        <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 140, marginBottom: 8 }}>
          {[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0].map((threshold, i) => {
            const count = Math.round(60 * Math.exp(-Math.pow(threshold - 0.8, 2) * 30));
            return (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <span className="mono subtle" style={{ fontSize: 9 }}>{count}</span>
                <div style={{ width: "100%", height: count * 1.6, background: threshold >= 0.8 ? "var(--success)" : threshold >= 0.6 ? "var(--info)" : "var(--warning)", borderRadius: 2 }} />
                <span className="subtle mono" style={{ fontSize: 9 }}>{threshold.toFixed(2)}</span>
              </div>
            );
          })}
        </div>
        <div className="row subtle" style={{ fontSize: 11, gap: 8, justifyContent: "center" }}>
          <Badge tone="success" dot>≥ 0.80 kept</Badge>
          <Badge tone="info" dot>0.60–0.79 reranked</Badge>
          <Badge tone="warning" dot>&lt; 0.60 dropped</Badge>
        </div>
      </Card>
    </div>

    <div style={{ height: 14 }} />

    <Card title="Recent retrievals" subtitle="Most recent · score profile per query" bodyClass="flush">
      <table className="table">
        <thead><tr><th>Query</th><th style={{ textAlign: "right" }}>top_k</th><th style={{ textAlign: "right" }}>kept</th><th>Scores</th><th style={{ textAlign: "right" }}>Latency</th><th>When</th></tr></thead>
        <tbody>
          {JIT_RECENT.map(r => (
            <tr key={r.id}>
              <td style={{ fontSize: 12.5 }}>{r.query}</td>
              <td className="mono tnum subtle" style={{ textAlign: "right" }}>{r.k}</td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{r.kept}</td>
              <td>
                <div className="row" style={{ gap: 3 }}>
                  {r.scores.map((s, i) => (
                    <span key={i} className="mono tnum" style={{
                      fontSize: 10, padding: "1px 5px", borderRadius: 3,
                      background: s >= 0.85 ? "oklch(from var(--success) l c h / 0.16)" : s >= 0.7 ? "oklch(from var(--info) l c h / 0.16)" : "oklch(from var(--warning) l c h / 0.16)",
                      color: s >= 0.85 ? "var(--success)" : s >= 0.7 ? "var(--info)" : "var(--warning)",
                    }}>{s.toFixed(2)}</span>
                  ))}
                </div>
              </td>
              <td className="mono tnum subtle" style={{ textAlign: "right" }}>{r.ms}ms</td>
              <td className="subtle" style={{ fontSize: 11.5 }}>{r.at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

// ===================================================================
// /cache-manager — multi-kind cache: prompt / tool result / embedding / observation
// Backed by backend/src/agent_harness/context_mgmt/cache_manager.py
// ===================================================================
const CACHE_KINDS = [
  { id: "prompt",      name: "Prompt cache",      hits: 28420, misses: 12180, sizeMB: 142, evictions: 18, ttl: "1h", c: "var(--thinking)" },
  { id: "tool_result", name: "Tool result cache", hits: 14820, misses: 8420,  sizeMB: 84,  evictions: 4,  ttl: "5m", c: "var(--tool)" },
  { id: "embedding",   name: "Embedding cache",   hits: 9420,  misses: 1820,  sizeMB: 220, evictions: 0,  ttl: "30d", c: "var(--memory)" },
  { id: "observation", name: "Observation cache", hits: 7820,  misses: 4120,  sizeMB: 28,  evictions: 12, ttl: "10m", c: "var(--warning)" },
];

const CacheManager = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Cache Manager</div>
        <div className="page-sub">
          Range 3 · Multi-kind cache · LRU eviction · per-tenant scoped
          <span className="route-pill">/cache-manager</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="refresh">Refresh</Button>
        <Button variant="danger" size="sm" icon="x">Flush all</Button>
      </div>
    </div>

    <div className="grid-stats">
      {CACHE_KINDS.map(k => {
        const total = k.hits + k.misses;
        const rate = ((k.hits / total) * 100).toFixed(1);
        return (
          <div key={k.id} className="stat" style={{ borderLeft: `3px solid ${k.c}` }}>
            <div className="stat-label">
              <span className="row" style={{ gap: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: k.c }} />
                {k.name}
              </span>
              <span className="mono subtle" style={{ fontSize: 10 }}>{k.ttl}</span>
            </div>
            <div className="stat-value">{rate}<span className="unit">% hit</span></div>
            <div className="row subtle" style={{ fontSize: 10.5, gap: 6 }}>
              <span className="mono">{(k.hits/1000).toFixed(1)}K hits</span>
              <span>·</span>
              <span className="mono">{(k.misses/1000).toFixed(1)}K miss</span>
              <span>·</span>
              <span className="mono">{k.sizeMB}MB</span>
            </div>
          </div>
        );
      })}
    </div>

    <div className="grid-main">
      <Card title="Hit / miss ratio · 24h" subtitle="By cache kind">
        <div className="col" style={{ gap: 14 }}>
          {CACHE_KINDS.map(k => {
            const total = k.hits + k.misses;
            const hitPct = (k.hits / total) * 100;
            return (
              <div key={k.id}>
                <div className="spread" style={{ marginBottom: 4 }}>
                  <span className="row" style={{ gap: 6 }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: k.c }} />
                    <span className="mono" style={{ fontSize: 12 }}>{k.id}</span>
                  </span>
                  <span className="mono tnum subtle" style={{ fontSize: 11 }}>{hitPct.toFixed(1)}%</span>
                </div>
                <div style={{ height: 8, background: "var(--bg-3)", borderRadius: 2, overflow: "hidden", display: "flex" }}>
                  <span style={{ width: hitPct + "%", background: k.c }} />
                  <span style={{ width: (100 - hitPct) + "%", background: "var(--bg-3)" }} />
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Eviction policy" subtitle="Per-kind config">
        <div className="col" style={{ gap: 8, fontSize: 12 }}>
          {CACHE_KINDS.map(k => (
            <div key={k.id} className="spread">
              <span className="mono">{k.id}</span>
              <span className="row" style={{ gap: 6 }}>
                <Badge>LRU</Badge>
                <span className="mono subtle">TTL {k.ttl}</span>
                <span className="mono subtle">· evicted {k.evictions}</span>
              </span>
            </div>
          ))}
        </div>
        <div className="thin-rule" />
        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>
          All caches enforce <span className="mono">tenant_id</span> + <span className="mono">scope</span> as composite key. Cross-tenant cache leak is a Cat 8 critical tripwire.
        </div>
      </Card>
    </div>
  </div>
);

// ===================================================================
// /redaction — PII / secret patterns and recent redaction events
// Backed by backend/src/agent_harness/context_mgmt/observation_masker.py
// ===================================================================
const REDACT_PATTERNS = [
  { id: "email",      kind: "PII",    pattern: "[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}", count: 1820, severity: "medium", enabled: true },
  { id: "credit_card", kind: "PII",   pattern: "\\b\\d{4}[ -]?\\d{4}[ -]?\\d{4}[ -]?\\d{4}\\b", count: 18, severity: "critical", enabled: true },
  { id: "ssn",        kind: "PII",    pattern: "\\b\\d{3}-\\d{2}-\\d{4}\\b", count: 4, severity: "critical", enabled: true },
  { id: "ipv4",       kind: "PII",    pattern: "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b", count: 2840, severity: "low", enabled: true },
  { id: "aws_key",    kind: "secret", pattern: "AKIA[0-9A-Z]{16}", count: 2, severity: "critical", enabled: true },
  { id: "bearer",     kind: "secret", pattern: "(?i)bearer\\s+[a-z0-9._-]+", count: 184, severity: "high", enabled: true },
  { id: "github_pat", kind: "secret", pattern: "ghp_[A-Za-z0-9]{36}", count: 0, severity: "critical", enabled: true },
  { id: "private_key", kind: "secret", pattern: "-----BEGIN .+ PRIVATE KEY-----", count: 0, severity: "critical", enabled: true },
];

const REDACT_RECENT = [
  { at: "now", caller: "tools.zendesk", pattern: "email", original: "jamie@acme.com", redacted: "[EMAIL]", agent: "incident-responder" },
  { at: "1m ago", caller: "tools.metrics", pattern: "ipv4", original: "10.0.5.42", redacted: "[IPV4]", agent: "incident-responder" },
  { at: "2m ago", caller: "memory.write", pattern: "bearer", original: "Bearer eyJ...…wK4", redacted: "[BEARER_TOKEN]", agent: "compliance-auditor" },
  { at: "8m ago", caller: "tools.slack", pattern: "credit_card", original: "4532 1234 5678 9012", redacted: "[CC]", agent: "billing-helper" },
  { at: "12m ago", caller: "memory.read", pattern: "email", original: "support@globex.eu", redacted: "[EMAIL]", agent: "support-triage" },
];

const RedactionPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Observation Masker</div>
        <div className="page-sub">
          Range 3 · PII + secret redaction · runs on every tool input / output
          <span className="route-pill">/redaction</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="download">Export</Button>
        <Button variant="primary" size="sm" icon="plus">New pattern</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Redactions · 1h" value="4,870" delta="+220" deltaDir="up" />
      <Stat label="Patterns active" value={String(REDACT_PATTERNS.filter(p => p.enabled).length)} unit={`/${REDACT_PATTERNS.length}`} />
      <Stat label="Critical hits · 24h" value={String(REDACT_PATTERNS.filter(p => p.severity === "critical").reduce((s, p) => s + p.count, 0))} delta="+2" deltaDir="down" />
      <Stat label="False-positive rate" value="0.4" unit="%" delta="-0.1pp" deltaDir="up" />
    </div>

    <div className="grid-main">
      <Card title="Patterns" subtitle={`${REDACT_PATTERNS.length} regex + classifier rules`} bodyClass="flush">
        <table className="table">
          <thead><tr><th>Id</th><th>Kind</th><th>Pattern</th><th>Severity</th><th style={{ textAlign: "right" }}>Hits · 24h</th><th>Enabled</th></tr></thead>
          <tbody>
            {REDACT_PATTERNS.map(p => (
              <tr key={p.id}>
                <td className="mono" style={{ fontSize: 12 }}>{p.id}</td>
                <td><Badge tone={p.kind === "secret" ? "danger" : "warning"}>{p.kind}</Badge></td>
                <td className="mono subtle" style={{ fontSize: 11, maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.pattern}</td>
                <td><RiskBadge level={p.severity} /></td>
                <td className="mono tnum" style={{ textAlign: "right" }}>{p.count.toLocaleString()}</td>
                <td><Switch on={p.enabled} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Recent redactions" subtitle="Last 5 events · WORM logged">
        <div className="col" style={{ gap: 10 }}>
          {REDACT_RECENT.map((r, i) => (
            <div key={i} style={{ padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6 }}>
              <div className="row" style={{ gap: 6, marginBottom: 4 }}>
                <Badge tone="memory">{r.pattern}</Badge>
                <span className="mono subtle" style={{ fontSize: 10.5 }}>{r.caller}</span>
                <span className="subtle" style={{ marginLeft: "auto", fontSize: 10.5 }}>{r.at}</span>
              </div>
              <div className="mono" style={{ fontSize: 11, color: "var(--fg-muted)", textDecoration: "line-through" }}>{r.original}</div>
              <div className="mono" style={{ fontSize: 11, color: "var(--success)", marginTop: 2 }}>→ {r.redacted}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  </div>
);

// ===================================================================
// /tenant-onboarding — multi-step wizard
// Backed by backend/src/platform_layer/tenant/onboarding.py
// ===================================================================
const ONBOARDING_STEPS = [
  { id: "identity", title: "Tenant identity", desc: "Name, slug, region" },
  { id: "plan",     title: "Plan",            desc: "Pick capacity tier" },
  { id: "sso",      title: "SSO",             desc: "SAML / OIDC config" },
  { id: "admin",    title: "Admin user",      desc: "First member invite" },
  { id: "agent",    title: "First agent",     desc: "Pick a template" },
  { id: "review",   title: "Review & ship",   desc: "Confirm & provision" },
];

const TenantOnboardingPage = () => {
  const [step, setStep] = usePf2(2); // landed mid-wizard for demo
  const next = () => setStep(s => Math.min(s + 1, ONBOARDING_STEPS.length - 1));
  const back = () => setStep(s => Math.max(s - 1, 0));
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Onboard Tenant</div>
          <div className="page-sub">
            6-step wizard · provisioning audited end-to-end
            <span className="route-pill">/admin/tenant-onboarding</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" size="sm">Cancel</Button>
          <Button variant="outline" size="sm" icon="download">Save draft</Button>
        </div>
      </div>

      {/* Stepper */}
      <div style={{ position: "relative", marginBottom: 22 }}>
        <div style={{ position: "absolute", left: 14, right: 14, top: 12, height: 2, background: "var(--border)", borderRadius: 1 }} />
        <div style={{ position: "absolute", left: 14, top: 12, height: 2, background: "var(--primary)",
          width: `calc(${(step / (ONBOARDING_STEPS.length - 1)) * 100}% - 14px)`,
          borderRadius: 1, transition: "width 0.25s" }} />
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${ONBOARDING_STEPS.length}, 1fr)`, position: "relative" }}>
          {ONBOARDING_STEPS.map((s, i) => {
            const done = i < step, current = i === step;
            return (
              <div key={s.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, cursor: "pointer" }} onClick={() => setStep(i)}>
                <div style={{
                  width: 26, height: 26, borderRadius: "50%",
                  background: done ? "var(--primary)" : current ? "var(--bg-1)" : "var(--bg-2)",
                  border: `1.5px solid ${done || current ? "var(--primary)" : "var(--border)"}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: done ? "var(--primary-fg)" : current ? "var(--primary)" : "var(--fg-muted)",
                  fontWeight: 600, fontSize: 11.5, fontFamily: "var(--font-mono)",
                  zIndex: 1, transition: "all 0.15s",
                }}>
                  {done ? <Icon name="check" size={12} /> : i + 1}
                </div>
                <div style={{ fontSize: 11.5, fontWeight: current ? 600 : 400, color: current ? "var(--fg)" : "var(--fg-muted)", textAlign: "center" }}>{s.title}</div>
                <div className="subtle" style={{ fontSize: 10.5, textAlign: "center" }}>{s.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <Card title={ONBOARDING_STEPS[step].title} subtitle={ONBOARDING_STEPS[step].desc} bodyClass="">
          {step === 0 && (
            <div className="col" style={{ gap: 14 }}>
              <Field label="Tenant name" help="Human-readable; shown in topbar"><input className="input" defaultValue="Globex EU" /></Field>
              <Field label="Slug" help="URL-safe id; immutable"><input className="input mono" defaultValue="globex-eu" /></Field>
              <Field label="Region"><select className="select" defaultValue="eu-west-1"><option>ap-east-1</option><option>eu-west-1</option><option>us-east-1</option><option>ap-northeast-1</option></select></Field>
              <Field label="Compliance frameworks">
                <div className="kbar">
                  <Badge tone="primary">SOC2 Type II</Badge>
                  <Badge tone="primary">ISO27001</Badge>
                  <Badge>PCI-DSS</Badge>
                  <Badge>HIPAA</Badge>
                </div>
              </Field>
            </div>
          )}
          {step === 1 && (
            <div className="grid-3">
              {[
                { name: "Starter", price: "$0", limit: "1M tokens / mo · 5 seats", tone: "" },
                { name: "Pro",     price: "$499/mo", limit: "10M tokens / mo · 20 seats · SSO", tone: "primary", picked: true },
                { name: "Enterprise", price: "Custom", limit: "Unlimited · BYOK · 99.95% SLA", tone: "" },
              ].map(p => (
                <div key={p.name} className="card" style={{ borderColor: p.picked ? "var(--primary)" : "var(--border)", borderWidth: p.picked ? 2 : 1 }}>
                  <div className="card-body">
                    <div className="row" style={{ gap: 6 }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{p.name}</span>
                      {p.picked && <Badge tone="primary" style={{ marginLeft: "auto" }}>selected</Badge>}
                    </div>
                    <div style={{ fontSize: 22, fontWeight: 600, margin: "8px 0" }}>{p.price}</div>
                    <div className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>{p.limit}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {step === 2 && (
            <div className="col" style={{ gap: 14 }}>
              <Field label="SSO provider">
                <div className="row" style={{ gap: 6 }}>
                  {["SAML 2.0 · WorkOS", "OIDC · Okta", "OIDC · Azure AD"].map((p, i) => (
                    <Badge key={p} tone={i === 0 ? "primary" : ""}>{p}</Badge>
                  ))}
                </div>
              </Field>
              <Field label="Allowed email domains"><input className="input mono" defaultValue="globex.eu, globex.com" /></Field>
              <Field label="Required claim mapping"><pre style={{ margin: 0, padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--fg-muted)" }}>{`saml:NameID         → user.email
saml:eduPersonRole  → roles[]
saml:OrganizationId → tenant_id`}</pre></Field>
              <Field label="MFA"><div className="row"><Switch on={true} /><span className="muted">Required for all members</span></div></Field>
            </div>
          )}
          {step === 3 && (
            <div className="col" style={{ gap: 14 }}>
              <Field label="Admin email"><input className="input" defaultValue="admin@globex.eu" /></Field>
              <Field label="Send invite via"><select className="select" defaultValue="email"><option value="email">Email</option><option value="sso">SSO bootstrap</option></select></Field>
              <Field label="Initial role"><Badge tone="primary">tenant_admin</Badge></Field>
            </div>
          )}
          {step === 4 && (
            <div className="col" style={{ gap: 10 }}>
              {["incident-responder · SRE workflows", "compliance-auditor · audit + evidence", "patrol-runner · scheduled health checks", "Empty · start from scratch"].map((t, i) => (
                <div key={t} className="row" style={{ gap: 10, padding: 10, border: "1px solid var(--border)", borderRadius: "var(--radius)", cursor: "pointer", background: i === 0 ? "var(--primary-soft)" : "var(--bg-1)", borderColor: i === 0 ? "var(--primary)" : "var(--border)" }}>
                  <Icon name="chat" size={14} style={{ color: "var(--primary)" }} />
                  <span style={{ fontSize: 12.5 }}>{t}</span>
                  {i === 0 && <Badge tone="primary" style={{ marginLeft: "auto" }}>picked</Badge>}
                </div>
              ))}
            </div>
          )}
          {step === 5 && (
            <div className="col" style={{ gap: 8, fontSize: 12.5 }}>
              {[
                ["Tenant", "Globex EU · globex-eu · eu-west-1"],
                ["Plan", "Pro · $499/mo · 10M tokens"],
                ["SSO", "SAML 2.0 · WorkOS · 2 domains"],
                ["Admin", "admin@globex.eu · tenant_admin"],
                ["First agent", "incident-responder"],
                ["Provisioning ETA", "~ 90 seconds"],
              ].map(([k, v]) => (
                <div key={k} className="spread"><span className="muted">{k}</span><span className="mono">{v}</span></div>
              ))}
              <div className="thin-rule" />
              <div className="muted">By clicking Provision, you accept the platform <a style={{ color: "var(--primary)" }} href="#">terms</a> and authorize WORM-audited setup.</div>
            </div>
          )}
        </Card>

        <div className="row" style={{ marginTop: 14, gap: 8 }}>
          <Button variant="outline" onClick={back} disabled={step === 0}>Back</Button>
          <div className="grow" />
          <Button variant={step === ONBOARDING_STEPS.length - 1 ? "primary" : "primary"} icon={step === ONBOARDING_STEPS.length - 1 ? "bolt" : undefined} iconRight={step < ONBOARDING_STEPS.length - 1 ? "arrow_right" : undefined} onClick={next} disabled={step === ONBOARDING_STEPS.length - 1 && false}>
            {step === ONBOARDING_STEPS.length - 1 ? "Provision tenant" : "Continue"}
          </Button>
        </div>
      </div>
    </div>
  );
};

// ===================================================================
// /pricing — plan editor + per-resource pricing
// Backed by backend/src/platform_layer/billing/pricing.py
// ===================================================================
const PLANS = [
  { name: "Starter", price: 0, period: "free", tokens: "1M", seats: 5, agents: 3, sla: "best-effort", retention: "30d", c: "var(--info)" },
  { name: "Pro",     price: 499, period: "/ mo", tokens: "10M", seats: 20, agents: 25, sla: "99.5%", retention: "365d", c: "var(--primary)", popular: true },
  { name: "Enterprise", price: "Custom", period: "", tokens: "Unlimited", seats: "Unlimited", agents: "Unlimited", sla: "99.95%", retention: "7y", c: "var(--memory)" },
];

const PRICING_RESOURCES = [
  { resource: "Input tokens",        unit: "1M tokens",   starter: "included", pro: "included",  ent: "$0.40 / 1M overage" },
  { resource: "Output tokens",       unit: "1M tokens",   starter: "included", pro: "included",  ent: "$1.20 / 1M overage" },
  { resource: "Thinking tokens",     unit: "1M tokens",   starter: "—",         pro: "$2 / 1M",   ent: "$1.50 / 1M" },
  { resource: "Tool runs",           unit: "1K runs",     starter: "$0",        pro: "$0.50",     ent: "Custom" },
  { resource: "Subagent spawns",     unit: "1K spawns",   starter: "—",         pro: "$2",        ent: "Custom" },
  { resource: "Embeddings",          unit: "1M tokens",   starter: "$0.04",     pro: "$0.04",     ent: "$0.03" },
  { resource: "Memory storage",      unit: "GB · month",  starter: "$0.20",     pro: "$0.15",     ent: "$0.10" },
  { resource: "Audit retention",     unit: "GB · year",   starter: "—",         pro: "$0.80",     ent: "Included" },
  { resource: "Sandbox compute",     unit: "vCPU · hr",   starter: "—",         pro: "$0.06",     ent: "$0.04" },
];

const PricingPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Pricing Model</div>
        <div className="page-sub">
          Plan tiers + per-resource overage rates · WORM-audited on change
          <span className="route-pill">/admin/pricing</span>
          <Badge tone="warning">platform admin</Badge>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="git">Versions</Button>
        <Button variant="primary" size="sm" icon="bolt">Publish new pricing</Button>
      </div>
    </div>

    <div className="grid-3" style={{ marginBottom: 16 }}>
      {PLANS.map(p => (
        <div key={p.name} className="card" style={{ borderLeft: `3px solid ${p.c}`, position: "relative" }}>
          {p.popular && <Badge tone="primary" style={{ position: "absolute", right: 10, top: 10 }}>most picked</Badge>}
          <div className="card-body">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{p.name}</div>
            <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
              {typeof p.price === "number" ? `$${p.price}` : p.price}
              <span style={{ fontSize: 13, color: "var(--fg-muted)", fontWeight: 400, marginLeft: 4 }}>{p.period}</span>
            </div>
            <div className="hr" />
            <div className="col" style={{ gap: 6, fontSize: 12 }}>
              <div className="spread"><span className="muted">Tokens / mo</span><span className="mono">{p.tokens}</span></div>
              <div className="spread"><span className="muted">Seats</span><span className="mono">{p.seats}</span></div>
              <div className="spread"><span className="muted">Agents</span><span className="mono">{p.agents}</span></div>
              <div className="spread"><span className="muted">SLA</span><span className="mono">{p.sla}</span></div>
              <div className="spread"><span className="muted">Audit retention</span><span className="mono">{p.retention}</span></div>
            </div>
          </div>
        </div>
      ))}
    </div>

    <Card title="Per-resource rates" subtitle="Editable overage / usage-based rates" bodyClass="flush">
      <table className="table">
        <thead><tr><th>Resource</th><th>Unit</th><th>Starter</th><th>Pro</th><th>Enterprise</th></tr></thead>
        <tbody>
          {PRICING_RESOURCES.map(r => (
            <tr key={r.resource}>
              <td style={{ fontSize: 12.5 }}>{r.resource}</td>
              <td className="mono subtle" style={{ fontSize: 11.5 }}>{r.unit}</td>
              <td className="mono" style={{ fontSize: 11.5 }}>{r.starter}</td>
              <td className="mono" style={{ fontSize: 11.5, color: "var(--primary)" }}>{r.pro}</td>
              <td className="mono" style={{ fontSize: 11.5 }}>{r.ent}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

// ===================================================================
// Domain detail pages (shared component, 5 routes)
// Backed by backend/src/business_domain/{patrol,correlation,rootcause,audit_domain,incident}/*.py
// ===================================================================
const DOMAIN_DATA = {
  "domain-patrol": {
    id: "patrol", name: "Patrol", icon: "refresh", tone: "var(--tool)",
    desc: "Scheduled health checks across infra · cron-based · scope-aware",
    sprint: "Sprint 54 ship · GA",
    runs24: 412, active: 18, ok: 408, fail: 4, sla: "5s p95",
    agents: ["patrol-runner", "patrol-scheduler"],
    tools: ["patrol_schedule", "patrol_get_results", "patrol_acknowledge", "patrol_pause"],
    items: [
      { id: "PTR-9921", title: "APAC database health", schedule: "every 5m", lastRun: "2m ago", status: "ok" },
      { id: "PTR-9912", title: "EU edge cache integrity", schedule: "every 15m", lastRun: "8m ago", status: "ok" },
      { id: "PTR-9871", title: "Cross-region replication lag", schedule: "every 1m", lastRun: "now", status: "warn" },
      { id: "PTR-9810", title: "PCI scope ports", schedule: "daily 02:00", lastRun: "6h ago", status: "ok" },
    ],
  },
  "domain-correlation": {
    id: "correlate", name: "Event Correlation", icon: "branch", tone: "var(--thinking)",
    desc: "Cluster signals across services into incidents · streaming",
    sprint: "Sprint 55 ship · GA",
    runs24: 1820, active: 7, ok: 1808, fail: 12, sla: "12ms p95",
    agents: ["correlator-bot", "anomaly-detector"],
    tools: ["events_subscribe", "correlate_window", "incident_open", "anomaly_detect", "severity_classify"],
    items: [
      { id: "EVT-44012", title: "payment-gateway 5xx + pgbouncer saturation", schedule: "live", lastRun: "now", status: "active" },
      { id: "EVT-44009", title: "auth-svc latency cluster (3 nodes)", schedule: "live", lastRun: "12m ago", status: "active" },
      { id: "EVT-43988", title: "tenant_3kp9 token spike (anomaly)", schedule: "live", lastRun: "1h ago", status: "active" },
    ],
  },
  "domain-rca": {
    id: "rca", name: "Root Cause Analysis", icon: "thinking", tone: "var(--primary)",
    desc: "5-whys + timeline + verifiable evidence · agent-driven RCA",
    sprint: "Sprint 56 ship · GA",
    runs24: 28, active: 4, ok: 26, fail: 2, sla: "5m p95",
    agents: ["rca-bot", "evidence-collector"],
    tools: ["incident_get", "metrics.query", "log.tail", "log.grep", "evidence.attach"],
    items: [
      { id: "RCA-2026-05-16", title: "payment-gateway 5xx spike", schedule: "—", lastRun: "now", status: "active" },
      { id: "RCA-2026-05-12", title: "cache eviction storm", schedule: "—", lastRun: "4d ago", status: "done" },
      { id: "RCA-2026-05-08", title: "rollback failed on canary", schedule: "—", lastRun: "8d ago", status: "done" },
    ],
  },
  "domain-audit": {
    id: "audit", name: "Compliance Audit", icon: "audit", tone: "var(--memory)",
    desc: "WORM evidence · PCI/SOC2/ISO27001 frameworks · Merkle chain",
    sprint: "Sprint 53.5 ship · GA",
    runs24: 84, active: 3, ok: 84, fail: 0, sla: "n/a",
    agents: ["compliance-auditor", "evidence-exporter"],
    tools: ["audit_query_logs", "audit.export_chain", "evidence.bundle", "compliance_check", "redact_pii"],
    items: [
      { id: "AUD-Q2-2026", title: "Q2 SOC2 control evidence", schedule: "quarterly", lastRun: "running", status: "active" },
      { id: "AUD-PCI-2026-05", title: "PCI-DSS scope quarterly review", schedule: "quarterly", lastRun: "running", status: "active" },
      { id: "AUD-ANOM-3kp9", title: "Anomaly: tenant_3kp9 access pattern", schedule: "—", lastRun: "1h ago", status: "active" },
    ],
  },
  "domain-incident": {
    id: "incident", name: "Incident Management", icon: "warn", tone: "var(--danger)",
    desc: "P0/P1 lifecycle · on-call paging · postmortem authoring",
    sprint: "Sprint 56 ship · GA",
    runs24: 6, active: 2, ok: 4, fail: 2, sla: "200ms p95",
    agents: ["incident-responder", "change-reviewer", "postmortem-writer"],
    tools: ["incident_get", "k8s.set_env", "k8s.rollback", "page_oncall", "change.create", "cdn.purge"],
    items: [
      { id: "INC-4087", title: "payment-gateway SLO breach", schedule: "—", lastRun: "P1 · 4m ago", status: "active" },
      { id: "INC-4086", title: "edge-cdn cache poisoning", schedule: "—", lastRun: "P2 · 21m ago", status: "active" },
      { id: "INC-4082", title: "auth-svc nightly latency", schedule: "—", lastRun: "resolved", status: "done" },
    ],
  },
};

const DomainDetailPage = () => {
  // Read route from hash so this single component serves all 5 domains
  const route = window.location.hash.replace("#", "") || "domain-patrol";
  const d = DOMAIN_DATA[route] || DOMAIN_DATA["domain-patrol"];
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="row" style={{ gap: 10, marginBottom: 6 }}>
            <div style={{ width: 32, height: 32, borderRadius: 7, background: `oklch(from ${d.tone} l c h / 0.2)`, color: d.tone, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name={d.icon} size={16} />
            </div>
            <div>
              <div className="row" style={{ gap: 8 }}>
                <span style={{ fontSize: 20, fontWeight: 600 }}>{d.name}</span>
                <Badge tone="success" dot>{d.sprint}</Badge>
              </div>
              <div className="page-sub" style={{ marginTop: 2 }}>
                {d.desc}
                <span className="route-pill">/incidents/{d.id}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="ghost" size="sm" icon="chevron_right" onClick={() => { location.hash = "incidents"; }}>All domains</Button>
          <Button variant="primary" size="sm" icon="plus">New item</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Active items" value={d.active} />
        <Stat label="Runs · 24h" value={d.runs24.toLocaleString()} delta="+12%" deltaDir="up" />
        <Stat label="Success" value={`${((d.ok / (d.ok + d.fail)) * 100).toFixed(1)}%`} delta={d.fail > 0 ? "-0.4pp" : "0"} deltaDir={d.fail > 0 ? "down" : "up"} />
        <Stat label="SLA" value={d.sla} />
      </div>

      <div className="grid-main">
        <Card title="Active items" bodyClass="flush" actions={<Button variant="ghost" size="sm" icon="filter">Filter</Button>}>
          <table className="table">
            <thead><tr><th>ID</th><th>Title</th><th>Schedule</th><th>Last run</th><th>Status</th></tr></thead>
            <tbody>
              {d.items.map(it => (
                <tr key={it.id}>
                  <td className="mono" style={{ fontSize: 11.5, color: "var(--fg-muted)" }}>{it.id}</td>
                  <td style={{ fontSize: 12.5 }}>{it.title}</td>
                  <td className="mono subtle" style={{ fontSize: 11.5 }}>{it.schedule}</td>
                  <td className="subtle" style={{ fontSize: 11.5 }}>{it.lastRun}</td>
                  <td>
                    <Badge tone={it.status === "ok" ? "success" : it.status === "warn" ? "warning" : it.status === "done" ? "" : "danger"} dot>
                      {it.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <div className="col" style={{ gap: 14 }}>
          <Card title="Agents in scope" subtitle={`${d.agents.length} agent${d.agents.length === 1 ? "" : "s"} assigned`}>
            <div className="col" style={{ gap: 8 }}>
              {d.agents.map(name => (
                <div key={name} className="row" style={{ gap: 10, padding: "6px 0" }}>
                  <div style={{ width: 26, height: 26, borderRadius: 5, background: `oklch(from ${d.tone} l c h / 0.2)`, color: d.tone, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon name={d.icon} size={12} />
                  </div>
                  <div className="grow">
                    <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{name}</div>
                    <div className="subtle mono" style={{ fontSize: 10.5 }}>claude-haiku-4-5</div>
                  </div>
                  <Badge tone="success" dot>live</Badge>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Tools in scope" subtitle={`${d.tools.length} ToolSpec`}>
            <div className="kbar">
              {d.tools.map(t => <Badge key={t} tone="tool" pill>{t}</Badge>)}
            </div>
            <div className="hr" />
            <Button variant="outline" size="sm" icon="tool" onClick={() => { location.hash = "tools"; }}>Open registry</Button>
          </Card>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { JITRetrieval, CacheManager, RedactionPage, TenantOnboardingPage, PricingPage, DomainDetailPage });
