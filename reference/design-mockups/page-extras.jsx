/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, Stat, Spark, SevDot */
const { useState: useEx, useEffect: useEffEx } = React;

// ===================== /auth — login, callback, dev-login =====================
const AuthShell = ({ children, footer }) => (
  <div style={{
    minHeight: "100vh",
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: 40,
    background:
      "radial-gradient(ellipse 800px 600px at 50% -10%, oklch(from var(--primary) l c h / 0.12) 0%, transparent 60%), var(--bg)",
  }}>
    <div style={{ width: 400, display: "flex", flexDirection: "column", gap: 18 }}>
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

const AuthLogin = () => (
  <AuthShell footer={<span>By signing in you agree to the <a style={{ color: "var(--primary)" }} href="#">Terms</a> · <a style={{ color: "var(--primary)" }} href="#">Privacy</a></span>}>
    <Card>
      <div className="col" style={{ gap: 16 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Sign in</div>
          <div className="muted" style={{ fontSize: 12.5 }}>Continue with SSO or your work email.</div>
        </div>
        <Button variant="outline" size="lg" icon="shield">Continue with SAML SSO</Button>
        <Button variant="outline" size="lg" icon="globe">Continue with Microsoft</Button>
        <Button variant="outline" size="lg" icon="git">Continue with Google Workspace</Button>
        <div className="row" style={{ gap: 8, margin: "4px 0" }}>
          <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          <span className="subtle" style={{ fontSize: 11 }}>or</span>
          <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
        </div>
        <Field label="Work email">
          <input className="input" placeholder="you@acme.com" defaultValue="jamie@acme.com" style={{ height: 36, fontSize: 13.5 }} />
        </Field>
        <Button variant="primary" size="lg" iconRight="arrow_right">Continue</Button>
        <div className="row subtle" style={{ fontSize: 11, justifyContent: "center", gap: 6 }}>
          <Icon name="shield" size={11} />
          <span>SAML 2.0 / OIDC · MFA required by tenant policy</span>
        </div>
      </div>
    </Card>
    <a href="#auth-dev" style={{ fontSize: 11, color: "var(--fg-subtle)", textAlign: "center" }}>
      Trouble signing in? Use <span className="mono" style={{ color: "var(--warning)" }}>dev-login</span> (non-prod only)
    </a>
  </AuthShell>
);

const AuthCallback = () => {
  const [step, setStep] = useEx(0);
  useEffEx(() => {
    const t1 = setTimeout(() => setStep(1), 800);
    const t2 = setTimeout(() => setStep(2), 1800);
    const t3 = setTimeout(() => setStep(3), 2800);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);
  const steps = [
    { k: "Verifying SAML assertion", done: step > 0 },
    { k: "Resolving tenant + RLS context", done: step > 1 },
    { k: "Loading feature flags + memory scopes", done: step > 2 },
  ];
  return (
    <AuthShell>
      <Card>
        <div className="col" style={{ gap: 18, alignItems: "center", textAlign: "center", padding: 8 }}>
          <div style={{
            width: 48, height: 48, borderRadius: "50%",
            background: "conic-gradient(from 0deg, var(--primary), transparent 70%)",
            animation: "spin 1.2s linear infinite",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--bg-1)" }} />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600 }}>Completing sign-in…</div>
            <div className="muted mono" style={{ fontSize: 11.5, marginTop: 4 }}>callback=acme.workos.com</div>
          </div>
          <div className="col" style={{ gap: 8, alignSelf: "stretch", marginTop: 8 }}>
            {steps.map((s, i) => (
              <div key={i} className="row" style={{ gap: 8, fontSize: 12 }}>
                <span style={{
                  width: 14, height: 14, borderRadius: "50%",
                  background: s.done ? "var(--success)" : "var(--bg-3)",
                  border: s.done ? "none" : "1px solid var(--border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {s.done && <Icon name="check" size={9} style={{ color: "white" }} />}
                </span>
                <span style={{ color: s.done ? "var(--fg)" : "var(--fg-muted)" }}>{s.k}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </AuthShell>
  );
};

const AuthDev = () => (
  <AuthShell footer={<span>Disable <span className="mono">DEV_LOGIN=true</span> in production environments.</span>}>
    <div className="hitl-card" data-severity="risk-high" style={{ margin: 0 }}>
      <div className="hitl-card-bar" />
      <div className="hitl-head">
        <span className="icon-ring"><Icon name="warn" size={13} /></span>
        Dev login — non-production only
      </div>
      <div style={{ fontSize: 12.5, color: "var(--fg-muted)" }}>
        Skips SAML / MFA. All actions are still audited under your assumed identity, including any HITL approvals.
      </div>
    </div>
    <Card>
      <div className="col" style={{ gap: 14 }}>
        <Field label="Assume identity">
          <select className="select" defaultValue="u_jamie" style={{ height: 34, fontSize: 13 }}>
            <option value="u_jamie">jamie@acme.com · operator</option>
            <option value="u_priya">priya@acme.com · compliance</option>
            <option value="u_dan">dan@acme.com · admin</option>
            <option value="u_platform">platform@beacon.dev · platform</option>
          </select>
        </Field>
        <Field label="Tenant">
          <select className="select" defaultValue="tenant_01h9a2" style={{ height: 34, fontSize: 13 }}>
            <option value="tenant_01h9a2">acme-prod (Pro · ap-east-1)</option>
            <option value="tenant_01h7zz">globex-eu (Pro · eu-west-1)</option>
            <option value="tenant_01h6kp">initech-jp (Enterprise · ap-northeast-1)</option>
          </select>
        </Field>
        <Field label="Role">
          <div className="row" style={{ gap: 6 }}>
            {["operator", "compliance", "admin", "platform"].map(r => (
              <Badge key={r} tone={r === "operator" ? "primary" : ""}>{r}</Badge>
            ))}
          </div>
        </Field>
        <div className="hr" style={{ margin: "2px 0" }} />
        <Button variant="primary" size="lg" iconRight="arrow_right" onClick={() => { location.hash = "chat-v2"; }}>
          Continue as jamie@acme.com
        </Button>
      </div>
    </Card>
  </AuthShell>
);

// ===================== /subagent-tree =====================
const SUBAGENT_ROOT = {
  id: "incident-responder", name: "incident-responder", role: "root", model: "claude-haiku-4-5",
  status: "hitl-paused", turns: 4, tokens: 18420, started: "10:42:18", duration: "4m 14s",
  children: [
    {
      id: "fork-t1", name: "fork · concurrent (t1)", role: "fork", status: "done", turns: 0, tokens: 0,
      children: [
        { id: "sa-log", name: "log-scanner", model: "claude-haiku-4-5", role: "subagent", status: "done", turns: 3, tokens: 8120, duration: "2.20s", tools: ["log.tail", "log.grep"],
          children: [
            { id: "sa-log-tool", name: "log.tail", role: "tool", status: "done", turns: 1, tokens: 320, duration: "1.1s" },
          ]},
        { id: "sa-dep", name: "dep-checker", model: "claude-haiku-4-5", role: "subagent", status: "done", turns: 2, tokens: 6280, duration: "1.86s", tools: ["health.probe", "k8s.get_deployment"],
          children: [
            { id: "sa-dep-1", name: "health.probe", role: "tool", status: "done", turns: 1, tokens: 120, duration: "0.4s" },
            { id: "sa-dep-2", name: "k8s.get_deployment", role: "tool", status: "done", turns: 1, tokens: 280, duration: "0.6s" },
          ]},
        { id: "sa-met", name: "metrics-pull", model: "claude-haiku-4-5", role: "subagent", status: "done", turns: 1, tokens: 2240, duration: "0.32s", tools: ["metrics.query"],
          children: [
            { id: "sa-met-1", name: "metrics.query", role: "tool", status: "done", turns: 1, tokens: 180, duration: "0.21s" },
          ]},
      ]},
  ],
};

const SubagentTree = () => {
  const [selected, setSelected] = useEx("sa-log");
  const node = findNode(SUBAGENT_ROOT, selected) || SUBAGENT_ROOT;
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Subagent Tree</div>
          <div className="page-sub">
            Session <span className="mono">sess_4tk2p</span> · depth 2 · concurrency 3 / 5
            <span className="route-pill">/subagent-tree</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="download">Export tree</Button>
          <Button variant="outline" size="sm" icon="loop" onClick={() => location.hash = "loop-debug"}>Loop view</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Tree depth" value="2" />
        <Stat label="Subagents spawned" value="3" delta="+0" deltaDir="up" />
        <Stat label="Total tokens" value="18,420" />
        <Stat label="Wall time saved (fork)" value="2.18s" delta="-58%" deltaDir="up" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
        <Card title="Topology" subtitle="Click a node to drill in · 4 modes: Fork / AsTool / Teammate / Mailbox" bodyClass="dense">
          <SubagentGraph root={SUBAGENT_ROOT} selected={selected} onSelect={setSelected} />
        </Card>

        <Card title={<span className="row" style={{ gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: roleColor(node.role) }} />
            {node.name}
          </span>}
          subtitle={`${node.role} · ${node.status}`}
          bodyClass="dense"
        >
          <div className="col" style={{ gap: 7, fontSize: 12 }}>
            <KvRowEx k="id" v={node.id} mono />
            <KvRowEx k="role" v={<Badge tone={node.role === "subagent" ? "primary" : node.role === "tool" ? "tool" : node.role === "fork" ? "thinking" : ""}>{node.role}</Badge>} />
            {node.model && <KvRowEx k="model" v={node.model} mono />}
            <KvRowEx k="status" v={<Badge tone={node.status === "done" ? "success" : node.status === "running" ? "info" : "warning"} dot>{node.status}</Badge>} />
            <KvRowEx k="turns" v={node.turns} mono />
            {node.tokens != null && <KvRowEx k="tokens" v={node.tokens.toLocaleString()} mono />}
            {node.duration && <KvRowEx k="duration" v={node.duration} mono />}
            {node.tools && <KvRowEx k="tools" v={<span className="mono">{node.tools.length}</span>} />}
          </div>
          {node.tools && (
            <>
              <div className="hr" />
              <div className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Tools used</div>
              <div className="col" style={{ gap: 4 }}>
                {node.tools.map(t => (
                  <div key={t} className="mono" style={{ fontSize: 11.5, color: "var(--tool)" }}>· {t}</div>
                ))}
              </div>
            </>
          )}
          <div className="hr" />
          <div className="col" style={{ gap: 6 }}>
            <Button variant="outline" size="sm" icon="eye">Open transcript</Button>
            <Button variant="outline" size="sm" icon="loop">Show in loop view</Button>
            <Button variant="outline" size="sm" icon="audit">Audit entries</Button>
          </div>
        </Card>
      </div>

      <div style={{ height: 14 }} />

      <Card title="Subagent modes" subtitle="V2 supports 4 invocation patterns">
        <div className="grid-stats" style={{ marginBottom: 0 }}>
          {[
            { name: "Fork", sub: "Concurrent fan-out", icon: "fork", c: "var(--thinking)", desc: "Parent spawns N children in parallel · gathers when all return · 58% wall-time savings on this session." },
            { name: "AsTool", sub: "Nested call", icon: "tool", c: "var(--tool)", desc: "Subagent invoked like a regular tool · synchronous · isolated memory scope." },
            { name: "Teammate", sub: "Handoff", icon: "branch", c: "var(--info)", desc: "Conversation transferred to specialist agent · shared history · single active speaker." },
            { name: "Mailbox", sub: "Async messaging", icon: "send", c: "var(--memory)", desc: "Agents post messages to each other's queue · long-running coordination · no shared loop." },
          ].map(m => (
            <div key={m.name} style={{ padding: 12, background: "var(--bg-1)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", borderLeft: `3px solid ${m.c}` }}>
              <div className="row" style={{ gap: 8, marginBottom: 6 }}>
                <Icon name={m.icon} size={14} style={{ color: m.c }} />
                <span style={{ fontWeight: 600, fontSize: 13 }}>{m.name}</span>
                <span className="subtle" style={{ fontSize: 11 }}>{m.sub}</span>
              </div>
              <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.5 }}>{m.desc}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

const roleColor = (r) =>
  r === "root" ? "var(--primary)" :
  r === "subagent" ? "var(--info)" :
  r === "fork" ? "var(--thinking)" :
  r === "tool" ? "var(--tool)" : "var(--fg-muted)";

const findNode = (n, id) => {
  if (n.id === id) return n;
  for (const c of n.children || []) { const f = findNode(c, id); if (f) return f; }
  return null;
};

const SubagentGraph = ({ root, selected, onSelect }) => {
  // Custom radial / column layout: column per depth.
  // Compute positions
  const COL_W = 200, ROW_H = 62, X0 = 20, Y0 = 20;
  const layout = [];
  const place = (node, depth, ySlot) => {
    layout.push({ node, x: X0 + depth * COL_W, y: Y0 + ySlot.value * ROW_H, depth });
    ySlot.value += 1;
    if (node.children) {
      const start = ySlot.value;
      node.children.forEach(c => place(c, depth + 1, ySlot));
      // Recenter parent y to midpoint of children if applicable
      const end = ySlot.value;
      if (end > start) {
        const ix = layout.findIndex(l => l.node === node);
        layout[ix].y = Y0 + ((start + end - 1) / 2) * ROW_H;
      }
    }
  };
  place(root, 0, { value: 0 });
  const maxX = Math.max(...layout.map(l => l.x)) + 180;
  const maxY = Math.max(...layout.map(l => l.y)) + 50;
  // Edges
  const edges = [];
  layout.forEach(({ node }) => {
    if (node.children) {
      node.children.forEach(c => {
        const p = layout.find(l => l.node === node);
        const cl = layout.find(l => l.node === c);
        edges.push({ x1: p.x + 180, y1: p.y + 18, x2: cl.x, y2: cl.y + 18 });
      });
    }
  });
  return (
    <div style={{ position: "relative", width: maxX, minHeight: maxY, padding: 8 }}>
      <svg style={{ position: "absolute", inset: 0, pointerEvents: "none", width: maxX, height: maxY }}>
        {edges.map((e, i) => {
          const cx = (e.x1 + e.x2) / 2;
          return <path key={i} d={`M${e.x1},${e.y1} C${cx},${e.y1} ${cx},${e.y2} ${e.x2},${e.y2}`} fill="none" stroke="var(--border-strong)" strokeWidth="1.5" />;
        })}
      </svg>
      {layout.map(({ node, x, y }) => (
        <div key={node.id}
          onClick={() => onSelect(node.id)}
          style={{
            position: "absolute", left: x, top: y, width: 180,
            background: selected === node.id ? "oklch(from var(--primary) l c h / 0.10)" : "var(--bg-1)",
            border: selected === node.id ? "1.5px solid var(--primary)" : "1px solid var(--border)",
            borderLeft: `3px solid ${roleColor(node.role)}`,
            borderRadius: "var(--radius)",
            padding: "7px 10px",
            cursor: "pointer",
            transition: "background 0.12s",
            fontFamily: "var(--font-mono)", fontSize: 11.5,
          }}>
          <div className="row" style={{ gap: 5, marginBottom: 2 }}>
            <Icon name={node.role === "tool" ? "tool" : node.role === "fork" ? "fork" : node.role === "root" ? "chat" : "branch"} size={11} style={{ color: roleColor(node.role) }} />
            <span style={{ fontWeight: 600, color: roleColor(node.role), overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{node.name}</span>
          </div>
          <div className="row" style={{ gap: 5, fontSize: 10 }}>
            <span style={{ color: "var(--fg-muted)" }}>{node.role}</span>
            {node.turns > 0 && <><span className="subtle">·</span><span style={{ color: "var(--fg-muted)" }}>{node.turns}t</span></>}
            {node.tokens > 0 && <><span className="subtle">·</span><span style={{ color: "var(--fg-muted)" }}>{(node.tokens / 1000).toFixed(1)}k</span></>}
            <span style={{ flex: 1 }} />
            <span style={{
              width: 6, height: 6, borderRadius: "50%",
              background: node.status === "done" ? "var(--success)" : node.status === "running" ? "var(--info)" : "var(--warning)"
            }} />
          </div>
        </div>
      ))}
    </div>
  );
};

const KvRowEx = ({ k, v, mono }) => (
  <div className="spread" style={{ fontSize: 12 }}>
    <span className="muted" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{k}</span>
    <span className={mono ? "mono tnum" : ""}>{v}</span>
  </div>
);

// ===================== /devui — 11+1 maturity + Cat 12 metric =====================
const CATEGORIES = [
  { id: 1, name: "Loop (TAO/ReAct)", scope: "core", maturity: "Hardened", coverage: 94, owner: "platform", spans: 1.2, alerts: 0, lastSprint: "57.12" },
  { id: 2, name: "Tool Layer", scope: "core", maturity: "GA", coverage: 88, owner: "platform", spans: 0.8, alerts: 1, lastSprint: "57.10" },
  { id: 3, name: "Memory (dual-axis)", scope: "core", maturity: "GA", coverage: 91, owner: "platform", spans: 0.4, alerts: 0, lastSprint: "57.11" },
  { id: 4, name: "Streaming (SSE LoopEvent)", scope: "core", maturity: "Hardened", coverage: 96, owner: "platform", spans: 0.2, alerts: 0, lastSprint: "55.8" },
  { id: 5, name: "Identity & RBAC", scope: "core", maturity: "GA", coverage: 82, owner: "security", spans: 0.1, alerts: 0, lastSprint: "57.13" },
  { id: 6, name: "Provider Adapter (LLM-neutral)", scope: "core", maturity: "GA", coverage: 86, owner: "platform", spans: 0.6, alerts: 0, lastSprint: "57.05" },
  { id: 7, name: "Verification", scope: "core", maturity: "Beta", coverage: 71, owner: "platform", spans: 0.3, alerts: 2, lastSprint: "57.14" },
  { id: 8, name: "Tripwires / Guardrails", scope: "core", maturity: "GA", coverage: 84, owner: "security", spans: 0.1, alerts: 1, lastSprint: "56.9" },
  { id: 9, name: "Audit Chain (WORM)", scope: "core", maturity: "Hardened", coverage: 99, owner: "compliance", spans: 0.4, alerts: 0, lastSprint: "53.5" },
  { id: 10, name: "i18n & Locale", scope: "core", maturity: "GA", coverage: 78, owner: "frontend", spans: 0.0, alerts: 0, lastSprint: "57.09" },
  { id: 11, name: "Subagent (Fork/AsTool/Teammate/Mailbox)", scope: "core", maturity: "Beta", coverage: 76, owner: "platform", spans: 0.7, alerts: 3, lastSprint: "57.15" },
  { id: 12, name: "Observability (cross-cutting)", scope: "cross-cutting", maturity: "Hardened", coverage: 92, owner: "platform", spans: 1.4, alerts: 0, lastSprint: "56.3" },
];

const matColor = (m) =>
  m === "Hardened" ? "var(--success)" :
  m === "GA" ? "var(--info)" :
  m === "Beta" ? "var(--warning)" :
  m === "Concept" ? "var(--fg-subtle)" : "var(--fg-muted)";

const DevUI = () => {
  const [tab, setTab] = useEx("matrix");
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Developer UI</div>
          <div className="page-sub">
            11 + 1 category maturity · Cat 12 cross-cutting metric panel
            <span className="route-pill">/devui</span>
            <Badge tone="warning">platform scope</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">Open in repo</Button>
          <Button variant="outline" size="sm" icon="download">Maturity report</Button>
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { id: "matrix", label: "Category Matrix" },
          { id: "cat12", label: "Cat 12 Metrics" },
          { id: "sse", label: "LoopEvent Coverage" },
          { id: "a11y", label: "A11y Audit" },
        ]}
      />

      {tab === "matrix" && <DevUIMatrix />}
      {tab === "cat12" && <DevUICat12 />}
      {tab === "sse" && <DevUISSE />}
      {tab === "a11y" && <A11yAudit />}
    </div>
  );
};

const DevUIMatrix = () => (
  <>
    <div className="grid-stats">
      <Stat label="Categories at GA+" value="9" unit="/12" delta="+1" deltaDir="up" />
      <Stat label="Avg test coverage" value="86.4" unit="%" delta="+1.8pp" deltaDir="up" />
      <Stat label="Open category alerts" value="7" delta="-2" deltaDir="up" />
      <Stat label="Bundle (gzipped)" value="297.9" unit="kB" delta="+2.1kB" deltaDir="down" />
    </div>

    <Card title="Category maturity matrix" subtitle="Owner + coverage + recent activity · click to drill" bodyClass="flush">
      <table className="table">
        <thead>
          <tr>
            <th style={{ width: 38 }}>Cat</th>
            <th>Name</th>
            <th>Maturity</th>
            <th>Owner</th>
            <th style={{ textAlign: "right" }}>Coverage</th>
            <th style={{ textAlign: "right" }}>Span rate</th>
            <th style={{ textAlign: "right" }}>Alerts</th>
            <th>Last sprint</th>
          </tr>
        </thead>
        <tbody>
          {CATEGORIES.map(c => (
            <tr key={c.id}>
              <td><span className="mono" style={{ fontSize: 11.5, color: "var(--fg-muted)" }}>{c.id === 12 ? "12*" : String(c.id).padStart(2, "0")}</span></td>
              <td>
                <div className="row" style={{ gap: 8 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: matColor(c.maturity) }} />
                  <span style={{ fontSize: 12.5 }}>{c.name}</span>
                  {c.scope === "cross-cutting" && <Badge tone="memory">cross-cutting</Badge>}
                </div>
              </td>
              <td><Badge tone={c.maturity === "Hardened" ? "success" : c.maturity === "GA" ? "info" : "warning"} dot>{c.maturity}</Badge></td>
              <td className="subtle" style={{ fontSize: 11.5 }}>@{c.owner}</td>
              <td className="mono tnum" style={{ textAlign: "right", color: c.coverage > 90 ? "var(--success)" : c.coverage > 80 ? "var(--fg)" : "var(--warning)" }}>{c.coverage}%</td>
              <td className="mono tnum subtle" style={{ textAlign: "right" }}>{c.spans.toFixed(1)}/s</td>
              <td style={{ textAlign: "right" }}>
                {c.alerts ? <Badge tone="danger">{c.alerts}</Badge> : <span className="subtle">—</span>}
              </td>
              <td className="mono subtle" style={{ fontSize: 11 }}>{c.lastSprint}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </>
);

const DevUICat12 = () => (
  <Card title="Cat 12 · OTel cross-cutting" subtitle="Span / log / metric volume by category">
    <div className="col" style={{ gap: 10 }}>
      {CATEGORIES.map(c => {
        const w = (c.spans / 1.4) * 100;
        return (
          <div key={c.id}>
            <div className="spread" style={{ marginBottom: 3 }}>
              <span className="mono" style={{ fontSize: 11.5 }}>cat-{String(c.id).padStart(2, "0")} · {c.name}</span>
              <span className="mono tnum subtle" style={{ fontSize: 11 }}>{c.spans.toFixed(1)} spans/s</span>
            </div>
            <div className="bar-track">
              <span style={{ width: w + "%", background: matColor(c.maturity) }} />
            </div>
          </div>
        );
      })}
    </div>
  </Card>
);

const DevUISSE = () => (
  <div className="grid-main">
    <Card title="LoopEvent SSE coverage" subtitle="22 event types · last 1h" actions={<Button variant="ghost" size="sm" icon="log" onClick={() => location.hash = "sse"}>Open SSE Inspector</Button>}>
      <div className="col" style={{ gap: 7, fontSize: 11.5 }}>
        {[
          { k: "ThinkingBlock.*", v: 14820, c: "var(--thinking)" },
          { k: "ToolCall.*", v: 8120, c: "var(--tool)" },
          { k: "VerificationResult", v: 6420, c: "var(--success)" },
          { k: "MemoryOp.*", v: 4820, c: "var(--memory)" },
          { k: "SubagentSpawned/Completed", v: 412, c: "var(--info)" },
          { k: "HITLRequested/Resolved", v: 184, c: "var(--warning)" },
          { k: "LoopIteration.start/end", v: 14820, c: "var(--primary)" },
        ].map(e => (
          <div key={e.k} className="spread">
            <span className="row" style={{ gap: 6 }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: e.c }} />
              <span className="mono">{e.k}</span>
            </span>
            <span className="mono tnum subtle">{e.v.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </Card>
    <Card title="Open category alerts" subtitle="Auto-paged · linked to PR / runbook">
      <div className="col" style={{ gap: 7, fontSize: 11.5 }}>
        {[
          { cat: "07 Verification", t: "Coverage below 75% gate", lvl: "high" },
          { cat: "07 Verification", t: "Flaky check: claim_pii_redacted", lvl: "medium" },
          { cat: "08 Tripwires", t: "Tripwire fired 3× in 1h: cross-tenant", lvl: "critical" },
          { cat: "11 Subagent", t: "Fork concurrency saturating", lvl: "high" },
          { cat: "11 Subagent", t: "Mailbox: stale message > 24h", lvl: "medium" },
          { cat: "11 Subagent", t: "AsTool: timeout > p95 budget", lvl: "medium" },
          { cat: "02 Tool Layer", t: "ToolSpec schema drift detected", lvl: "high" },
        ].map((a, i) => (
          <div key={i} className="row" style={{ gap: 8 }}>
            <SevDot level={a.lvl} />
            <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)", minWidth: 92 }}>{a.cat}</span>
            <span style={{ fontSize: 11.5 }}>{a.t}</span>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const A11yAudit = () => {
  const [running, setRunning] = useEx(false);
  const [results, setResults] = useEx(null);
  const [error, setError] = useEx(null);

  const loadAxe = () => new Promise((resolve, reject) => {
    if (window.axe) return resolve();
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/axe-core@4.10.0/axe.min.js";
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load axe-core from CDN"));
    document.head.appendChild(s);
  });

  const runAudit = async () => {
    setRunning(true);
    setError(null);
    try {
      await loadAxe();
      if (typeof window.axe === "undefined") {
        setError("axe-core failed to load from CDN. Check network or refresh.");
        setRunning(false);
        return;
      }
      const r = await window.axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      });
      setResults(r);
    } catch (e) {
      setError(String(e.message || e));
    }
    setRunning(false);
  };

  return (
    <div>
      <div className="grid-stats">
        <Stat label="Standard" value="WCAG-AA" />
        <Stat label="Routes audited" value={results ? "1" : "—"} unit={results ? "/ 15" : ""} />
        <Stat label="Violations" value={results ? String(results.violations.length) : "—"}
              deltaDir={results && results.violations.length > 0 ? "down" : "up"} />
        <Stat label="Passes" value={results ? String(results.passes.length) : "—"} />
      </div>

      <Card title="axe-core gate" subtitle="WCAG 2.1 AA · loaded from CDN · runs on current page" actions={
        <Button variant="primary" size="sm" icon="bolt" onClick={runAudit} disabled={running}>
          {running ? "Running…" : results ? "Re-run audit" : "Run audit"}
        </Button>
      }>
        {!results && !error && !running && (
          <div className="muted" style={{ fontSize: 12.5, padding: 8 }}>
            Click <b>Run audit</b> to scan the current DOM. The CI gate (axe-core e2e) runs the same checks across all 15 routes + auth pages on every PR.
          </div>
        )}
        {running && (
          <div className="row" style={{ gap: 10, padding: 8 }}>
            <div style={{ width: 18, height: 18, borderRadius: "50%", border: "2px solid var(--border)", borderTopColor: "var(--primary)", animation: "spin 0.8s linear infinite" }} />
            <span className="muted">Scanning DOM…</span>
          </div>
        )}
        {error && (
          <div className="hitl-card" data-severity="risk-high" style={{ margin: 0 }}>
            <div className="hitl-card-bar" />
            <div className="hitl-head"><span className="icon-ring"><Icon name="warn" size={13} /></span>Audit failed</div>
            <div className="muted" style={{ fontSize: 12 }}>{error}</div>
          </div>
        )}
        {results && (
          <div className="col" style={{ gap: 14 }}>
            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <Badge tone="danger">{results.violations.length} violations</Badge>
              <Badge tone="warning">{results.incomplete.length} incomplete</Badge>
              <Badge tone="success">{results.passes.length} passes</Badge>
              <Badge>{results.inapplicable.length} inapplicable</Badge>
              <span className="subtle mono" style={{ fontSize: 11 }}>· engine v{results.testEngine?.version}</span>
            </div>

            {results.violations.length > 0 ? (
              <div className="col" style={{ gap: 8 }}>
                {results.violations.map((v, i) => (
                  <div key={i} style={{ padding: 12, background: "var(--bg-2)", border: `1px solid ${v.impact === "critical" ? "var(--danger)" : v.impact === "serious" ? "var(--warning)" : "var(--border)"}`, borderLeft: `3px solid ${v.impact === "critical" ? "var(--danger)" : v.impact === "serious" ? "var(--warning)" : "var(--info)"}`, borderRadius: "var(--radius)" }}>
                    <div className="row" style={{ gap: 8, marginBottom: 4 }}>
                      <Badge tone={v.impact === "critical" ? "danger" : v.impact === "serious" ? "warning" : "info"}>{v.impact || "minor"}</Badge>
                      <span className="mono" style={{ fontSize: 12, fontWeight: 600 }}>{v.id}</span>
                      <span className="subtle mono" style={{ fontSize: 11 }}>· {v.nodes.length} node{v.nodes.length !== 1 ? "s" : ""}</span>
                    </div>
                    <div style={{ fontSize: 12.5, marginBottom: 6 }}>{v.help}</div>
                    <a href={v.helpUrl} target="_blank" rel="noopener noreferrer" className="mono" style={{ fontSize: 11, color: "var(--primary)" }}>{v.helpUrl}</a>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: 14, background: "oklch(from var(--success) l c h / 0.08)", border: "1px solid oklch(from var(--success) l c h / 0.3)", borderRadius: "var(--radius)", color: "var(--success)" }}>
                <Icon name="check" size={14} style={{ verticalAlign: "middle", marginRight: 6 }} />
                No violations on this route. CI gate passes.
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};

// ===================== /incidents — 5 IPA business domains =====================
const DOMAINS = [
  {
    id: "patrol", name: "Patrol", icon: "refresh", desc: "Scheduled checks across infra · cron / scope-aware",
    tone: "var(--tool)",
    stats: { active: 18, last24: 412, ok: 408, fail: 4 },
    items: [
      { id: "PTR-9921", title: "APAC database health", region: "ap-east-1", schedule: "every 5m", lastRun: "2m ago", status: "ok" },
      { id: "PTR-9912", title: "EU edge cache integrity", region: "eu-west-1", schedule: "every 15m", lastRun: "8m ago", status: "ok" },
      { id: "PTR-9871", title: "Cross-region replication lag", region: "global", schedule: "every 1m", lastRun: "now", status: "warn" },
      { id: "PTR-9810", title: "PCI scope ports", region: "global", schedule: "daily 02:00", lastRun: "6h ago", status: "ok" },
    ],
  },
  {
    id: "correlate", name: "Event Correlation", icon: "branch", desc: "Cluster signals across services into incidents",
    tone: "var(--thinking)",
    stats: { active: 7, last24: 1820, ok: 1808, fail: 12 },
    items: [
      { id: "EVT-44012", title: "payment-gateway 5xx + pgbouncer saturation", region: "ap-east-1", schedule: "—", lastRun: "now", status: "active" },
      { id: "EVT-44009", title: "auth-svc latency cluster (3 nodes)", region: "us-east-1", schedule: "—", lastRun: "12m ago", status: "active" },
      { id: "EVT-43988", title: "tenant_3kp9 token spike (anomaly)", region: "ap-east-1", schedule: "—", lastRun: "1h ago", status: "active" },
    ],
  },
  {
    id: "rca", name: "Root Cause Analysis", icon: "thinking", desc: "5-whys + timeline + verifiable evidence",
    tone: "var(--primary)",
    stats: { active: 4, last24: 28, ok: 26, fail: 2 },
    items: [
      { id: "RCA-2026-05-16", title: "payment-gateway 5xx spike", region: "ap-east-1", schedule: "—", lastRun: "now", status: "active" },
      { id: "RCA-2026-05-12", title: "cache eviction storm", region: "global", schedule: "—", lastRun: "4d ago", status: "done" },
      { id: "RCA-2026-05-08", title: "rollback failed on canary", region: "us-east-1", schedule: "—", lastRun: "8d ago", status: "done" },
    ],
  },
  {
    id: "audit", name: "Compliance Audit", icon: "audit", desc: "WORM evidence · PCI/SOC2/ISO27001 frameworks",
    tone: "var(--memory)",
    stats: { active: 3, last24: 84, ok: 84, fail: 0 },
    items: [
      { id: "AUD-Q2-2026", title: "Q2 SOC2 control evidence", region: "global", schedule: "quarterly", lastRun: "running", status: "active" },
      { id: "AUD-PCI-2026-05", title: "PCI-DSS scope quarterly review", region: "global", schedule: "quarterly", lastRun: "running", status: "active" },
      { id: "AUD-ANOM-3kp9", title: "Anomaly: tenant_3kp9 access pattern", region: "ap-east-1", schedule: "—", lastRun: "1h ago", status: "active" },
    ],
  },
  {
    id: "incident", name: "Incident Management", icon: "warn", desc: "P0/P1 lifecycle · on-call · postmortem",
    tone: "var(--danger)",
    stats: { active: 2, last24: 6, ok: 4, fail: 2 },
    items: [
      { id: "INC-4087", title: "payment-gateway SLO breach", region: "ap-east-1", schedule: "—", lastRun: "P1 · 4m ago", status: "active" },
      { id: "INC-4086", title: "edge-cdn cache poisoning", region: "us-east-1", schedule: "—", lastRun: "P2 · 21m ago", status: "active" },
      { id: "INC-4082", title: "auth-svc nightly latency", region: "us-east-1", schedule: "—", lastRun: "resolved", status: "done" },
    ],
  },
];

const Incidents = () => {
  const [active, setActive] = useEx("patrol");
  const d = DOMAINS.find(x => x.id === active);
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Business Domains</div>
          <div className="page-sub">
            5 IPA domains · operator workflows
            <span className="route-pill">/incidents</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="filter">All regions</Button>
          <Button variant="primary" size="sm" icon="plus">New incident</Button>
        </div>
      </div>

      <div className="grid-stats" style={{ gridTemplateColumns: "repeat(5, 1fr)" }}>
        {DOMAINS.map(dom => (
          <button key={dom.id}
            onClick={() => setActive(dom.id)}
            className="stat"
            style={{
              borderColor: active === dom.id ? dom.tone : "var(--border)",
              borderLeft: `3px solid ${dom.tone}`,
              cursor: "pointer", textAlign: "left",
              background: active === dom.id ? `oklch(from ${dom.tone} l c h / 0.05)` : "var(--bg-1)",
            }}>
            <div className="stat-label">
              <span className="row" style={{ gap: 6 }}>
                <Icon name={dom.icon} size={12} style={{ color: dom.tone }} />
                {dom.name}
              </span>
            </div>
            <div className="stat-value" style={{ fontSize: 22 }}>{dom.stats.active}</div>
            <div className="subtle" style={{ fontSize: 10.5, fontFamily: "var(--font-mono)", marginTop: -2 }}>
              {dom.stats.last24} runs · 24h
            </div>
          </button>
        ))}
      </div>

      <div className="grid-main">
        <Card
          title={<span className="row" style={{ gap: 8 }}>
            <Icon name={d.icon} size={14} style={{ color: d.tone }} />
            {d.name}
          </span>}
          subtitle={d.desc}
          bodyClass="flush"
          actions={<div className="row"><Button variant="ghost" size="sm" icon="filter">Filter</Button><Button variant="outline" size="sm" iconRight="arrow_right" onClick={() => { location.hash = `domain-${active === 'correlate' ? 'correlation' : active === 'audit' ? 'audit' : active}`; }}>Open detail</Button><Button variant="outline" size="sm" icon="plus">New</Button></div>}
        >
          <table className="table">
            <thead>
              <tr><th>ID</th><th>Title</th><th>Region</th><th>Schedule</th><th>Last run</th><th>Status</th></tr>
            </thead>
            <tbody>
              {d.items.map(it => (
                <tr key={it.id}>
                  <td className="mono" style={{ fontSize: 11.5, color: "var(--fg-muted)" }}>{it.id}</td>
                  <td style={{ fontSize: 12.5 }}>{it.title}</td>
                  <td className="mono subtle" style={{ fontSize: 11.5 }}>{it.region}</td>
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

        <Card title="Domain agents" subtitle="Assigned to this domain">
          <div className="col" style={{ gap: 10 }}>
            {{
              patrol: ["patrol-runner", "patrol-scheduler"],
              correlate: ["correlator-bot", "anomaly-detector"],
              rca: ["rca-bot", "evidence-collector"],
              audit: ["compliance-auditor", "evidence-exporter"],
              incident: ["incident-responder", "change-reviewer", "postmortem-writer"],
            }[d.id].map(name => (
              <div key={name} className="row" style={{ gap: 10, padding: "6px 0" }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: `oklch(from ${d.tone} l c h / 0.2)`, color: d.tone, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Icon name={d.icon} size={13} />
                </div>
                <div className="grow">
                  <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{name}</div>
                  <div className="subtle mono" style={{ fontSize: 10.5 }}>claude-haiku-4-5 · 6 tools</div>
                </div>
                <Badge tone="success" dot>live</Badge>
              </div>
            ))}
            <div className="hr" style={{ margin: "4px 0" }} />
            <Button variant="outline" size="sm" icon="plus">Assign agent</Button>
          </div>
          <div className="hr" />
          <div className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>Tools in scope</div>
          <div className="kbar">
            {(d.id === "patrol" ? ["patrol_schedule", "patrol_get_results", "patrol_acknowledge"] :
              d.id === "correlate" ? ["events_subscribe", "correlate_window", "incident_open"] :
              d.id === "rca" ? ["incident_get", "metrics.query", "log.tail", "evidence.attach"] :
              d.id === "audit" ? ["audit_query_logs", "audit.export_chain", "evidence.bundle"] :
              ["incident_get", "k8s.set_env", "k8s.rollback", "page_oncall"])
              .map(t => <Badge key={t} tone="tool" pill>{t}</Badge>)}
          </div>
        </Card>
      </div>
    </div>
  );
};

// ===================== /verification — claim verification dashboard =====================
const VERIFY_CLAIMS = [
  { id: "vc_4tk2p_1", agent: "incident-responder", session: "sess_4tk2p", claim: "pgbouncer pool saturated at 50/50 since 10:22", evidence: "metrics.query series; saturation_since field non-null", ok: true, score: 0.94, ms: 18, kind: "metric_match", at: "now" },
  { id: "vc_4tk2p_2", agent: "incident-responder", session: "sess_4tk2p", claim: "INC-4012 was resolved by raising pool 50 → 200", evidence: "incidents.list returned resolved record with matching resolution text", ok: true, score: 0.98, ms: 12, kind: "doc_match", at: "now" },
  { id: "vc_88vqc_3", agent: "rca-bot", session: "sess_88vqc", claim: "cache eviction was due to TTL inversion", evidence: "redis.info before/after; pattern matches RCA-2026-04 root_cause", ok: true, score: 0.87, ms: 42, kind: "doc_match", at: "5m ago" },
  { id: "vc_91kxu_4", agent: "compliance-auditor", session: "sess_91kxu", claim: "All PCI scope ports are gated by FW rule pci-edge-22", evidence: "audit.export_chain returned 1 row; rule signature matches", ok: true, score: 0.99, ms: 64, kind: "evidence_chain", at: "8m ago" },
  { id: "vc_2za8mc_5", agent: "lead-enricher", session: "sess_2za8mc", claim: "Contact email enriched from public source", evidence: "expected source url not in allowlist", ok: false, score: 0.42, ms: 28, kind: "source_allowlist", at: "9m ago" },
  { id: "vc_4tk2p_6", agent: "incident-responder", session: "sess_4tk2p", claim: "pgbouncer pool fix matches canary-only deployment", evidence: "k8s.get_deployment shows pool=50 only on canary; prod is 200", ok: true, score: 0.96, ms: 22, kind: "metric_match", at: "12m ago" },
  { id: "vc_77kzpn_7", agent: "meeting-notetaker", session: "sess_77kzpn", claim: "Action items extracted with owner assigned", evidence: "verifier.check failed: 1 of 5 items has no owner", ok: false, score: 0.62, ms: 14, kind: "schema_completeness", at: "20m ago" },
  { id: "vc_xq71vt_8", agent: "code-reviewer", session: "sess_xq71vt", claim: "PR-482 covers added function with unit test", evidence: "coverage.json reports 100% on changed lines", ok: true, score: 0.99, ms: 88, kind: "coverage_match", at: "26m ago" },
];

const VerificationPage = () => {
  const passRate = (VERIFY_CLAIMS.filter(c => c.ok).length / VERIFY_CLAIMS.length * 100).toFixed(1);
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Verification</div>
          <div className="page-sub">
            Range 7 · Claim verification with evidence · failed claims block downstream actions
            <span className="route-pill">/verification</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="filter">All kinds</Button>
          <Button variant="outline" size="sm" icon="download">Export</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Pass rate · 1h" value={passRate} unit="%" delta="-1.4pp" deltaDir="down" />
        <Stat label="Claims · 1h" value="2,840" delta="+180" deltaDir="up" />
        <Stat label="Failed · 1h" value="22" delta="+4" deltaDir="down" />
        <Stat label="Median latency" value="24" unit="ms" delta="-3ms" deltaDir="up" />
      </div>

      <div className="grid-main">
        <Card title="Recent verification runs" subtitle="Most recent first · failures pinned" bodyClass="flush">
          <table className="table">
            <thead><tr><th></th><th>Claim</th><th>Agent</th><th>Kind</th><th style={{ textAlign: "right" }}>Score</th><th>When</th></tr></thead>
            <tbody>
              {VERIFY_CLAIMS.map(c => (
                <tr key={c.id}>
                  <td>
                    {c.ok
                      ? <span style={{ width: 16, height: 16, borderRadius: "50%", background: "oklch(from var(--success) l c h / 0.2)", color: "var(--success)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name="check" size={10} /></span>
                      : <span style={{ width: 16, height: 16, borderRadius: "50%", background: "oklch(from var(--danger) l c h / 0.2)", color: "var(--danger)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name="x" size={10} /></span>}
                  </td>
                  <td>
                    <div style={{ fontSize: 12.5 }}>{c.claim}</div>
                    <div className="subtle mono" style={{ fontSize: 11, marginTop: 2 }}>evidence: {c.evidence}</div>
                  </td>
                  <td className="mono" style={{ fontSize: 11.5, color: "var(--fg-muted)" }}>{c.agent}</td>
                  <td><Badge tone="success">{c.kind}</Badge></td>
                  <td className="mono tnum" style={{ textAlign: "right", color: c.score > 0.85 ? "var(--success)" : c.score > 0.6 ? "var(--warning)" : "var(--danger)" }}>{c.score.toFixed(2)}</td>
                  <td className="subtle" style={{ fontSize: 11.5 }}>{c.at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <div className="col" style={{ gap: 14 }}>
          <Card title="Failure kinds" subtitle="What's breaking">
            <div className="col" style={{ gap: 8, fontSize: 12 }}>
              {[
                { k: "source_allowlist", n: 18, c: "var(--danger)" },
                { k: "schema_completeness", n: 12, c: "var(--warning)" },
                { k: "metric_threshold", n: 8, c: "var(--warning)" },
                { k: "evidence_chain", n: 3, c: "var(--memory)" },
                { k: "doc_match", n: 2, c: "var(--info)" },
              ].map(f => (
                <div key={f.k}>
                  <div className="spread" style={{ marginBottom: 3 }}>
                    <span className="row" style={{ gap: 6 }}>
                      <span style={{ width: 5, height: 5, borderRadius: "50%", background: f.c }} />
                      <span className="mono" style={{ fontSize: 11.5 }}>{f.k}</span>
                    </span>
                    <span className="mono tnum" style={{ fontSize: 11 }}>{f.n}</span>
                  </div>
                  <div className="bar-track">
                    <span style={{ width: (f.n / 22 * 100) + "%", background: f.c }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Flaky checks" subtitle="Failing &gt; 5%, last 24h">
            <div className="col" style={{ gap: 6, fontSize: 12 }}>
              {[
                { check: "claim_pii_redacted", rate: "18%", agent: "compliance-auditor" },
                { check: "source_in_allowlist", rate: "12%", agent: "lead-enricher" },
                { check: "schema.action_items_have_owner", rate: "8%", agent: "meeting-notetaker" },
              ].map(f => (
                <div key={f.check} className="spread">
                  <div>
                    <div className="mono" style={{ fontSize: 11.5 }}>{f.check}</div>
                    <div className="subtle mono" style={{ fontSize: 10.5 }}>{f.agent}</div>
                  </div>
                  <Badge tone="warning">{f.rate}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ===================== /feature-flags (lifted out of /tenant-settings) =====================
const FeatureFlagsPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Feature Flags</div>
        <div className="page-sub">
          Tenant-scoped overrides · changes audited
          <span className="route-pill">/feature-flags</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="git">Open ConfigMap</Button>
        <Button variant="primary" size="sm" icon="plus">New flag</Button>
      </div>
    </div>

    <Card title="14 flags" subtitle="acme-prod tenant · operator scope read-only · admin can edit" bodyClass="flush">
      <table className="table">
        <thead><tr><th>Flag</th><th>Description</th><th>Default</th><th>Override</th><th>Rolled out</th><th></th></tr></thead>
        <tbody>
          {[
            { k: "subagent.fork.enabled", desc: "Allow concurrent fork mode", def: "on", on: true, rollout: 100 },
            { k: "subagent.max_depth", desc: "Maximum subagent recursion depth", def: "5", on: 5, ctl: "num", rollout: 100 },
            { k: "memory.long_term_write", desc: "Allow writes to user/tenant memory", def: "on", on: true, rollout: 100 },
            { k: "tool.sandbox_full", desc: "Permit FULL_SANDBOX tool runs", def: "off", on: false, rollout: 0 },
            { k: "hitl.escalate_to_teams", desc: "Mirror HITL events to MS Teams", def: "on", on: true, rollout: 100 },
            { k: "verification.required", desc: "Block tool output without verification", def: "on", on: true, rollout: 100 },
            { k: "loop.max_iterations", desc: "Hard ceiling on loop turns", def: "30", on: 30, ctl: "num", rollout: 100 },
            { k: "streaming.thinking", desc: "Stream thinking blocks to client", def: "on", on: true, rollout: 100 },
            { k: "hitl.async_via_email", desc: "Off-platform approvals via email", def: "off", on: false, rollout: 0 },
            { k: "rag.use_voyage_3", desc: "Embedding upgrade voyage-3", def: "on", on: true, rollout: 80 },
            { k: "audit.merkle_export", desc: "Export Merkle chain segments", def: "on", on: true, rollout: 100 },
            { k: "i18n.locale_zh_tw", desc: "繁體中文 UI", def: "on", on: true, rollout: 100 },
            { k: "ui.tweaks_panel", desc: "Show in-product theme tweaks", def: "off", on: false, rollout: 0 },
            { k: "loop.detailed_traces", desc: "Stream Cat 12 spans to client", def: "off", on: false, rollout: 10 },
          ].map(f => (
            <tr key={f.k}>
              <td className="mono" style={{ fontSize: 12 }}>{f.k}</td>
              <td className="subtle" style={{ fontSize: 12 }}>{f.desc}</td>
              <td><Badge>{f.def}</Badge></td>
              <td>
                {f.ctl === "num"
                  ? <input className="input mono" style={{ width: 70, fontSize: 12 }} defaultValue={f.on} />
                  : <Switch on={f.on} />}
              </td>
              <td style={{ width: 130 }}>
                <div className="row" style={{ gap: 6 }}>
                  <div className="bar-track" style={{ width: 80 }}>
                    <span style={{ width: f.rollout + "%" }} />
                  </div>
                  <span className="mono tnum subtle" style={{ fontSize: 10.5 }}>{f.rollout}%</span>
                </div>
              </td>
              <td><Icon name="dots" size={14} className="subtle" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

Object.assign(window, { AuthLogin, AuthCallback, AuthDev, SubagentTree, DevUI, Incidents, VerificationPage, FeatureFlagsPage });
