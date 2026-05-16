/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, SevDot */
const { useState: useTs, useMemo: useMTs, useEffect: useETs } = React;

// ============ 24 business tools across 5 domains ============
const TOOLS = [
  // Patrol domain (4)
  { id: "patrol_schedule", domain: "patrol", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 412, p95: 220, desc: "Schedule a recurring patrol with cron + scope.", since: "v2.0.0" },
  { id: "patrol_get_results", domain: "patrol", type: "REST", method: "GET", sandbox: "NONE", risk: "low", policy: "auto", calls24: 8420, p95: 80, desc: "Read patrol run results for the last N hours.", since: "v2.0.0" },
  { id: "patrol_acknowledge", domain: "patrol", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "low", policy: "auto", calls24: 184, p95: 110, desc: "Acknowledge a failed patrol run; suppresses pages.", since: "v2.0.0" },
  { id: "patrol_pause", domain: "patrol", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 22, p95: 90, desc: "Temporarily pause a patrol schedule with a TTL.", since: "v2.1.0" },

  // Event Correlation (5)
  { id: "events_subscribe", domain: "correlate", type: "SSE", method: "GET", sandbox: "NONE", risk: "low", policy: "auto", calls24: 9120, p95: 12, desc: "Subscribe to event stream filtered by service/severity.", since: "v1.8.0" },
  { id: "correlate_window", domain: "correlate", type: "REST", method: "POST", sandbox: "NONE", risk: "low", policy: "auto", calls24: 2840, p95: 280, desc: "Cluster events within a time window using selected features.", since: "v2.0.0" },
  { id: "incident_open", domain: "correlate", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "high", policy: "always_ask", calls24: 18, p95: 320, desc: "Open a new incident from clustered events.", since: "v2.0.0" },
  { id: "anomaly_detect", domain: "correlate", type: "REST", method: "POST", sandbox: "NONE", risk: "low", policy: "auto", calls24: 4820, p95: 410, desc: "Run anomaly detection over a metric series.", since: "v2.2.0" },
  { id: "severity_classify", domain: "correlate", type: "REST", method: "POST", sandbox: "NONE", risk: "low", policy: "auto", calls24: 1820, p95: 64, desc: "Classify an incident severity (P0/P1/P2/P3).", since: "v2.0.0" },

  // RCA (5)
  { id: "incident_get", domain: "rca", type: "REST", method: "GET", sandbox: "NONE", risk: "low", policy: "auto", calls24: 6420, p95: 92, desc: "Fetch incident details + timeline.", since: "v1.0.0" },
  { id: "metrics.query", domain: "rca", type: "REST", method: "GET", sandbox: "NONE", risk: "low", policy: "auto", calls24: 12820, p95: 210, desc: "Query time-series metrics from observability store.", since: "v1.0.0" },
  { id: "log.tail", domain: "rca", type: "SSE", method: "GET", sandbox: "NONE", risk: "low", policy: "auto", calls24: 3820, p95: 1100, desc: "Tail structured logs from a service / namespace.", since: "v1.4.0" },
  { id: "log.grep", domain: "rca", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 1240, p95: 1800, desc: "Run a bounded grep across log archive.", since: "v1.4.0" },
  { id: "evidence.attach", domain: "rca", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "auto", calls24: 880, p95: 140, desc: "Attach metrics / logs / artifacts as evidence to RCA.", since: "v2.0.0" },

  // Compliance Audit (5)
  { id: "audit_query_logs", domain: "audit", type: "SQL", method: "READ", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 420, p95: 380, desc: "Query the WORM audit log table with RLS enforcement.", since: "v1.6.0" },
  { id: "audit.export_chain", domain: "audit", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "high", policy: "always_ask", calls24: 18, p95: 4200, desc: "Export the Merkle chain segment for offline verification.", since: "v2.0.0" },
  { id: "evidence.bundle", domain: "audit", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 84, p95: 2100, desc: "Bundle evidence artifacts + audit entries into a signed zip.", since: "v2.0.0" },
  { id: "compliance_check", domain: "audit", type: "REST", method: "POST", sandbox: "NONE", risk: "low", policy: "auto", calls24: 320, p95: 480, desc: "Validate a control against framework (PCI/SOC2/ISO27001).", since: "v2.1.0" },
  { id: "redact_pii", domain: "audit", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "high", policy: "always_ask", calls24: 12, p95: 220, desc: "Issue a GDPR tombstone for a subject across memory scopes.", since: "v2.2.0" },

  // Incident Management (5)
  { id: "k8s.set_env", domain: "incident", type: "REST", method: "POST", sandbox: "FULL_SANDBOX", risk: "high", policy: "always_ask", calls24: 8, p95: 1200, desc: "Update env vars on a Kubernetes deployment.", since: "v1.4.0" },
  { id: "k8s.rollback", domain: "incident", type: "REST", method: "POST", sandbox: "FULL_SANDBOX", risk: "critical", policy: "always_ask", calls24: 2, p95: 5400, desc: "Roll back a Kubernetes deployment to a prior revision.", since: "v1.4.0" },
  { id: "page_oncall", domain: "incident", type: "Slack", method: "POST", sandbox: "RESTRICTED", risk: "high", policy: "always_ask", calls24: 22, p95: 280, desc: "Page the on-call engineer via PagerDuty / Slack.", since: "v1.0.0" },
  { id: "change.create", domain: "incident", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "medium", policy: "ask_once", calls24: 18, p95: 320, desc: "Create a change request in the CMDB.", since: "v2.0.0" },
  { id: "cdn.purge", domain: "incident", type: "REST", method: "POST", sandbox: "RESTRICTED", risk: "high", policy: "always_ask", calls24: 6, p95: 1800, desc: "Purge CDN cache by URL pattern or tag.", since: "v2.1.0" },
];

