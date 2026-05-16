/* global React, Icon, Button, Badge, Card, Tabs, Field, Switch, RiskBadge, SevDot */
const { useState: useAg } = React;

// ===================================================================
// /orchestrator — top-level agent configuration
// Backed by backend/src/agent_harness/orchestrator_loop/loop.py
// ===================================================================
const Orchestrator = () => {
  const [tab, setTab] = useAg("config");
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="row" style={{ gap: 10, marginBottom: 6 }}>
            <div className="brand-mark" style={{ width: 32, height: 32 }} />
            <div>
              <div className="row" style={{ gap: 8 }}>
                <span className="mono" style={{ fontSize: 20, fontWeight: 600 }}>orchestrator-main</span>
                <Badge tone="primary">v3.4.1</Badge>
                <Badge dot tone="success">live</Badge>
              </div>
              <div className="page-sub">
                Range 1 · TAO/ReAct loop · dispatches 4 subagent modes (fork / teammate / handoff / as_tool)
                <span className="route-pill">/orchestrator</span>
              </div>
            </div>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="play">Test in Chat</Button>
          <Button variant="outline" size="sm" icon="git">View in repo</Button>
          <Button variant="primary" size="sm" icon="bolt">Deploy</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Sessions · 24h" value="2,847" delta="+12%" deltaDir="up" />
        <Stat label="Avg loop turns" value="4.2" delta="+0.1" deltaDir="down" />
        <Stat label="Subagent spawns · 24h" value="412" delta="+8" deltaDir="up" />
        <Stat label="p95 session" value="18.4" unit="s" delta="-2s" deltaDir="up" />
      </div>

      <Tabs
        value={tab} onChange={setTab}
        items={[
          { id: "config",    label: "Config" },
          { id: "prompt",    label: "System Prompt" },
          { id: "tools",     label: "Tools",    count: 18 },
          { id: "subagents", label: "Subagents", count: 6 },
          { id: "budgets",   label: "Budgets" },
          { id: "policies",  label: "Policies" },
        ]}
      />

      {tab === "config" && <OrchestratorConfig />}
      {tab === "prompt" && <OrchestratorPrompt />}
      {tab === "tools" && <OrchestratorTools />}
      {tab === "subagents" && <OrchestratorSubagents />}
      {tab === "budgets" && <OrchestratorBudgets />}
      {tab === "policies" && <OrchestratorPolicies />}
    </div>
  );
};

