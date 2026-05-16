/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, Stat, Spark */
const { useState: useAd } = React;

// ============ Shared mini-chart ============
const AreaChart = ({ data, tone = "var(--primary)", h = 180, yLabel }) => {
  const w = 760, pad = 24;
  const max = Math.max(...data) * 1.15;
  const step = (w - pad * 2) / (data.length - 1);
  const points = data.map((v, i) => [pad + i * step, h - pad - (v / max) * (h - pad * 2)]);
  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L${points.at(-1)[0]},${h - pad} L${pad},${h - pad} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart" preserveAspectRatio="none">
      <defs>
        <linearGradient id={`ag-${tone.replace(/[^a-z]/gi, "")}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={tone} stopOpacity="0.32" />
          <stop offset="100%" stopColor={tone} stopOpacity="0" />
        </linearGradient>
      </defs>
      <g className="grid">
        {[0.25, 0.5, 0.75].map(t => (
          <line key={t} x1={pad} x2={w - pad} y1={pad + (h - pad * 2) * t} y2={pad + (h - pad * 2) * t} />
        ))}
      </g>
      <path d={area} fill={`url(#ag-${tone.replace(/[^a-z]/gi, "")})`} />
      <path d={line} fill="none" stroke={tone} strokeWidth="1.5" />
    </svg>
  );
};

// ============ /sla-dashboard ============
const SlaPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">SLA Dashboard</div>
        <div className="page-sub">
          Range 12 · Observability · p50 / p95 / p99 latency + error budget
          <span className="route-pill">/sla-dashboard</span>
        </div>
      </div>
      <div className="page-actions">
        <div className="btn-group">
          <Button variant="ghost" size="sm">1h</Button>
          <Button variant="outline" size="sm">24h</Button>
          <Button variant="ghost" size="sm">7d</Button>
          <Button variant="ghost" size="sm">30d</Button>
        </div>
        <Button variant="outline" size="sm" icon="refresh">Refresh</Button>
        <Button variant="outline" size="sm" icon="download">Export</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="p50 latency" value="284" unit="ms" delta="-18ms" deltaDir="up" spark={<Spark points={[320,310,300,295,290,288,290,286,284,282,284]} tone="var(--primary)" />} />
      <Stat label="p95 latency" value="1.84" unit="s" delta="-180ms" deltaDir="up" spark={<Spark points={[2.1,2.0,2.0,1.9,1.92,1.88,1.85,1.84,1.83,1.84]} tone="var(--info)" />} />
      <Stat label="p99 latency" value="4.21" unit="s" delta="+0.30s" deltaDir="down" spark={<Spark points={[3.6,3.7,3.8,3.9,4.0,4.1,4.0,4.2,4.21]} tone="var(--warning)" />} />
      <Stat label="Error budget" value="92.4" unit="%" delta="-1.2pp" deltaDir="down" spark={<Spark points={[100,99,98,97,96,95,94,93,92.4]} tone="var(--success)" />} />
    </div>

    <div className="grid-main">
      <Card title="Latency distribution" subtitle="24h · all agents · p50 / p95 / p99" actions={
        <div className="kbar">
          <Badge tone="primary" dot>p50</Badge>
          <Badge tone="info" dot>p95</Badge>
          <Badge tone="warning" dot>p99</Badge>
        </div>
      }>
        <LatencyChart />
      </Card>

      <Card title="SLO status" subtitle="Active SLO objectives">
        <div className="col" style={{ gap: 12 }}>
          {[
            { name: "Loop p95 < 2s", current: 1.84, target: 2.0, ok: true, used: 8 },
            { name: "Tool success ≥ 99%", current: 99.4, target: 99, ok: true, used: 28 },
            { name: "HITL response < 5m", current: 2.3, target: 5, ok: true, used: 12 },
            { name: "Subagent depth ≤ 5", current: 4, target: 5, ok: true, used: 0 },
            { name: "Cost / run < $0.05", current: 0.052, target: 0.05, ok: false, used: 108 },
          ].map(s => (
            <div key={s.name}>
              <div className="spread" style={{ marginBottom: 4 }}>
                <span className="row" style={{ gap: 6, fontSize: 12.5 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.ok ? "var(--success)" : "var(--danger)" }} />
                  {s.name}
                </span>
                <span className="mono tnum" style={{ fontSize: 11.5, color: s.ok ? "var(--fg-muted)" : "var(--danger)" }}>
                  {s.current} <span className="subtle">/ {s.target}</span>
                </span>
              </div>
              <div className="bar-track">
                <span style={{ width: Math.min(100, s.used) + "%", background: s.ok ? "var(--success)" : "var(--danger)" }} />
              </div>
              <div className="subtle mono" style={{ fontSize: 10, marginTop: 3 }}>budget used: {s.used}%</div>
            </div>
          ))}
        </div>
      </Card>
    </div>

    <div style={{ height: 14 }} />

    <div className="grid-main">
      <Card title="Top slow operations" subtitle="p99 contributors · last 24h" bodyClass="flush">
        <table className="table">
          <thead>
            <tr><th>Operation</th><th>Kind</th><th style={{ textAlign: "right" }}>p50</th><th style={{ textAlign: "right" }}>p95</th><th style={{ textAlign: "right" }}>p99</th><th style={{ textAlign: "right" }}>Calls</th></tr>
          </thead>
          <tbody>
            {[
              { name: "tool.metrics.query", k: "tool", p50: 180, p95: 1900, p99: 4400, calls: 2840 },
              { name: "tool.k8s.set_env", k: "tool", p50: 920, p95: 2800, p99: 5200, calls: 18 },
              { name: "loop.iteration", k: "loop", p50: 290, p95: 1820, p99: 4100, calls: 14820 },
              { name: "subagent.spawn", k: "subagent", p50: 12, p95: 38, p99: 220, calls: 412 },
              { name: "verification.run", k: "verify", p50: 18, p95: 84, p99: 180, calls: 9200 },
              { name: "memory.write", k: "memory", p50: 4, p95: 12, p99: 38, calls: 7820 },
            ].map(r => (
              <tr key={r.name}>
                <td className="mono" style={{ fontSize: 11.5 }}>{r.name}</td>
                <td><Badge tone={r.k === "tool" ? "tool" : r.k === "memory" ? "memory" : r.k === "subagent" ? "thinking" : r.k === "verify" ? "success" : "primary"}>{r.k}</Badge></td>
                <td className="mono tnum" style={{ textAlign: "right" }}>{r.p50}ms</td>
                <td className="mono tnum" style={{ textAlign: "right" }}>{r.p95}ms</td>
                <td className="mono tnum" style={{ textAlign: "right", color: r.p99 > 3000 ? "var(--warning)" : "var(--fg-muted)" }}>{r.p99}ms</td>
                <td className="mono tnum subtle" style={{ textAlign: "right" }}>{r.calls.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Error rate by service" subtitle="Last hour">
        <div className="col" style={{ gap: 10 }}>
          {[
            { name: "inference.adapter", rate: 0.04 },
            { name: "tool.runner", rate: 0.6 },
            { name: "memory.store", rate: 0.0 },
            { name: "audit.writer", rate: 0.0 },
            { name: "subagent.scheduler", rate: 0.12 },
            { name: "webhook.dispatcher", rate: 0.4 },
          ].map(s => (
            <div key={s.name}>
              <div className="spread" style={{ marginBottom: 3 }}>
                <span className="mono" style={{ fontSize: 11.5 }}>{s.name}</span>
                <span className="mono tnum" style={{ fontSize: 11, color: s.rate > 0.5 ? "var(--warning)" : "var(--fg-muted)" }}>{s.rate.toFixed(2)}%</span>
              </div>
              <div className="bar-track">
                <span style={{ width: Math.min(100, s.rate * 50) + "%", background: s.rate > 0.5 ? "var(--warning)" : "var(--success)" }} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  </div>
);

const LatencyChart = () => {
  // 3 series: p50, p95, p99
  const data = Array.from({ length: 48 }, (_, i) => {
    const x = i / 47;
    const base = 280 + Math.sin(x * 6) * 30;
    return {
      p50: base + Math.random() * 20,
      p95: base * 5.2 + Math.random() * 200 + Math.sin(x * 8) * 100,
      p99: base * 11 + Math.random() * 500 + (i > 35 ? 800 : 0),
    };
  });
  const w = 760, h = 220, pad = 30;
  const max = Math.max(...data.map(d => d.p99)) * 1.1;
  const step = (w - pad * 2) / (data.length - 1);
  const series = ["p50", "p95", "p99"];
  const colors = { p50: "var(--primary)", p95: "var(--info)", p99: "var(--warning)" };
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart" preserveAspectRatio="none" style={{ height: 220 }}>
      <g className="grid">
        {[0.25, 0.5, 0.75].map(t => (
          <line key={t} x1={pad} x2={w - pad} y1={pad + (h - pad * 2) * t} y2={pad + (h - pad * 2) * t} />
        ))}
      </g>
      <g className="axis">
        {[0, 12, 24, 36, 47].map(i => (
          <text key={i} x={pad + i * step} y={h - 8} textAnchor="middle">
            -{Math.round((47 - i) / 2)}h
          </text>
        ))}
        {[0, 0.25, 0.5, 0.75].map(t => (
          <text key={t} x={pad - 6} y={pad + (h - pad * 2) * t + 3} textAnchor="end">
            {Math.round(max * (1 - t)) + "ms"}
          </text>
        ))}
      </g>
      {series.map(s => {
        const d = data.map((dp, i) => `${i === 0 ? "M" : "L"}${pad + i * step},${h - pad - (dp[s] / max) * (h - pad * 2)}`).join(" ");
        return <path key={s} d={d} fill="none" stroke={colors[s]} strokeWidth={s === "p50" ? 1.8 : 1.4} opacity={s === "p99" ? 0.9 : 1} />;
      })}
    </svg>
  );
};

// ============ /cost-dashboard ============
const CostPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Cost Ledger</div>
        <div className="page-sub">
          Range 12 · Token + tool spend · admin-only provider breakdown
          <span className="route-pill">/cost-dashboard</span>
          <Badge tone="warning">admin scope</Badge>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="filter">By tenant</Button>
        <Button variant="outline" size="sm" icon="download">CSV</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Spend · MTD" value="$2,847" delta="+8.4%" deltaDir="down" spark={<Spark points={[1200,1450,1700,1980,2200,2400,2600,2847]} tone="var(--memory)" />} />
      <Stat label="Tokens · MTD" value="14.2" unit="M" delta="+2.1M" deltaDir="up" spark={<Spark points={[8,9,10,11,12,13,14,14.2]} />} />
      <Stat label="Cost / run" value="$0.052" delta="+$0.004" deltaDir="down" spark={<Spark points={[0.044,0.046,0.048,0.05,0.05,0.052,0.052]} tone="var(--warning)" />} />
      <Stat label="Cache hit rate" value="38" unit="%" delta="+4pp" deltaDir="up" spark={<Spark points={[28,30,32,34,35,36,37,38]} tone="var(--success)" />} />
    </div>

    <div className="grid-main">
      <Card title="Spend over time" subtitle="Daily · 30 days · stacked by category">
        <AreaChart data={[80,90,85,95,110,105,120,115,130,140,128,150,145,160,170,165,180,175,190,200,195,210,220,230,225,240,255,250,265,284]} tone="var(--memory)" h={200} />
      </Card>

      <Card title="Spend by category" subtitle="Last 7 days">
        <div className="col" style={{ gap: 12 }}>
          {[
            { name: "Inference (input)", v: 1240, pct: 44, c: "var(--thinking)" },
            { name: "Inference (output)", v: 780, pct: 27, c: "var(--primary)" },
            { name: "Thinking tokens", v: 412, pct: 14, c: "var(--info)" },
            { name: "Tool runs", v: 280, pct: 10, c: "var(--tool)" },
            { name: "Embeddings", v: 90, pct: 3, c: "var(--memory)" },
            { name: "Sandbox compute", v: 45, pct: 2, c: "var(--warning)" },
          ].map(s => (
            <div key={s.name}>
              <div className="spread" style={{ marginBottom: 4 }}>
                <span className="row" style={{ gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: s.c }} />
                  <span style={{ fontSize: 12 }}>{s.name}</span>
                </span>
                <span className="mono tnum" style={{ fontSize: 11.5 }}>${s.v.toLocaleString()}</span>
              </div>
              <div className="bar-track"><span style={{ width: s.pct + "%", background: s.c }} /></div>
            </div>
          ))}
        </div>
      </Card>
    </div>

    <div style={{ height: 14 }} />

    <div className="grid-main">
      <Card title="Spend by tenant" subtitle="MTD · top 8" bodyClass="flush">
        <table className="table">
          <thead><tr><th>Tenant</th><th>Plan</th><th style={{ textAlign: "right" }}>Tokens</th><th style={{ textAlign: "right" }}>Cost</th><th style={{ textAlign: "right" }}>Quota used</th><th></th></tr></thead>
          <tbody>
            {[
              { name: "acme-prod", plan: "Pro", tokens: "4.2M", cost: 842, pct: 42 },
              { name: "globex-eu", plan: "Pro", tokens: "3.1M", cost: 624, pct: 62 },
              { name: "initech-jp", plan: "Enterprise", tokens: "2.8M", cost: 581, pct: 14 },
              { name: "umbrella-us", plan: "Pro", tokens: "1.7M", cost: 342, pct: 34 },
              { name: "wonka-apac", plan: "Starter", tokens: "0.9M", cost: 184, pct: 92, warn: true },
              { name: "stark-prod", plan: "Pro", tokens: "0.7M", cost: 138, pct: 7 },
              { name: "wayne-corp", plan: "Enterprise", tokens: "0.5M", cost: 96, pct: 5 },
              { name: "tenant_3kp9", plan: "Starter", tokens: "2.4M", cost: 480, pct: 320, warn: true, alert: true },
            ].map(t => (
              <tr key={t.name}>
                <td className="row" style={{ gap: 6 }}>
                  <span style={{ width: 18, height: 18, borderRadius: 4, background: "var(--primary-soft-2)", color: "var(--primary)", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 600 }}>{t.name[0].toUpperCase()}</span>
                  <span className="mono" style={{ fontSize: 12 }}>{t.name}</span>
                  {t.alert && <Badge tone="danger" dot>anomaly</Badge>}
                </td>
                <td><Badge>{t.plan}</Badge></td>
                <td className="mono tnum subtle" style={{ textAlign: "right" }}>{t.tokens}</td>
                <td className="mono tnum" style={{ textAlign: "right" }}>${t.cost}</td>
                <td style={{ textAlign: "right" }}>
                  <span className="mono tnum" style={{ fontSize: 11, color: t.pct > 100 ? "var(--danger)" : t.pct > 80 ? "var(--warning)" : "var(--fg-muted)" }}>{t.pct}%</span>
                </td>
                <td style={{ width: 100 }}>
                  <div className="bar-track">
                    <span style={{ width: Math.min(100, t.pct) + "%", background: t.pct > 100 ? "var(--danger)" : t.pct > 80 ? "var(--warning)" : "var(--success)" }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Provider mix" subtitle={<span className="row" style={{ gap: 6 }}><Icon name="shield" size={11} /> Admin-only · UI shields from operators</span>}>
        <div className="col" style={{ gap: 10 }}>
          {[
            { p: "provider-A", tokens: "8.1M", cost: 1620, pct: 57, c: "var(--primary)" },
            { p: "provider-B", tokens: "4.4M", cost: 884, pct: 31, c: "var(--thinking)" },
            { p: "provider-C", tokens: "1.3M", cost: 260, pct: 9, c: "var(--tool)" },
            { p: "self-hosted", tokens: "0.4M", cost: 83, pct: 3, c: "var(--memory)" },
          ].map(s => (
            <div key={s.p}>
              <div className="spread" style={{ marginBottom: 4 }}>
                <span className="row" style={{ gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: s.c }} />
                  <span className="mono" style={{ fontSize: 12 }}>{s.p}</span>
                </span>
                <span className="mono tnum" style={{ fontSize: 11.5 }}>${s.cost} <span className="subtle">· {s.tokens}</span></span>
              </div>
              <div className="bar-track"><span style={{ width: s.pct + "%", background: s.c }} /></div>
            </div>
          ))}
          <div className="thin-rule" />
          <div className="subtle" style={{ fontSize: 11 }}>Provider identity is redacted in operator views to enforce LLM-neutrality. Switching providers does not change tool semantics.</div>
        </div>
      </Card>
    </div>
  </div>
);

// ============ /admin/tenants ============
const TENANTS = [
  { id: "tenant_01h9a2", name: "acme-prod", plan: "Pro", seats: 8, region: "ap-east-1", agents: 12, runs24: 14820, status: "active", created: "2024-11-04" },
  { id: "tenant_01h7zz", name: "globex-eu", plan: "Pro", seats: 12, region: "eu-west-1", agents: 18, runs24: 9820, status: "active", created: "2024-09-12" },
  { id: "tenant_01h6kp", name: "initech-jp", plan: "Enterprise", seats: 42, region: "ap-northeast-1", agents: 28, runs24: 18420, status: "active", created: "2023-06-22" },
  { id: "tenant_01h22a", name: "umbrella-us", plan: "Pro", seats: 6, region: "us-east-1", agents: 7, runs24: 3820, status: "active", created: "2025-01-30" },
  { id: "tenant_01j33b", name: "wonka-apac", plan: "Starter", seats: 3, region: "ap-southeast-1", agents: 4, runs24: 220, status: "quota-warn", created: "2025-02-14" },
  { id: "tenant_01k77c", name: "stark-prod", plan: "Pro", seats: 9, region: "us-west-2", agents: 11, runs24: 1820, status: "active", created: "2024-04-08" },
  { id: "tenant_01n44d", name: "wayne-corp", plan: "Enterprise", seats: 22, region: "us-east-1", agents: 19, runs24: 880, status: "active", created: "2023-11-19" },
  { id: "tenant_3kp9",   name: "tenant_3kp9", plan: "Starter", seats: 2, region: "ap-east-1", agents: 1, runs24: 12200, status: "anomaly", created: "2026-05-01" },
];

const TenantsPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Tenants</div>
        <div className="page-sub">
          Multi-tenant lifecycle · RLS-isolated · feature flags + quotas per tenant
          <span className="route-pill">/admin/tenants</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="download">Export</Button>
        <Button variant="primary" size="sm" icon="plus">New tenant</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Active tenants" value="48" delta="+3" deltaDir="up" />
      <Stat label="Total seats" value="284" delta="+18" deltaDir="up" />
      <Stat label="Agents deployed" value="612" delta="+24" deltaDir="up" />
      <Stat label="Anomalies" value="1" delta="+1" deltaDir="down" />
    </div>

    <Card title="All tenants" subtitle="48 active · 3 anomalies in last 24h" bodyClass="flush" actions={
      <div className="row">
        <div className="cmdk" style={{ minWidth: 220 }}>
          <Icon name="search" size={13} />
          <span className="grow">Filter by name, id, region…</span>
        </div>
        <Button variant="ghost" size="sm" icon="filter">Plan: all</Button>
        <Button variant="ghost" size="sm" icon="sliders">Sort: runs (24h)</Button>
      </div>
    }>
      <table className="table">
        <thead>
          <tr>
            <th>Tenant</th>
            <th>Plan</th>
            <th>Region</th>
            <th style={{ textAlign: "right" }}>Seats</th>
            <th style={{ textAlign: "right" }}>Agents</th>
            <th style={{ textAlign: "right" }}>Runs · 24h</th>
            <th>Status</th>
            <th>Created</th>
            <th style={{ width: 28 }}></th>
          </tr>
        </thead>
        <tbody>
          {TENANTS.map(t => (
            <tr key={t.id}>
              <td>
                <div className="row" style={{ gap: 8 }}>
                  <span style={{ width: 24, height: 24, borderRadius: 5, background: "var(--primary-soft-2)", color: "var(--primary)", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 600 }}>{t.name[0].toUpperCase()}</span>
                  <div>
                    <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{t.name}</div>
                    <div className="mono subtle" style={{ fontSize: 10.5 }}>{t.id}</div>
                  </div>
                </div>
              </td>
              <td><Badge tone={t.plan === "Enterprise" ? "primary" : t.plan === "Pro" ? "info" : ""}>{t.plan}</Badge></td>
              <td className="mono subtle" style={{ fontSize: 11.5 }}>{t.region}</td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{t.seats}</td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{t.agents}</td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{t.runs24.toLocaleString()}</td>
              <td>
                <Badge tone={t.status === "active" ? "success" : t.status === "anomaly" ? "danger" : "warning"} dot>{t.status}</Badge>
              </td>
              <td className="subtle" style={{ fontSize: 11.5 }}>{t.created}</td>
              <td><Icon name="dots" size={14} className="subtle" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

// ============ /admin/tenant-settings ============
const TenantSettings = () => {
  const [tab, setTab] = useAd("general");
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Tenant Settings</div>
          <div className="page-sub">
            <span className="mono" style={{ color: "var(--fg)", fontWeight: 500 }}>acme-prod</span>
            <span className="route-pill">tenant_01h9a2</span>
            <Badge tone="primary">Pro · 8 seats</Badge>
          </div>
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { id: "general", label: "General" },
          { id: "flags", label: "Feature Flags", count: 14 },
          { id: "quotas", label: "Quotas" },
          { id: "hitl", label: "HITL Policies" },
          { id: "members", label: "Members", count: 8 },
          { id: "danger", label: "Danger Zone" },
        ]}
      />

      {tab === "general" && (
        <div className="grid-main">
          <Card title="General">
            <div className="col" style={{ gap: 14, maxWidth: 480 }}>
              <Field label="Display name"><input className="input" defaultValue="acme-prod" /></Field>
              <Field label="Tenant id"><input className="input mono" readOnly defaultValue="tenant_01h9a2" /></Field>
              <Field label="Default region"><select className="select" defaultValue="ap-east-1"><option>ap-east-1</option><option>us-east-1</option><option>eu-west-1</option></select></Field>
              <Field label="Default locale"><select className="select" defaultValue="zh-TW"><option>zh-TW</option><option>en-US</option><option>ja-JP</option></select></Field>
              <Field label="Data retention" help="Memory + audit retention. WORM audit is append-only.">
                <div className="row" style={{ gap: 8 }}>
                  <input className="input" defaultValue="365" style={{ maxWidth: 100 }} /><span className="muted">days</span>
                </div>
              </Field>
            </div>
          </Card>
          <Card title="Identity & SSO">
            <div className="col" style={{ gap: 10, fontSize: 12 }}>
              <div className="spread"><span className="muted">Provider</span><Badge>SAML 2.0 · WorkOS</Badge></div>
              <div className="spread"><span className="muted">SCIM</span><Badge tone="success" dot>enabled</Badge></div>
              <div className="spread"><span className="muted">Allowed domains</span><span className="mono">acme.com, acme.io</span></div>
              <div className="spread"><span className="muted">MFA</span><Badge tone="success" dot>required</Badge></div>
              <Button variant="outline" size="sm" icon="settings">Configure</Button>
            </div>
          </Card>
        </div>
      )}

      {tab === "flags" && <FeatureFlags />}
      {tab === "quotas" && <Quotas />}
      {tab === "hitl" && <HITLPolicies />}
      {tab === "members" && <Members />}
      {tab === "danger" && <DangerZone />}
    </div>
  );
};

const FeatureFlags = () => (
  <Card title="Feature flags" subtitle="Tenant-scoped overrides">
    <table className="table">
      <thead><tr><th>Flag</th><th>Description</th><th>Default</th><th>Tenant override</th></tr></thead>
      <tbody>
        {[
          { k: "subagent.fork.enabled", desc: "Allow concurrent fork mode", def: "on", on: true },
          { k: "subagent.max_depth", desc: "Maximum subagent recursion depth", def: "5", on: 5, ctl: "num" },
          { k: "memory.long_term_write", desc: "Allow writes to user/tenant memory", def: "on", on: true },
          { k: "tool.sandbox_full", desc: "Permit FULL_SANDBOX tool runs", def: "off", on: false },
          { k: "hitl.escalate_to_teams", desc: "Mirror HITL events to MS Teams", def: "on", on: true },
          { k: "verification.required", desc: "Block tool output without verification", def: "on", on: true },
          { k: "loop.max_iterations", desc: "Hard ceiling on loop turns", def: "30", on: 30, ctl: "num" },
          { k: "streaming.thinking", desc: "Stream thinking blocks to client", def: "on", on: true },
        ].map(f => (
          <tr key={f.k}>
            <td className="mono" style={{ fontSize: 12 }}>{f.k}</td>
            <td className="subtle" style={{ fontSize: 12 }}>{f.desc}</td>
            <td><Badge>{f.def}</Badge></td>
            <td>
              {f.ctl === "num"
                ? <input className="input mono" style={{ width: 80, fontSize: 12 }} defaultValue={f.on} />
                : <Switch on={f.on} />}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const Quotas = () => (
  <div className="grid-main">
    <Card title="Usage quotas">
      <div className="col" style={{ gap: 14 }}>
        {[
          { k: "Tokens / month", used: 4.2, max: 10, unit: "M", pct: 42 },
          { k: "Runs / day", used: 14820, max: 50000, unit: "", pct: 30 },
          { k: "Subagents concurrent", used: 3, max: 20, unit: "", pct: 15 },
          { k: "Memory entries", used: 18200, max: 100000, unit: "", pct: 18 },
          { k: "Audit storage", used: 240, max: 1024, unit: " MB", pct: 23 },
        ].map(q => (
          <div key={q.k}>
            <div className="spread" style={{ marginBottom: 4 }}>
              <span style={{ fontSize: 12.5 }}>{q.k}</span>
              <span className="mono tnum" style={{ fontSize: 11.5 }}>
                <span style={{ color: "var(--fg)" }}>{q.used.toLocaleString()}</span>{q.unit}
                <span className="subtle"> / {q.max.toLocaleString()}{q.unit}</span>
              </span>
            </div>
            <div className="bar-track"><span style={{ width: q.pct + "%" }} /></div>
          </div>
        ))}
      </div>
    </Card>
    <Card title="Rate limits">
      <div className="col" style={{ gap: 10, fontSize: 12 }}>
        <div className="spread"><span className="muted">API requests</span><span className="mono">100 / min</span></div>
        <div className="spread"><span className="muted">Tool calls</span><span className="mono">1,000 / min</span></div>
        <div className="spread"><span className="muted">SSE connections</span><span className="mono">50 concurrent</span></div>
        <Button variant="outline" size="sm">Request increase</Button>
      </div>
    </Card>
  </div>
);

const HITLPolicies = () => (
  <Card title="HITL policies" subtitle="Per-tool · risk-tiered · escalation routing">
    <table className="table">
      <thead><tr><th>Risk tier</th><th>Default policy</th><th>SLA</th><th>Approvers</th><th>Off-platform</th></tr></thead>
      <tbody>
        {[
          { risk: "critical", policy: "always_ask", sla: "5m", approvers: "@platform-l2 + @on-call-mgr", off: ["Teams", "Email"] },
          { risk: "high", policy: "always_ask", sla: "15m", approvers: "@platform-l2", off: ["Teams"] },
          { risk: "medium", policy: "ask_once", sla: "60m", approvers: "@platform-l1", off: [] },
          { risk: "low", policy: "auto", sla: "—", approvers: "—", off: [] },
        ].map(p => (
          <tr key={p.risk}>
            <td><span className="row" style={{ gap: 6 }}><span className={`sev-dot sev-${p.risk}`} /><span style={{ fontSize: 12, textTransform: "capitalize" }}>{p.risk}</span></span></td>
            <td><Badge tone={p.policy === "auto" ? "success" : p.policy === "ask_once" ? "info" : "warning"}>{p.policy}</Badge></td>
            <td className="mono">{p.sla}</td>
            <td className="mono subtle" style={{ fontSize: 11.5 }}>{p.approvers}</td>
            <td>
              <div className="row" style={{ gap: 4 }}>
                {p.off.length ? p.off.map(c => <Badge key={c}>{c}</Badge>) : <span className="subtle">—</span>}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const Members = () => (
  <Card title="Members" subtitle="8 active · 0 invitations" actions={<Button variant="primary" size="sm" icon="plus">Invite</Button>} bodyClass="flush">
    <table className="table">
      <thead><tr><th>Member</th><th>Email</th><th>Role</th><th>Last active</th><th></th></tr></thead>
      <tbody>
        {[
          { n: "Jamie Liu", e: "jamie@acme.com", r: "operator", a: "now", c: 250 },
          { n: "Priya Mishra", e: "priya@acme.com", r: "compliance", a: "8m ago", c: 350 },
          { n: "Sam Wong", e: "sam@acme.com", r: "operator", a: "2h ago", c: 210 },
          { n: "Yui Kato", e: "yui@acme.com", r: "operator", a: "yesterday", c: 30 },
          { n: "Dan O'Brien", e: "dan@acme.com", r: "admin", a: "3 days ago", c: 290 },
          { n: "Rae Tan", e: "rae@acme.com", r: "operator", a: "1 week ago", c: 340 },
          { n: "Ben Park", e: "ben@acme.com", r: "operator", a: "2 weeks ago", c: 80 },
          { n: "Mira Habib", e: "mira@acme.com", r: "admin", a: "1 month ago", c: 10 },
        ].map(m => (
          <tr key={m.e}>
            <td>
              <div className="row" style={{ gap: 8 }}>
                <span style={{ width: 24, height: 24, borderRadius: "50%", background: `linear-gradient(135deg, oklch(0.65 0.15 ${m.c}), oklch(0.5 0.16 ${(m.c + 60) % 360}))`, color: "white", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 600 }}>{m.n.split(" ").map(x => x[0]).join("")}</span>
                <span style={{ fontSize: 12.5 }}>{m.n}</span>
              </div>
            </td>
            <td className="mono subtle" style={{ fontSize: 11.5 }}>{m.e}</td>
            <td><Badge tone={m.r === "admin" ? "primary" : m.r === "compliance" ? "memory" : ""}>{m.r}</Badge></td>
            <td className="subtle" style={{ fontSize: 11.5 }}>{m.a}</td>
            <td><Icon name="dots" size={14} className="subtle" /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const DangerZone = () => (
  <Card title="Danger zone" className="" actions={null}>
    <div className="col" style={{ gap: 20, maxWidth: 540 }}>
      {[
        { k: "Suspend tenant", v: "Block all new sessions and tool calls. Existing sessions complete.", btn: "Suspend" },
        { k: "Rotate all API keys", v: "Invalidate every active key. Operators must re-issue.", btn: "Rotate" },
        { k: "Tombstone all PII", v: "GDPR Art. 17. Memory entries marked subject-erased; audit chain preserves hashes.", btn: "Tombstone" },
        { k: "Delete tenant", v: "Permanent. Cannot be undone. WORM audit retained 7 years per compliance.", btn: "Delete" },
      ].map(z => (
        <div key={z.k} style={{ padding: 14, border: "1px solid var(--border)", borderLeft: `2px solid var(--danger)`, borderRadius: "var(--radius)" }}>
          <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>{z.k}</div>
          <div className="muted" style={{ fontSize: 12, marginBottom: 10 }}>{z.v}</div>
          <Button variant="danger" size="sm">{z.btn}</Button>
        </div>
      ))}
    </div>
  </Card>
);

Object.assign(window, { SlaPage, CostPage, TenantsPage, TenantSettings });