const DOMAIN_INFO = {
  patrol:    { name: "Patrol", icon: "refresh", tone: "var(--tool)" },
  correlate: { name: "Event Correlation", icon: "branch", tone: "var(--thinking)" },
  rca:       { name: "Root Cause Analysis", icon: "thinking", tone: "var(--primary)" },
  audit:     { name: "Compliance Audit", icon: "audit", tone: "var(--memory)" },
  incident:  { name: "Incident Management", icon: "warn", tone: "var(--danger)" },
};

const SANDBOX_INFO = {
  NONE:          { tone: "success", desc: "Read-only; no isolation needed." },
  RESTRICTED:    { tone: "warning", desc: "Bounded I/O · network allowlist · 30s timeout." },
  FULL_SANDBOX:  { tone: "danger",  desc: "Process-level isolation · resource quotas · audit-gated." },
};

// ============ /tools — ToolSpec admin ============
const ToolsAdmin = () => {
  const [selected, setSelected] = useTs("k8s.set_env");
  const [domain, setDomain] = useTs("all");
  const [q, setQ] = useTs("");

  const filtered = TOOLS.filter(t =>
    (domain === "all" || t.domain === domain) &&
    (!q || t.id.toLowerCase().includes(q.toLowerCase()))
  );
  const active = TOOLS.find(t => t.id === selected) || TOOLS[0];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Tool Registry</div>
          <div className="page-sub">
            24 ToolSpecs · LLM-neutral schema · sandbox + HITL bound per tool
            <span className="route-pill">/tools</span>
            <Badge tone="warning">platform admin</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">Open registry repo</Button>
          <Button variant="outline" size="sm" icon="download">Export OpenAPI</Button>
          <Button variant="primary" size="sm" icon="plus">Register tool</Button>
        </div>
      </div>

      <div className="row" style={{ gap: 4, marginBottom: 14, flexWrap: "wrap" }}>
        <button
          onClick={() => setDomain("all")}
          className="badge"
          style={{
            cursor: "pointer", fontSize: 11.5,
            background: domain === "all" ? "var(--primary-soft)" : "var(--bg-2)",
            color: domain === "all" ? "var(--primary)" : "var(--fg-muted)",
            borderColor: domain === "all" ? "var(--primary-soft-2)" : "var(--border)",
          }}>All <span className="subtle">· {TOOLS.length}</span></button>
        {Object.entries(DOMAIN_INFO).map(([k, d]) => {
          const count = TOOLS.filter(t => t.domain === k).length;
          return (
            <button
              key={k}
              onClick={() => setDomain(k)}
              className="badge"
              style={{
                cursor: "pointer", fontSize: 11.5,
                background: domain === k ? `oklch(from ${d.tone} l c h / 0.16)` : "var(--bg-2)",
                color: domain === k ? d.tone : "var(--fg-muted)",
                borderColor: domain === k ? `oklch(from ${d.tone} l c h / 0.4)` : "var(--border)",
              }}>
              <Icon name={d.icon} size={11} />
              {d.name} <span className="subtle">· {count}</span>
            </button>
          );
        })}
        <div className="grow" />
        <div style={{ position: "relative", maxWidth: 220, minWidth: 180 }}>
          <Icon name="search" size={13} style={{ position: "absolute", left: 9, top: 8, color: "var(--fg-subtle)" }} />
          <input className="input" style={{ paddingLeft: 28, fontSize: 12 }} placeholder="Filter tools…" value={q} onChange={e => setQ(e.target.value)} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14 }}>
        <Card title={`${filtered.length} tools`} subtitle="Click a row to inspect / edit" bodyClass="flush">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Sandbox</th>
                <th>Risk</th>
                <th>HITL</th>
                <th style={{ textAlign: "right" }}>Calls · 24h</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => {
                const d = DOMAIN_INFO[t.domain];
                return (
                  <tr key={t.id} onClick={() => setSelected(t.id)}
                    style={{ background: selected === t.id ? "oklch(from var(--primary) l c h / 0.10)" : undefined }}>
                    <td>
                      <div className="row" style={{ gap: 8 }}>
                        <span style={{ width: 5, height: 5, borderRadius: "50%", background: d.tone }} />
                        <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{t.id}</span>
                      </div>
                      <div className="subtle" style={{ fontSize: 11, marginTop: 2, paddingLeft: 13, maxWidth: 360, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.desc}</div>
                    </td>
                    <td>
                      <Badge tone="tool">{t.type} <span className="subtle">· {t.method}</span></Badge>
                    </td>
                    <td><Badge tone={SANDBOX_INFO[t.sandbox].tone}>{t.sandbox}</Badge></td>
                    <td><RiskBadge level={t.risk} /></td>
                    <td><Badge tone={t.policy === "auto" ? "success" : t.policy === "ask_once" ? "info" : "warning"}>{t.policy}</Badge></td>
                    <td className="mono tnum" style={{ textAlign: "right" }}>{t.calls24.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>

        <ToolDetail tool={active} />
      </div>
    </div>
  );
};

const ToolDetail = ({ tool }) => {
  const [tab, setTab] = useTs("spec");
  const d = DOMAIN_INFO[tool.domain];
  return (
    <Card
      title={<span className="row" style={{ gap: 8 }}>
        <Icon name={d.icon} size={14} style={{ color: d.tone }} />
        <span className="mono">{tool.id}</span>
        <Badge mono>{tool.since}</Badge>
      </span>}
      subtitle={tool.desc}
      bodyClass="flush"
      actions={<div className="row"><Button variant="ghost" size="sm" icon="play">Test</Button><Button variant="outline" size="sm" icon="copy" /></div>}
    >
      <div style={{ padding: "0 16px" }}>
        <Tabs
          value={tab} onChange={setTab}
          items={[
            { id: "spec", label: "Spec" },
            { id: "sandbox", label: "Sandbox & HITL" },
            { id: "policy", label: "Policy" },
            { id: "history", label: "History" },
          ]}
        />
      </div>
      <div className="card-body">
        {tab === "spec" && <ToolSpec tool={tool} />}
        {tab === "sandbox" && <ToolSandbox tool={tool} />}
        {tab === "policy" && <ToolPolicy tool={tool} />}
        {tab === "history" && <ToolHistory tool={tool} />}
      </div>
    </Card>
  );
};

const ToolSpec = ({ tool }) => {
  const schema = `{
  "$schema": "ipa://toolspec/v2",
  "name": "${tool.id}",
  "version": "${tool.since}",
  "domain": "${tool.domain}",
  "transport": {
    "type": "${tool.type}",
    "method": "${tool.method}",
    "endpoint": "{{tenant.api_root}}/v1/${tool.id.replace(/\./g, "/")}",
    "timeout_ms": 30000
  },
  "input_schema": {
    "type": "object",
    "required": ${tool.id === "k8s.set_env" ? '["namespace", "deployment", "env"]' : '["query"]'},
    "properties": {${tool.id === "k8s.set_env" ? `
      "namespace": { "type": "string", "pattern": "^[a-z0-9-]+$" },
      "deployment": { "type": "string" },
      "env": { "type": "object", "additionalProperties": { "type": "string" } },
      "rolling": { "type": "boolean", "default": true }` : `
      "query": { "type": "string" },
      "window": { "type": "string", "pattern": "^[0-9]+(s|m|h|d)$" }`}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "ok": { "type": "boolean" },
      "data": { "type": "object" },
      "audit_id": { "type": "string" }
    }
  },
  "redact_paths": ["input.env", "output.data.secrets"],
  "provider_neutral": true
}`;
  return (
    <div className="col" style={{ gap: 12 }}>
      <Field label="ToolSpec (JSON · v2)" help={<span>This schema is consumed by every provider adapter. <a href="#" style={{ color: "var(--primary)" }}>See provider mapping →</a></span>}>
        <pre style={{ margin: 0, padding: 12, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.55, color: "var(--fg)", maxHeight: 320, overflowY: "auto" }}>{schema}</pre>
      </Field>
      <div className="row" style={{ gap: 8 }}>
        <Button variant="outline" size="sm" icon="check">Validate</Button>
        <Button variant="outline" size="sm" icon="play">Dry-run</Button>
        <Button variant="outline" size="sm" icon="copy">Copy</Button>
      </div>
    </div>
  );
};

const ToolSandbox = ({ tool }) => {
  const s = SANDBOX_INFO[tool.sandbox];
  return (
    <div className="col" style={{ gap: 14 }}>
      <Field label="Sandbox level" help={s.desc}>
        <div className="row" style={{ gap: 6 }}>
          {["NONE", "RESTRICTED", "FULL_SANDBOX"].map(lvl => (
            <button key={lvl} className="badge" style={{
              cursor: "pointer", padding: "5px 10px", fontSize: 11.5,
              background: tool.sandbox === lvl ? `oklch(from var(--${SANDBOX_INFO[lvl].tone === "success" ? "success" : SANDBOX_INFO[lvl].tone === "warning" ? "warning" : "danger"}) l c h / 0.2)` : "var(--bg-2)",
              color: tool.sandbox === lvl ? `var(--${SANDBOX_INFO[lvl].tone === "success" ? "success" : SANDBOX_INFO[lvl].tone === "warning" ? "warning" : "danger"})` : "var(--fg-muted)",
              borderColor: tool.sandbox === lvl ? `var(--${SANDBOX_INFO[lvl].tone === "success" ? "success" : SANDBOX_INFO[lvl].tone === "warning" ? "warning" : "danger"})` : "var(--border)",
            }}>{lvl}</button>
          ))}
        </div>
      </Field>
      <div className="thin-rule" />
      <div className="col" style={{ gap: 8, fontSize: 12 }}>
        <div className="spread"><span className="muted">Network allowlist</span><span className="mono">api.acme.io · {tool.domain === "incident" ? "k8s.acme.io" : "*"}.acme.io</span></div>
        <div className="spread"><span className="muted">Timeout</span><span className="mono">30,000 ms</span></div>
        <div className="spread"><span className="muted">Memory limit</span><span className="mono">128 MB</span></div>
        <div className="spread"><span className="muted">CPU limit</span><span className="mono">500 mCPU</span></div>
        <div className="spread"><span className="muted">Egress (sniffing)</span><Badge tone="success" dot>monitored</Badge></div>
      </div>
      <div className="thin-rule" />
      <Field label="HITL policy by risk tier" help="Override per-tool; default inherits from tenant policy.">
        <div className="col" style={{ gap: 5 }}>
          {[
            { lvl: "low", policy: "auto" },
            { lvl: "medium", policy: "ask_once" },
            { lvl: "high", policy: "always_ask" },
            { lvl: "critical", policy: "always_ask" },
          ].map(r => (
            <div key={r.lvl} className="spread" style={{ fontSize: 11.5 }}>
              <span className="row" style={{ gap: 6 }}><SevDot level={r.lvl} /><span style={{ textTransform: "capitalize" }}>{r.lvl}</span></span>
              <Badge tone={r.policy === "auto" ? "success" : r.policy === "ask_once" ? "info" : "warning"}>{r.policy}</Badge>
            </div>
          ))}
        </div>
      </Field>
    </div>
  );
};

const ToolPolicy = ({ tool }) => (
  <div className="col" style={{ gap: 12 }}>
    <Field label="Risk tier" help="Determines default HITL policy via tenant matrix.">
      <div className="row" style={{ gap: 6 }}>
        {["low", "medium", "high", "critical"].map(lvl => (
          <button key={lvl} className="badge" style={{
            cursor: "pointer", padding: "5px 10px", fontSize: 11.5,
            background: tool.risk === lvl ? `oklch(from var(--risk-${lvl}) l c h / 0.2)` : "var(--bg-2)",
            color: tool.risk === lvl ? `var(--risk-${lvl})` : "var(--fg-muted)",
            borderColor: tool.risk === lvl ? `var(--risk-${lvl})` : "var(--border)",
          }}><SevDot level={lvl} /> {lvl}</button>
        ))}
      </div>
    </Field>
    <Field label="HITL policy" help="auto: no prompt · ask_once: prompt first time per session · always_ask: every invocation">
      <div className="row" style={{ gap: 6 }}>
        {["auto", "ask_once", "always_ask"].map(p => (
          <button key={p} className="badge" style={{
            cursor: "pointer", padding: "5px 10px", fontSize: 11.5,
            background: tool.policy === p ? "var(--primary-soft)" : "var(--bg-2)",
            color: tool.policy === p ? "var(--primary)" : "var(--fg-muted)",
            borderColor: tool.policy === p ? "var(--primary)" : "var(--border)",
          }}>{p}</button>
        ))}
      </div>
    </Field>
    <Field label="Approvers" help="Required for ask_once and always_ask.">
      <input className="input mono" defaultValue={tool.risk === "critical" ? "@platform-l2 + @on-call-mgr" : tool.risk === "high" ? "@platform-l2" : "@platform-l1"} />
    </Field>
    <Field label="Off-platform notifications">
      <div className="row" style={{ gap: 8 }}>
        <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" defaultChecked={tool.risk === "high" || tool.risk === "critical"} /> Teams</label>
        <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" defaultChecked={tool.risk === "critical"} /> Email</label>
        <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" /> PagerDuty</label>
      </div>
    </Field>
    <Field label="Tripwires" help="Static guardrails that block invocations matching pattern.">
      <div className="kbar">
        <Badge tone="danger">cross-tenant scope</Badge>
        <Badge tone="danger">PII in input</Badge>
        {tool.id === "k8s.set_env" && <Badge tone="warning">prod namespace</Badge>}
      </div>
    </Field>
  </div>
);

const ToolHistory = ({ tool }) => (
  <div className="col" style={{ gap: 0 }}>
    <div className="subtle" style={{ fontSize: 11, marginBottom: 8, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Recent changes</div>
    {[
      { ver: "v2.2.1", at: "3d ago", by: "@platform-eng", note: "Tightened input pattern: namespace must match ^[a-z0-9-]+$" },
      { ver: "v2.2.0", at: "1w ago", by: "@platform-eng", note: "Promoted from RESTRICTED → FULL_SANDBOX after sandbox audit." },
      { ver: "v2.1.0", at: "1mo ago", by: "@security", note: "Added redact_paths for input.env (PII leak prevention)." },
      { ver: "v2.0.0", at: "2mo ago", by: "@platform-eng", note: "Migrated to ToolSpec v2 schema (provider-neutral)." },
    ].map((c, i) => (
      <div key={i} style={{ padding: "10px 0", borderTop: i ? "1px solid var(--border)" : "none" }}>
        <div className="row" style={{ gap: 6 }}>
          <Badge mono>{c.ver}</Badge>
          <span className="subtle" style={{ fontSize: 11 }}>{c.at}</span>
          <span className="mono subtle" style={{ fontSize: 11, marginLeft: "auto" }}>{c.by}</span>
        </div>
        <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>{c.note}</div>
      </div>
    ))}
    <div className="thin-rule" />
    <div className="subtle" style={{ fontSize: 11, marginBottom: 8, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Invocation stats · 7 days</div>
    <div className="row" style={{ gap: 6, alignItems: "flex-end", height: 60 }}>
      {[14, 22, 18, 28, 32, 26, 38].map((v, i) => (
        <div key={i} className="grow" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
          <div style={{ height: v * 1.4, width: "100%", background: "var(--primary)", borderRadius: 3 }} />
          <span className="subtle mono" style={{ fontSize: 9 }}>{["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i]}</span>
        </div>
      ))}
    </div>
  </div>
);

Object.assign(window, { ToolsAdmin });