const OrchestratorConfig = () => (
  <div className="grid-main">
    <Card title="Core settings">
      <div className="col" style={{ gap: 14, maxWidth: 540 }}>
        <Field label="Display name"><input className="input" defaultValue="orchestrator-main" /></Field>
        <Field label="Primary model" help="LLM-neutral; concrete provider chosen by adapter">
          <select className="select" defaultValue="claude-haiku-4-5">
            <option>claude-haiku-4-5</option>
            <option>claude-sonnet-4-5</option>
            <option>claude-opus-4-1</option>
            <option>gpt-5</option>
            <option>azure-openai-gpt-4o</option>
          </select>
        </Field>
        <Field label="Fallback model" help="Used when primary circuit breaker opens">
          <select className="select" defaultValue="claude-sonnet-4-5"><option>claude-sonnet-4-5</option><option>claude-opus-4-1</option></select>
        </Field>
        <div className="grid-2">
          <Field label="Temperature"><input className="input" defaultValue="0.2" /></Field>
          <Field label="Top P"><input className="input" defaultValue="0.95" /></Field>
        </div>
        <Field label="Max thinking tokens / turn"><input className="input" defaultValue="2048" /></Field>
        <Field label="Termination policy">
          <select className="select" defaultValue="end_turn"><option>end_turn (default)</option><option>max_turns</option><option>budget_exhausted</option></select>
        </Field>
      </div>
    </Card>
    <div className="col" style={{ gap: 14 }}>
      <Card title="Memory access" subtitle="What scopes orchestrator can touch">
        <div className="col" style={{ gap: 10, fontSize: 12.5 }}>
          {["system", "tenant", "role", "user", "session"].map(s => (
            <div key={s} className="spread">
              <span className="mono">{s}</span>
              <select className="select" style={{ width: 110, fontSize: 11.5 }} defaultValue={s === "system" ? "read" : "write"}>
                <option>none</option><option>read</option><option>write</option>
              </select>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Verification" subtitle="Range 7 settings">
        <div className="col" style={{ gap: 8, fontSize: 12 }}>
          <div className="row"><Switch on={true} /><span>Require verification before write tools</span></div>
          <div className="row"><Switch on={true} /><span>Block on failed verification</span></div>
          <div className="row"><Switch on={false} /><span>Skip verification for risk=low tools</span></div>
        </div>
      </Card>
    </div>
  </div>
);

const OrchestratorPrompt = () => (
  <div className="grid-main">
    <Card title="System prompt" subtitle="Variables wrapped in {{double-braces}}" actions={
      <div className="row">
        <Badge tone="primary">v3.4.1</Badge>
        <Button variant="ghost" size="sm" icon="git">History</Button>
        <Button variant="outline" size="sm" icon="play">Test</Button>
      </div>
    }>
      <textarea className="textarea" rows="20" defaultValue={`# Role
You are the orchestrator agent for IPA Platform V2 — an enterprise AI operations platform for {{tenant_name}}.

# Goal
Receive operator requests, plan a sequence of actions, dispatch to specialized subagents when the task is complex, and produce a verified outcome with HITL gating for any write action.

# Available subagents (call as_tool or fork)
- log-scanner — tail + grep logs from a service
- dep-checker — health-probe downstream services
- metrics-pull — query observability backend
- evidence-collector — assemble RCA evidence bundle
- compliance-auditor — answer audit queries with citations

# Tool use policy
- Read tools: auto-call when needed.
- Write tools: ALWAYS request HITL approval first (see range 9).
- If a tool fails 3× with TRANSIENT class, escalate to a teammate subagent.

# Output discipline
- Always emit a short reasoning trace.
- Final answer must cite tool calls + memory reads as evidence.

# Constraints
- Never promise timelines.
- Never expose internal tooling names to non-operator roles.
- Always respect tenant_id boundary; cross-tenant access is a tripwire.`} />
    </Card>
    <div className="col" style={{ gap: 14 }}>
      <Card title="Variables">
        <div className="col" style={{ gap: 8, fontSize: 12 }}>
          {[
            { k: "tenant_name", v: "string", req: true },
            { k: "operator_role", v: "enum", req: true },
            { k: "locale", v: "string", req: false },
            { k: "time_zone", v: "string", req: false },
          ].map(x => (
            <div key={x.k} className="spread">
              <span className="mono" style={{ fontSize: 11.5 }}>{`{{${x.k}}}`}</span>
              <div className="row" style={{ gap: 4 }}>
                <Badge>{x.v}</Badge>
                {x.req && <Badge tone="warning">required</Badge>}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  </div>
);

const OrchestratorTools = () => (
  <Card title="Tools attached to orchestrator" subtitle="18 of 24 enabled · order ≈ selection bias" actions={
    <Button variant="primary" size="sm" icon="plus" onClick={() => { location.hash = "tools"; }}>Open registry</Button>
  } bodyClass="flush">
    <table className="table">
      <thead><tr><th>Tool</th><th>Domain</th><th>Risk</th><th>Sandbox</th><th>Enabled</th></tr></thead>
      <tbody>
        {[
          { id: "incidents.list", domain: "rca", risk: "low", sandbox: "NONE", on: true },
          { id: "metrics.query", domain: "rca", risk: "low", sandbox: "NONE", on: true },
          { id: "log.tail", domain: "rca", risk: "low", sandbox: "NONE", on: true },
          { id: "log.grep", domain: "rca", risk: "medium", sandbox: "RESTRICTED", on: true },
          { id: "evidence.attach", domain: "rca", risk: "medium", sandbox: "RESTRICTED", on: true },
          { id: "audit_query_logs", domain: "audit", risk: "medium", sandbox: "RESTRICTED", on: true },
          { id: "redact_pii", domain: "audit", risk: "high", sandbox: "RESTRICTED", on: false },
          { id: "page_oncall", domain: "incident", risk: "high", sandbox: "RESTRICTED", on: true },
          { id: "k8s.set_env", domain: "incident", risk: "high", sandbox: "FULL_SANDBOX", on: false },
          { id: "k8s.rollback", domain: "incident", risk: "critical", sandbox: "FULL_SANDBOX", on: false },
        ].map(t => (
          <tr key={t.id}>
            <td className="mono" style={{ fontSize: 12 }}>{t.id}</td>
            <td><Badge>{t.domain}</Badge></td>
            <td><RiskBadge level={t.risk} /></td>
            <td><Badge tone={t.sandbox === "NONE" ? "success" : t.sandbox === "RESTRICTED" ? "warning" : "danger"}>{t.sandbox}</Badge></td>
            <td><Switch on={t.on} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const OrchestratorSubagents = () => (
  <Card title="Subagents this orchestrator can dispatch" subtitle="Pick from registry · per-subagent mode + budget" actions={
    <Button variant="primary" size="sm" icon="plus" onClick={() => { location.hash = "subagents"; }}>Open registry</Button>
  } bodyClass="flush">
    <table className="table">
      <thead><tr><th>Subagent</th><th>Allowed modes</th><th>Max tokens</th><th>Max concurrent</th><th>Enabled</th></tr></thead>
      <tbody>
        {[
          { id: "log-scanner",        modes: ["fork", "as_tool"], max_tok: 4000, max_conc: 3, on: true },
          { id: "dep-checker",        modes: ["fork", "as_tool"], max_tok: 3000, max_conc: 3, on: true },
          { id: "metrics-pull",       modes: ["fork", "as_tool"], max_tok: 2000, max_conc: 5, on: true },
          { id: "evidence-collector", modes: ["as_tool"], max_tok: 8000, max_conc: 1, on: true },
          { id: "compliance-auditor", modes: ["handoff", "teammate"], max_tok: 16000, max_conc: 1, on: true },
          { id: "postmortem-writer",  modes: ["handoff"], max_tok: 8000, max_conc: 1, on: false },
        ].map(s => (
          <tr key={s.id}>
            <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{s.id}</td>
            <td>
              <div className="row" style={{ gap: 4 }}>
                {s.modes.map(m => <Badge key={m} tone={m === "fork" ? "thinking" : m === "as_tool" ? "tool" : m === "handoff" ? "info" : "memory"}>{m}</Badge>)}
              </div>
            </td>
            <td className="mono tnum">{s.max_tok.toLocaleString()}</td>
            <td className="mono tnum">{s.max_conc}</td>
            <td><Switch on={s.on} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const OrchestratorBudgets = () => (
  <div className="grid-main">
    <Card title="Loop budgets" subtitle="Hard ceilings per session · loop terminates when exceeded">
      <div className="col" style={{ gap: 14 }}>
        {[
          { k: "Max loop turns", v: 30, unit: "" },
          { k: "Max total tokens", v: 200000, unit: "" },
          { k: "Max wall-clock duration", v: 600, unit: "s" },
          { k: "Max subagent depth", v: 3, unit: "" },
          { k: "Max concurrent subagents", v: 5, unit: "" },
          { k: "Max tool calls / turn", v: 8, unit: "" },
        ].map(b => (
          <div key={b.k} className="grid-2" style={{ gridTemplateColumns: "1fr auto", gap: 14, alignItems: "center" }}>
            <span style={{ fontSize: 12.5 }}>{b.k}</span>
            <div className="row" style={{ gap: 6 }}>
              <input className="input mono" defaultValue={b.v} style={{ width: 110 }} />
              <span className="muted" style={{ fontSize: 11 }}>{b.unit}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
    <Card title="Termination conditions">
      <div className="col" style={{ gap: 8, fontSize: 12 }}>
        <div className="row"><Switch on={true} /><span>Stop on <span className="mono">stop_reason=end_turn</span></span></div>
        <div className="row"><Switch on={true} /><span>Stop on max-turns reached</span></div>
        <div className="row"><Switch on={true} /><span>Stop on budget exhausted</span></div>
        <div className="row"><Switch on={true} /><span>Stop on FATAL error class</span></div>
        <div className="row"><Switch on={false} /><span>Stop on HITL rejection</span></div>
        <div className="row"><Switch on={true} /><span>Stop on tripwire fired</span></div>
      </div>
    </Card>
  </div>
);

const OrchestratorPolicies = () => (
  <Card title="HITL + risk policies">
    <div className="col" style={{ gap: 12, maxWidth: 720 }}>
      <Field label="Default HITL policy for write tools">
        <select className="select" defaultValue="always_ask"><option>auto</option><option>ask_once</option><option>always_ask</option></select>
      </Field>
      <Field label="Off-platform notifications">
        <div className="row" style={{ gap: 8 }}>
          <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" defaultChecked /> Teams</label>
          <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" defaultChecked /> Email</label>
          <label className="row" style={{ gap: 5, fontSize: 12 }}><input type="checkbox" /> PagerDuty</label>
        </div>
      </Field>
      <Field label="Risk escalation"><div className="kbar"><Badge tone="success">low → auto</Badge><Badge tone="info">medium → ask_once</Badge><Badge tone="warning">high → always_ask</Badge><Badge tone="danger">critical → always_ask + L2</Badge></div></Field>
      <div className="thin-rule" />
      <Field label="Cross-tenant tripwire (CANNOT disable)"><Badge tone="danger">armed · always-on</Badge></Field>
      <Field label="PII in tool input"><Badge tone="danger">armed · always-on</Badge></Field>
      <Field label="Provider key exposure"><Badge tone="danger">armed · always-on</Badge></Field>
    </div>
  </Card>
);

// ===================================================================
// /subagents — subagent registry CRUD
// Backed by backend/src/agent_harness/subagent/*
// ===================================================================
const SUBAGENT_LIST = [
  { id: "log-scanner",        role: "log-scanner",        prompt: "Tail and grep logs from a service. Return matched lines.", model: "claude-haiku-4-5",  modes: ["fork", "as_tool"], status: "live", calls24: 412, p95: 2.2 },
  { id: "dep-checker",        role: "dep-checker",        prompt: "Check health of downstream dependencies via health-probe.", model: "claude-haiku-4-5", modes: ["fork", "as_tool"], status: "live", calls24: 188, p95: 1.86 },
  { id: "metrics-pull",       role: "metrics-pull",       prompt: "Pull time-series metrics from observability backend.",       model: "claude-haiku-4-5", modes: ["fork", "as_tool"], status: "live", calls24: 540, p95: 0.32 },
  { id: "evidence-collector", role: "evidence-collector", prompt: "Assemble RCA evidence bundle from metrics + logs + memory.", model: "claude-sonnet-4-5", modes: ["as_tool"],          status: "live", calls24: 28,  p95: 4.4 },
  { id: "compliance-auditor", role: "compliance-auditor", prompt: "Answer compliance + audit queries with citations from KB.", model: "claude-opus-4-1",   modes: ["handoff", "teammate"], status: "live", calls24: 18,  p95: 8.2 },
  { id: "postmortem-writer",  role: "postmortem-writer",  prompt: "Draft postmortem doc following 5-whys + timeline template.", model: "claude-sonnet-4-5", modes: ["handoff"],           status: "staging", calls24: 2, p95: 12.0 },
  { id: "anomaly-detector",   role: "anomaly-detector",   prompt: "Detect statistical anomalies in metric streams.",              model: "claude-haiku-4-5",  modes: ["as_tool"],           status: "live", calls24: 84, p95: 0.41 },
  { id: "summarizer",         role: "summarizer",         prompt: "Compact reduce ≤500-token summary of an artifact.",            model: "claude-haiku-4-5",  modes: ["as_tool"],           status: "live", calls24: 612, p95: 0.55 },
];

const SubagentsRegistry = () => {
  const [selected, setSelected] = useAg("compliance-auditor");
  const active = SUBAGENT_LIST.find(s => s.id === selected) || SUBAGENT_LIST[0];
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Subagent Registry</div>
          <div className="page-sub">
            Range 11 · AgentSpec definitions · 4 dispatch modes (fork / teammate / handoff / as_tool)
            <span className="route-pill">/subagents</span>
            <span className="mono subtle">· {SUBAGENT_LIST.length} registered</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">Sync from repo</Button>
          <Button variant="primary" size="sm" icon="plus">New subagent</Button>
        </div>
      </div>

      <div className="grid-3" style={{ marginBottom: 16 }}>
        {[
          { mode: "fork", desc: "Concurrent fan-out · parent merges results", c: "var(--thinking)", count: 3 },
          { mode: "as_tool", desc: "LLM calls subagent as a tool · synchronous", c: "var(--tool)", count: 6 },
          { mode: "teammate", desc: "Peer-to-peer mailbox · async coordination", c: "var(--memory)", count: 1 },
          { mode: "handoff", desc: "Transfer control · shared conversation history", c: "var(--info)", count: 2 },
        ].map(m => (
          <div key={m.mode} className="stat" style={{ borderLeft: `3px solid ${m.c}` }}>
            <div className="stat-label"><span style={{ color: m.c, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em", fontFamily: "var(--font-mono)" }}>{m.mode}</span></div>
            <div className="stat-value" style={{ fontSize: 22 }}>{m.count}</div>
            <div className="subtle" style={{ fontSize: 10.5 }}>{m.desc}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
        <Card title="Subagents" subtitle="Click to inspect / edit" bodyClass="flush">
          <table className="table">
            <thead><tr><th>Role</th><th>Model</th><th>Modes</th><th>Status</th><th style={{ textAlign: "right" }}>Calls · 24h</th><th style={{ textAlign: "right" }}>p95</th></tr></thead>
            <tbody>
              {SUBAGENT_LIST.map(s => (
                <tr key={s.id} onClick={() => setSelected(s.id)} style={{ background: selected === s.id ? "oklch(from var(--primary) l c h / 0.10)" : undefined }}>
                  <td className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{s.role}</td>
                  <td className="mono subtle" style={{ fontSize: 11.5 }}>{s.model}</td>
                  <td>
                    <div className="row" style={{ gap: 4 }}>
                      {s.modes.map(m => <Badge key={m} tone={m === "fork" ? "thinking" : m === "as_tool" ? "tool" : m === "handoff" ? "info" : "memory"}>{m}</Badge>)}
                    </div>
                  </td>
                  <td><Badge tone={s.status === "live" ? "success" : "warning"} dot>{s.status}</Badge></td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>{s.calls24}</td>
                  <td className="mono tnum subtle" style={{ textAlign: "right" }}>{s.p95}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <SubagentDetail sub={active} />
      </div>
    </div>
  );
};

const SubagentDetail = ({ sub }) => {
  const [tab, setTab] = useAg("spec");
  return (
    <Card title={<span className="mono">{sub.role}</span>} subtitle={`AgentSpec · ${sub.modes.join(" + ")}`} bodyClass="flush"
      actions={<Button variant="ghost" size="sm" icon="play">Test invoke</Button>}
    >
      <div style={{ padding: "0 16px" }}>
        <Tabs value={tab} onChange={setTab}
          items={[{ id: "spec", label: "AgentSpec" }, { id: "budget", label: "Budget" }, { id: "tools", label: "Tools" }, { id: "stats", label: "Stats" }]}
        />
      </div>
      <div className="card-body">
        {tab === "spec" && (
          <div className="col" style={{ gap: 12 }}>
            <Field label="Role (immutable id)"><input className="input mono" readOnly defaultValue={sub.role} /></Field>
            <Field label="Model"><select className="select" defaultValue={sub.model}><option>claude-haiku-4-5</option><option>claude-sonnet-4-5</option><option>claude-opus-4-1</option></select></Field>
            <Field label="System prompt"><textarea className="textarea" rows="6" defaultValue={sub.prompt} /></Field>
            <Field label="Allowed dispatch modes">
              <div className="row" style={{ gap: 6 }}>
                {["fork", "as_tool", "teammate", "handoff"].map(m => (
                  <label key={m} className="row" style={{ gap: 5, fontSize: 12, padding: "4px 8px", border: "1px solid var(--border)", borderRadius: 4, background: sub.modes.includes(m) ? "var(--primary-soft)" : "var(--bg-1)", cursor: "pointer" }}>
                    <input type="checkbox" defaultChecked={sub.modes.includes(m)} style={{ accentColor: "var(--primary)" }} />
                    <span className="mono" style={{ color: sub.modes.includes(m) ? "var(--primary)" : "var(--fg-muted)" }}>{m}</span>
                  </label>
                ))}
              </div>
            </Field>
          </div>
        )}
        {tab === "budget" && (
          <div className="col" style={{ gap: 12 }}>
            <Field label="Max tokens"><input className="input mono" defaultValue="10000" /></Field>
            <Field label="Max duration (s)"><input className="input mono" defaultValue="300" /></Field>
            <Field label="Max concurrent invocations"><input className="input mono" defaultValue="5" /></Field>
            <Field label="Max subagent depth (from this)"><input className="input mono" defaultValue="3" /></Field>
            <div className="muted" style={{ fontSize: 11.5, padding: 10, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6 }}>
              Worktree mode is intentionally <span className="mono">absent</span> from V2 — IPA runs server-side, so we use mailbox + handoff for isolation instead of git worktrees.
            </div>
          </div>
        )}
        {tab === "tools" && (
          <div className="col" style={{ gap: 8 }}>
            <div className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Tools available to this subagent</div>
            <div className="kbar">
              <Badge tone="tool" pill>log.tail</Badge>
              <Badge tone="tool" pill>log.grep</Badge>
              <Badge tone="tool" pill>metrics.query</Badge>
            </div>
            <Button variant="outline" size="sm" icon="plus">Attach tool</Button>
          </div>
        )}
        {tab === "stats" && (
          <div className="col" style={{ gap: 8, fontSize: 12 }}>
            <div className="spread"><span className="muted">Calls · 24h</span><span className="mono">{sub.calls24}</span></div>
            <div className="spread"><span className="muted">p95 duration</span><span className="mono">{sub.p95}s</span></div>
            <div className="spread"><span className="muted">Success rate</span><span className="mono">99.2%</span></div>
            <div className="spread"><span className="muted">Avg tokens / call</span><span className="mono">2,840</span></div>
            <div className="spread"><span className="muted">Most-used orchestrator</span><span className="mono">orchestrator-main</span></div>
          </div>
        )}
      </div>
    </Card>
  );
};

Object.assign(window, { Orchestrator, SubagentsRegistry });
