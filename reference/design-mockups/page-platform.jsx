/* global React, Icon, Button, Badge, Card, Tabs, Field, RiskBadge, SevDot, Stat, Spark */
const { useState: usePf, useMemo: useMPf } = React;

// ============================================================
// /state-inspector — LoopState version chain + time-travel
// Backed by backend/src/agent_harness/_contracts/state.py
// ============================================================
const STATE_VERSIONS = [
  { v: 18, parent: 17, at: "10:42:28.420", by: "orchestrator_loop",  msg: "loop.iteration_4 end · stop_reason=hitl", checkpoint: false },
  { v: 17, parent: 16, at: "10:42:28.180", by: "reducer",             msg: "WRITE durable: pending_approval[a8f3.k2p1]", checkpoint: true },
  { v: 16, parent: 15, at: "10:42:27.480", by: "tools",               msg: "tool_result · metrics.query · 1.8KB", checkpoint: false },
  { v: 15, parent: 14, at: "10:42:25.220", by: "reducer",             msg: "WRITE durable: conversation_summary", checkpoint: true },
  { v: 14, parent: 13, at: "10:42:24.020", by: "subagent",            msg: "subagent.completed · log-scanner",     checkpoint: false },
  { v: 13, parent: 12, at: "10:42:22.840", by: "tools",               msg: "tool_result · incidents.list · 8 rows", checkpoint: false },
  { v: 12, parent: 11, at: "10:42:20.120", by: "orchestrator_loop",   msg: "loop.iteration_2 end · spawn 3 subagents", checkpoint: false },
  { v: 11, parent: 10, at: "10:42:19.620", by: "reducer",             msg: "compaction: hybrid · -2,140 tokens", checkpoint: true },
  { v: 10, parent: 9,  at: "10:42:18.840", by: "orchestrator_loop",   msg: "loop.iteration_1 end · stop_reason=tool_use", checkpoint: false },
  { v: 9,  parent: 8,  at: "10:42:18.020", by: "session_init",        msg: "session_id=sess_4tk2p · tenant=acme-prod", checkpoint: true },
];

const StateInspector = () => {
  const [selected, setSelected] = usePf(18);
  const current = STATE_VERSIONS.find(s => s.v === selected) || STATE_VERSIONS[0];
  const parent = STATE_VERSIONS.find(s => s.v === current.parent);
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">State Inspector</div>
          <div className="page-sub">
            Range 7 · LoopState time-travel · Reducer is the only mutator
            <span className="route-pill">/state-inspector</span>
            <span className="mono subtle">· {STATE_VERSIONS.length} versions · 3 checkpoints</span>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="clock">Diff vs parent</Button>
          <Button variant="outline" size="sm" icon="refresh">Restore from version</Button>
          <Button variant="outline" size="sm" icon="download">Export checkpoint</Button>
        </div>
      </div>

      <div className="grid-stats">
        <Stat label="Current version" value={`v${selected}`} />
        <Stat label="Transient size" value="12" unit=" msg" />
        <Stat label="Durable bytes" value="4.2" unit=" kB" />
        <Stat label="Pending approvals" value="1" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 14 }}>
        <Card title="Version chain" subtitle="Reducer-authored · monotonic" bodyClass="dense">
          <div className="col" style={{ gap: 0, position: "relative" }}>
            {STATE_VERSIONS.map((sv, i) => {
              const isLast = i === STATE_VERSIONS.length - 1;
              const isSel = sv.v === selected;
              const cat = sv.by === "reducer" ? "var(--memory)"
                : sv.by === "orchestrator_loop" ? "var(--primary)"
                : sv.by === "tools" ? "var(--tool)"
                : sv.by === "subagent" ? "var(--info)"
                : sv.by === "session_init" ? "var(--success)"
                : "var(--fg-muted)";
              return (
                <div key={sv.v} onClick={() => setSelected(sv.v)}
                  style={{
                    position: "relative", display: "grid",
                    gridTemplateColumns: "28px 1fr",
                    gap: 10, padding: "7px 4px", cursor: "pointer",
                    background: isSel ? "oklch(from var(--primary) l c h / 0.10)" : undefined,
                    borderRadius: 4,
                    borderLeft: isSel ? "2px solid var(--primary)" : "2px solid transparent",
                  }}>
                  {!isLast && <span style={{ position: "absolute", left: 17, top: 22, bottom: -8, width: 1, background: "var(--border)" }} />}
                  <span style={{
                    width: 20, height: 20, borderRadius: sv.checkpoint ? 4 : "50%",
                    background: sv.checkpoint ? `oklch(from ${cat} l c h / 0.2)` : "var(--bg-1)",
                    border: `1.5px solid ${cat}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: cat, fontSize: 9, fontFamily: "var(--font-mono)", fontWeight: 600,
                    marginTop: 4,
                  }}>{sv.checkpoint ? <Icon name="shield" size={10} /> : null}</span>
                  <div>
                    <div className="row" style={{ gap: 5, fontSize: 11.5 }}>
                      <span className="mono" style={{ fontWeight: 600 }}>v{sv.v}</span>
                      {sv.checkpoint && <Badge tone="memory">checkpoint</Badge>}
                      <span className="mono subtle" style={{ marginLeft: "auto", fontSize: 10 }}>{sv.at.slice(-6)}</span>
                    </div>
                    <div className="mono" style={{ fontSize: 10.5, color: cat, marginTop: 2 }}>{sv.by}</div>
                    <div className="subtle" style={{ fontSize: 11, marginTop: 2, lineHeight: 1.45 }}>{sv.msg}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <div className="col" style={{ gap: 14 }}>
          <Card title={<span className="row" style={{ gap: 6 }}>
            <span style={{ fontFamily: "var(--font-mono)" }}>v{selected}</span>
            <span className="subtle">by</span>
            <span className="mono" style={{ color: "var(--primary)" }}>{current.by}</span>
          </span>} subtitle={current.msg} bodyClass="dense">
            <div className="grid-2">
              <div>
                <div className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Transient state · in-memory</div>
                <div className="col" style={{ gap: 6, fontSize: 12 }}>
                  <KvLine k="messages" v={`${12} items`} mono />
                  <KvLine k="pending_tool_calls" v="1" mono />
                  <KvLine k="current_turn" v="4" mono />
                  <KvLine k="elapsed_ms" v="4,210" mono />
                  <KvLine k="token_usage_so_far" v="18,420" mono />
                </div>
              </div>
              <div>
                <div className="subtle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Durable state · DB-persisted</div>
                <div className="col" style={{ gap: 6, fontSize: 12 }}>
                  <KvLine k="session_id" v="sess_4tk2p" mono />
                  <KvLine k="tenant_id" v="tenant_01h9a2" mono />
                  <KvLine k="user_id" v="u_jamie" mono />
                  <KvLine k="pending_approval_ids" v="[a8f3.k2p1]" mono />
                  <KvLine k="last_checkpoint_version" v="17" mono />
                  <KvLine k="conversation_summary" v={<span className="subtle">— 124 chars —</span>} />
                </div>
              </div>
            </div>
          </Card>

          <Card title="Diff vs parent" subtitle={parent ? `v${parent.v} → v${current.v}` : "no parent"} bodyClass="dense">
            <pre style={{ margin: 0, padding: 12, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.55, overflowX: "auto" }}>
{`  durable.pending_approval_ids:
- []
+ ["a8f3.k2p1"]

  transient.pending_tool_calls:
- []
+ [{ name: "k8s.set_env", tool_call_id: "tc_8a02p" }]

  transient.token_usage_so_far:
- 18,200
+ 18,420  (+220)`}
            </pre>
          </Card>
        </div>
      </div>
    </div>
  );
};

const KvLine = ({ k, v, mono }) => (
  <div className="spread">
    <span className="muted mono" style={{ fontSize: 11 }}>{k}</span>
    <span className={mono ? "mono tnum" : ""} style={{ fontSize: 11.5 }}>{v}</span>
  </div>
);

// ============================================================
// /compaction — context compaction events + strategies
// Backed by backend/src/agent_harness/context_mgmt/compactor/
// ============================================================
const COMPACTION_EVENTS = [
  { id: "cmp_4tk2p_1", at: "10:42:19", session: "sess_4tk2p", strategy: "hybrid", before: 18420, after: 16280, msgs: 8, ms: 412, savedPct: 11.6, reason: "context > 90% budget" },
  { id: "cmp_88vqc_1", at: "10:31:00", session: "sess_88vqc", strategy: "structural", before: 28800, after: 22400, msgs: 14, ms: 38, savedPct: 22.2, reason: "redundant tool retries" },
  { id: "cmp_91kxu_1", at: "10:18:40", session: "sess_91kxu", strategy: "semantic", before: 42000, after: 18200, msgs: 28, ms: 2400, savedPct: 56.7, reason: "summarized 28 old turns" },
  { id: "cmp_kpw01_1", at: "10:08:24", session: "sess_kpw01", strategy: "hybrid", before: 24200, after: 19400, msgs: 9, ms: 480, savedPct: 19.8, reason: "context > 90% budget" },
  { id: "cmp_2afpw_1", at: "09:42:18", session: "sess_2afpw", strategy: "structural", before: 16800, after: 14200, msgs: 6, ms: 22, savedPct: 15.5, reason: "redundant tool retries" },
  { id: "cmp_qqx88_1", at: "08:35:11", session: "sess_qqx88", strategy: "semantic", before: 38400, after: 17800, msgs: 24, ms: 2180, savedPct: 53.6, reason: "summarized 24 old turns" },
];

const Compaction = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Context Compaction</div>
        <div className="page-sub">
          Range 4 · Token-budget reclaim · 3 strategies (STRUCTURAL / SEMANTIC / HYBRID)
          <span className="route-pill">/compaction</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="play">Run on current</Button>
        <Button variant="outline" size="sm" icon="download">Export events</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Tokens reclaimed · 24h" value="58.4" unit="K" delta="+12K" deltaDir="up" spark={<Spark points={[20,30,40,48,52,55,58]} tone="var(--success)" />} />
      <Stat label="Compaction events" value="84" delta="+6" deltaDir="up" />
      <Stat label="Avg saving" value="28.4" unit="%" delta="+2pp" deltaDir="up" />
      <Stat label="p95 duration" value="2.4" unit="s" delta="-180ms" deltaDir="up" />
    </div>

    <div className="grid-main">
      <Card title="Recent compactions" subtitle="Sessions where compaction fired" bodyClass="flush" actions={
        <div className="row">
          <Button variant="ghost" size="sm" icon="filter">All strategies</Button>
        </div>
      }>
        <table className="table">
          <thead>
            <tr>
              <th>Event</th>
              <th>Session</th>
              <th>Strategy</th>
              <th style={{ textAlign: "right" }}>Before → After</th>
              <th style={{ textAlign: "right" }}>Saved</th>
              <th style={{ textAlign: "right" }}>Duration</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {COMPACTION_EVENTS.map(c => (
              <tr key={c.id}>
                <td className="mono subtle" style={{ fontSize: 11 }}>{c.id.slice(-7)} <span style={{ marginLeft: 6 }}>{c.at}</span></td>
                <td className="mono" style={{ fontSize: 11.5 }}>{c.session}</td>
                <td>
                  <Badge tone={c.strategy === "structural" ? "info" : c.strategy === "semantic" ? "thinking" : "primary"}>
                    {c.strategy}
                  </Badge>
                </td>
                <td className="mono tnum" style={{ textAlign: "right", fontSize: 11 }}>
                  <span style={{ color: "var(--fg-muted)" }}>{c.before.toLocaleString()}</span>
                  <span className="subtle"> → </span>
                  <span style={{ color: "var(--success)" }}>{c.after.toLocaleString()}</span>
                </td>
                <td className="mono tnum" style={{ textAlign: "right", color: c.savedPct > 30 ? "var(--success)" : "var(--fg-muted)" }}>{c.savedPct.toFixed(1)}%</td>
                <td className="mono tnum subtle" style={{ textAlign: "right" }}>{c.ms}ms</td>
                <td className="subtle" style={{ fontSize: 12 }}>{c.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Strategy mix" subtitle="3 compactor strategies · 7-day distribution">
        <div className="col" style={{ gap: 16 }}>
          {[
            { name: "STRUCTURAL", desc: "Rule-based · drops redundant tool retries · keeps system + recent N + HITL", count: 38, pct: 45, tone: "var(--info)", avgMs: 28 },
            { name: "SEMANTIC", desc: "LLM-driven · summarize old turns into a single assistant message", count: 22, pct: 26, tone: "var(--thinking)", avgMs: 2180 },
            { name: "HYBRID", desc: "Structural first; if still over budget, fall through to semantic", count: 24, pct: 29, tone: "var(--primary)", avgMs: 480 },
          ].map(s => (
            <div key={s.name}>
              <div className="row" style={{ gap: 6, marginBottom: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: s.tone }} />
                <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: s.tone }}>{s.name}</span>
                <span className="mono tnum subtle" style={{ marginLeft: "auto", fontSize: 11 }}>{s.count} · {s.pct}%</span>
              </div>
              <div className="muted" style={{ fontSize: 11, lineHeight: 1.5, marginBottom: 5 }}>{s.desc}</div>
              <div className="bar-track">
                <span style={{ width: s.pct + "%", background: s.tone }} />
              </div>
              <div className="subtle mono" style={{ fontSize: 10.5, marginTop: 3 }}>avg duration: {s.avgMs}ms</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  </div>
);

// ============================================================
// /workflows — Microsoft Agent Framework Sequential / Parallel / Branch
// + Checkpointing (the distinctive Agent Framework feature)
// ============================================================
const WORKFLOWS = [
  { id: "wf_incident_p1", name: "incident_p1_response", kind: "branch", steps: 6, checkpoints: 4, runs24: 12, success: 11, p95: 184, active: true },
  { id: "wf_q4_audit",    name: "q4_compliance_audit", kind: "sequential", steps: 14, checkpoints: 8, runs24: 1, success: 1, p95: 1840, active: true },
  { id: "wf_patrol_apac", name: "patrol_apac_nightly", kind: "parallel", steps: 8, checkpoints: 2, runs24: 24, success: 24, p95: 92, active: true },
  { id: "wf_change_chg",  name: "change_review", kind: "sequential", steps: 5, checkpoints: 3, runs24: 8, success: 7, p95: 240, active: true },
  { id: "wf_rca",         name: "rca_5_whys", kind: "branch", steps: 7, checkpoints: 3, runs24: 4, success: 4, p95: 320, active: true },
];

const Workflows = () => {
  const [selected, setSelected] = usePf("wf_incident_p1");
  const wf = WORKFLOWS.find(w => w.id === selected) || WORKFLOWS[0];
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Workflows</div>
          <div className="page-sub">
            Microsoft Agent Framework · Sequential / Parallel / Branch + Checkpointing
            <span className="route-pill">/workflows</span>
            <Badge tone="primary">5 active</Badge>
          </div>
        </div>
        <div className="page-actions">
          <Button variant="outline" size="sm" icon="git">Templates</Button>
          <Button variant="primary" size="sm" icon="plus">New workflow</Button>
        </div>
      </div>

      <div className="grid-3" style={{ marginBottom: 16 }}>
        {[
          { kind: "sequential", name: "Sequential", icon: "arrow_right", desc: "Linear pipeline. Each step waits for the previous. Checkpoint after each step.", c: "var(--primary)" },
          { kind: "parallel", name: "Parallel", icon: "fork", desc: "Concurrent fan-out. All branches run; converge at join. Single checkpoint after join.", c: "var(--thinking)" },
          { kind: "branch", name: "Branch", icon: "branch", desc: "Conditional routing. Agent picks 1-of-N paths. Each path can have its own checkpoint policy.", c: "var(--info)" },
        ].map(k => (
          <div key={k.kind} className="card" style={{ borderLeft: `3px solid ${k.c}` }}>
            <div className="card-body">
              <div className="row" style={{ gap: 8, marginBottom: 8 }}>
                <Icon name={k.icon} size={14} style={{ color: k.c }} />
                <span style={{ fontWeight: 600, fontSize: 13 }}>{k.name}</span>
                <span className="mono subtle" style={{ marginLeft: "auto", fontSize: 10.5 }}>
                  {WORKFLOWS.filter(w => w.kind === k.kind).length} workflows
                </span>
              </div>
              <div className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>{k.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14 }}>
        <Card title="Active workflows" bodyClass="flush">
          <table className="table">
            <thead>
              <tr><th>Workflow</th><th>Kind</th><th style={{ textAlign: "right" }}>Steps</th><th style={{ textAlign: "right" }}>Checkpoints</th><th style={{ textAlign: "right" }}>Runs · 24h</th><th style={{ textAlign: "right" }}>p95</th><th>Success</th></tr>
            </thead>
            <tbody>
              {WORKFLOWS.map(w => (
                <tr key={w.id} onClick={() => setSelected(w.id)} style={{ background: selected === w.id ? "oklch(from var(--primary) l c h / 0.10)" : undefined }}>
                  <td><span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{w.name}</span></td>
                  <td><Badge tone={w.kind === "sequential" ? "primary" : w.kind === "parallel" ? "thinking" : "info"}>{w.kind}</Badge></td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>{w.steps}</td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>
                    <span className="row" style={{ gap: 4, justifyContent: "flex-end" }}>
                      <Icon name="shield" size={10} style={{ color: "var(--memory)" }} />
                      {w.checkpoints}
                    </span>
                  </td>
                  <td className="mono tnum" style={{ textAlign: "right" }}>{w.runs24}</td>
                  <td className="mono tnum subtle" style={{ textAlign: "right" }}>{w.p95}s</td>
                  <td>
                    <span className="mono tnum" style={{ fontSize: 11.5, color: w.success === w.runs24 ? "var(--success)" : "var(--warning)" }}>{w.success}/{w.runs24}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title={<span className="mono">{wf.name}</span>} subtitle={`${wf.kind} · ${wf.steps} steps · ${wf.checkpoints} checkpoints`} bodyClass="dense">
          <WorkflowGraph wf={wf} />
        </Card>
      </div>
    </div>
  );
};

const WorkflowGraph = ({ wf }) => {
  // Render workflow as a vertical list of steps with checkpoint markers
  const steps = wf.kind === "branch"
    ? [
        { name: "classify_severity", kind: "agent", ck: true },
        { name: "fetch_runbook", kind: "tool", ck: false },
        { name: "decide_route", kind: "agent", ck: true },
        { name: "auto_remediate", kind: "tool", ck: false, branch: "P0/P1" },
        { name: "escalate_l2", kind: "tool", ck: false, branch: "P0/P1" },
        { name: "draft_response", kind: "tool", ck: false, branch: "P2/P3" },
        { name: "post_incident", kind: "agent", ck: true },
      ]
    : wf.kind === "parallel"
    ? [
        { name: "trigger_split", kind: "system", ck: true },
        { name: "scan_apac_db", kind: "tool", ck: false, branch: "par-1" },
        { name: "scan_apac_redis", kind: "tool", ck: false, branch: "par-2" },
        { name: "scan_apac_pgbouncer", kind: "tool", ck: false, branch: "par-3" },
        { name: "join_results", kind: "system", ck: false },
        { name: "report_anomalies", kind: "agent", ck: true },
      ]
    : [
        { name: "scope_audit", kind: "agent", ck: true },
        { name: "pull_evidence", kind: "tool", ck: false },
        { name: "redact_pii", kind: "tool", ck: true },
        { name: "summarize_findings", kind: "agent", ck: true },
        { name: "human_review", kind: "hitl", ck: true },
        { name: "bundle_export", kind: "tool", ck: true },
      ];
  const kindColor = (k) => k === "agent" ? "var(--primary)" : k === "tool" ? "var(--tool)" : k === "hitl" ? "var(--warning)" : "var(--info)";
  return (
    <div style={{ position: "relative", paddingLeft: 14 }}>
      <div style={{ position: "absolute", left: 11, top: 6, bottom: 6, width: 1, background: "var(--border)" }} />
      {steps.map((s, i) => (
        <div key={i} style={{ position: "relative", display: "flex", alignItems: "center", gap: 10, padding: "6px 0" }}>
          <span style={{
            position: "absolute", left: -10, top: 12,
            width: 14, height: 14, borderRadius: s.ck ? 3 : "50%",
            background: s.ck ? `oklch(from var(--memory) l c h / 0.18)` : "var(--bg-1)",
            border: `1.5px solid ${s.ck ? "var(--memory)" : kindColor(s.kind)}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: s.ck ? "var(--memory)" : kindColor(s.kind),
          }}>{s.ck && <Icon name="shield" size={8} />}</span>
          <div className="grow" style={{ marginLeft: 8 }}>
            <div className="row" style={{ gap: 6 }}>
              <span className="mono" style={{ fontSize: 11.5, fontWeight: 500 }}>{s.name}</span>
              {s.branch && <Badge tone="info">{s.branch}</Badge>}
              {s.ck && <Badge tone="memory">checkpoint</Badge>}
              <span className="mono subtle" style={{ marginLeft: "auto", fontSize: 10.5, color: kindColor(s.kind) }}>{s.kind}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// ============================================================
// /error-policy — 4-class taxonomy + circuit breakers + retry budget
// Backed by backend/src/agent_harness/_contracts/errors.py + error_handling/
// ============================================================
const ERROR_CLASSES = [
  { id: "TRANSIENT",         desc: "Network blip / 5xx · auto-retry with backoff",                              count: 142, c: "var(--info)",     pct: 38 },
  { id: "LLM_RECOVERABLE",   desc: "Tool returned error · LLM self-corrects on next turn",                       count: 84,  c: "var(--thinking)", pct: 22 },
  { id: "HITL_RECOVERABLE",  desc: "User-fixable · missing creds / data · pauses loop for input",                count: 12,  c: "var(--warning)",  pct: 3 },
  { id: "FATAL",             desc: "Unrecoverable · loop terminates · session marked failed",                    count: 2,   c: "var(--danger)",   pct: 1 },
];

const CIRCUIT_BREAKERS = [
  { adapter: "azure_openai",  state: "closed", failures: 2,  threshold: 10, lastTrip: "—" },
  { adapter: "anthropic",     state: "closed", failures: 0,  threshold: 10, lastTrip: "—" },
  { adapter: "vector_db",     state: "closed", failures: 1,  threshold: 5,  lastTrip: "—" },
  { adapter: "tool.k8s",      state: "half_open", failures: 3, threshold: 5, lastTrip: "2m ago · 4/5" },
  { adapter: "tool.zendesk",  state: "open", failures: 8, threshold: 5,  lastTrip: "8m ago · cooldown 22m" },
  { adapter: "tool.slack",    state: "closed", failures: 0,  threshold: 5,  lastTrip: "—" },
];

const ErrorPolicyPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">Error Policy</div>
        <div className="page-sub">
          Range 8 · 4-class taxonomy · Circuit breaker · Retry budget · Terminator
          <span className="route-pill">/error-policy</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="git">Edit policy</Button>
        <Button variant="outline" size="sm" icon="download">Export</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Errors · 1h" value="240" delta="+12" deltaDir="down" />
      <Stat label="Auto-recovered" value="97.5" unit="%" delta="+0.8pp" deltaDir="up" />
      <Stat label="Circuits open" value="1" delta="+1" deltaDir="down" />
      <Stat label="Budget burn" value="12.4" unit="%" delta="-2pp" deltaDir="up" />
    </div>

    <div className="grid-main">
      <Card title="4-class taxonomy" subtitle="Where errors land · last 1h" actions={
        <Button variant="ghost" size="sm" icon="filter">Drill into class</Button>
      }>
        <div className="col" style={{ gap: 12 }}>
          {ERROR_CLASSES.map(c => (
            <div key={c.id}>
              <div className="row" style={{ gap: 8, marginBottom: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: c.c }} />
                <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: c.c }}>{c.id}</span>
                <span className="muted" style={{ fontSize: 11.5, marginLeft: 6 }}>{c.desc}</span>
                <span className="mono tnum" style={{ marginLeft: "auto", fontSize: 11.5 }}>{c.count}</span>
              </div>
              <div className="bar-track">
                <span style={{ width: c.pct + "%", background: c.c }} />
              </div>
            </div>
          ))}
        </div>
        <div className="thin-rule" />
        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>
          Sourced from <span className="mono">agent_harness/_contracts/errors.py</span>. ErrorClass enum drives <span className="mono">DefaultErrorPolicy.classify()</span> via MRO walk; adapters subclass <span className="mono">AuthenticationError</span> / <span className="mono">MissingDataError</span> / <span className="mono">ToolExecutionError</span>.
        </div>
      </Card>

      <Card title="Retry budget" subtitle="Per-tool circuit budget · 1h window" bodyClass="dense">
        <div className="col" style={{ gap: 10 }}>
          {[
            { name: "Inference retries", used: 18, max: 100 },
            { name: "Tool retries", used: 84, max: 500 },
            { name: "Subagent re-spawns", used: 3, max: 50 },
            { name: "HITL re-prompts", used: 1, max: 10 },
          ].map(b => (
            <div key={b.name}>
              <div className="spread" style={{ marginBottom: 3, fontSize: 12 }}>
                <span>{b.name}</span>
                <span className="mono tnum">{b.used}<span className="subtle">/{b.max}</span></span>
              </div>
              <div className="bar-track">
                <span style={{ width: ((b.used / b.max) * 100) + "%", background: (b.used / b.max) > 0.7 ? "var(--warning)" : "var(--success)" }} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>

    <div style={{ height: 14 }} />

    <Card title="Circuit breakers" subtitle="Per-adapter state · open = traffic blocked" bodyClass="flush">
      <table className="table">
        <thead><tr><th>Adapter</th><th>State</th><th style={{ textAlign: "right" }}>Failures</th><th style={{ textAlign: "right" }}>Threshold</th><th>Last trip</th><th></th></tr></thead>
        <tbody>
          {CIRCUIT_BREAKERS.map(cb => (
            <tr key={cb.adapter}>
              <td className="mono" style={{ fontSize: 12 }}>{cb.adapter}</td>
              <td>
                <Badge tone={cb.state === "closed" ? "success" : cb.state === "half_open" ? "warning" : "danger"} dot>{cb.state}</Badge>
              </td>
              <td className="mono tnum" style={{ textAlign: "right" }}>{cb.failures}</td>
              <td className="mono tnum subtle" style={{ textAlign: "right" }}>{cb.threshold}</td>
              <td className="subtle mono" style={{ fontSize: 11 }}>{cb.lastTrip}</td>
              <td>
                {cb.state === "open" && <Button variant="outline" size="sm" icon="refresh">Force close</Button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  </div>
);

// ============================================================
// /rbac — role + permission matrix
// Backed by backend/src/platform_layer/identity/rbac.py
// ============================================================
const ROLES = [
  { id: "platform_admin",  name: "Platform Admin", members: 3,  desc: "Cross-tenant ops; provider keys; tenant lifecycle" },
  { id: "tenant_admin",    name: "Tenant Admin",   members: 8,  desc: "Tenant-scoped settings; member mgmt; feature flags" },
  { id: "operator",        name: "Operator",       members: 24, desc: "Daily SRE workflows; chat; approvals" },
  { id: "compliance",      name: "Compliance",     members: 6,  desc: "Audit chain read; evidence bundling" },
  { id: "auditor",         name: "Auditor",        members: 4,  desc: "Read-only audit + verification" },
  { id: "developer",       name: "Developer",      members: 12, desc: "ToolSpec editing; prompt tuning; agent CRUD" },
];

const RESOURCES = [
  { id: "agent",          name: "Agent" },
  { id: "tool",           name: "Tool" },
  { id: "memory",         name: "Memory" },
  { id: "audit",          name: "Audit chain" },
  { id: "tenant",         name: "Tenant" },
  { id: "feature_flag",   name: "Feature flag" },
  { id: "hitl",           name: "HITL queue" },
];

// Permission matrix: role → resource → ["read"|"write"|"admin"|null]
const PERM = {
  platform_admin: { agent: "admin", tool: "admin", memory: "admin", audit: "admin", tenant: "admin", feature_flag: "admin", hitl: "admin" },
  tenant_admin:   { agent: "admin", tool: "write", memory: "write", audit: "read",  tenant: "write", feature_flag: "write", hitl: "admin" },
  operator:       { agent: "write", tool: "read",  memory: "write", audit: "read",  tenant: null,    feature_flag: "read",  hitl: "write" },
  compliance:     { agent: "read",  tool: "read",  memory: "read",  audit: "admin", tenant: "read",  feature_flag: "read",  hitl: "read"  },
  auditor:        { agent: "read",  tool: "read",  memory: "read",  audit: "read",  tenant: "read",  feature_flag: "read",  hitl: "read"  },
  developer:      { agent: "admin", tool: "admin", memory: "read",  audit: "read",  tenant: null,    feature_flag: "read",  hitl: "read"  },
};

const RBACPage = () => (
  <div>
    <div className="page-head">
      <div>
        <div className="page-title">RBAC</div>
        <div className="page-sub">
          Role-based access control · 6 roles × 7 resources · tenant-scoped
          <span className="route-pill">/rbac</span>
        </div>
      </div>
      <div className="page-actions">
        <Button variant="outline" size="sm" icon="download">Export policy</Button>
        <Button variant="primary" size="sm" icon="plus">New role</Button>
      </div>
    </div>

    <div className="grid-stats">
      <Stat label="Roles" value={String(ROLES.length)} />
      <Stat label="Members assigned" value="57" delta="+3" deltaDir="up" />
      <Stat label="Resource kinds" value={String(RESOURCES.length)} />
      <Stat label="Audit policy changes · 30d" value="14" delta="-2" deltaDir="up" />
    </div>

    <Card title="Permission matrix" subtitle="Role × Resource × Action · click cell to edit" bodyClass="flush">
      <table className="table">
        <thead>
          <tr>
            <th style={{ minWidth: 180 }}>Role</th>
            <th>Members</th>
            {RESOURCES.map(r => <th key={r.id} style={{ textAlign: "center", whiteSpace: "nowrap" }}>{r.name}</th>)}
          </tr>
        </thead>
        <tbody>
          {ROLES.map(role => (
            <tr key={role.id}>
              <td>
                <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>{role.name}</div>
                <div className="subtle" style={{ fontSize: 11, marginTop: 2 }}>{role.desc}</div>
              </td>
              <td><Badge>{role.members}</Badge></td>
              {RESOURCES.map(r => {
                const p = PERM[role.id][r.id];
                return (
                  <td key={r.id} style={{ textAlign: "center" }}>
                    {p ? <PermBadge p={p} /> : <span className="subtle mono" style={{ fontSize: 11 }}>—</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>

    <div style={{ height: 14 }} />

    <div className="grid-main">
      <Card title="Role assignment audit" subtitle="Recent grants / revokes · WORM logged" bodyClass="flush">
        <table className="table">
          <thead><tr><th>Action</th><th>Member</th><th>Role</th><th>By</th><th>When</th></tr></thead>
          <tbody>
            {[
              { act: "GRANT", who: "yui@acme.com", role: "operator", by: "@platform-l2", at: "12m ago" },
              { act: "REVOKE", who: "ex-contractor@acme.com", role: "developer", by: "@platform-l2", at: "2h ago" },
              { act: "GRANT", who: "ben@acme.com", role: "compliance", by: "@security", at: "yesterday" },
              { act: "GRANT", who: "rae@acme.com", role: "auditor", by: "@security", at: "yesterday" },
              { act: "MODIFY", who: "role:developer", role: "+ tool:admin", by: "@platform-l2", at: "3 days ago" },
            ].map((a, i) => (
              <tr key={i}>
                <td><Badge tone={a.act === "GRANT" ? "success" : a.act === "REVOKE" ? "danger" : "info"}>{a.act}</Badge></td>
                <td className="mono" style={{ fontSize: 11.5 }}>{a.who}</td>
                <td><Badge>{a.role}</Badge></td>
                <td className="mono subtle" style={{ fontSize: 11.5 }}>{a.by}</td>
                <td className="subtle" style={{ fontSize: 11.5 }}>{a.at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="JWT claims preview" subtitle="What goes in the bearer token">
        <pre style={{ margin: 0, padding: 12, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.55, color: "var(--fg)" }}>{`{
  "sub": "u_jamie",
  "tid": "tenant_01h9a2",
  "roles": ["operator"],
  "scope": [
    "agent:write",
    "memory:write",
    "audit:read",
    "hitl:write"
  ],
  "iat": 1715850000,
  "exp": 1715853600
}`}</pre>
      </Card>
    </div>
  </div>
);

const PermBadge = ({ p }) => {
  const map = {
    admin: { bg: "var(--danger)", label: "ADM" },
    write: { bg: "var(--warning)", label: "RW"  },
    read:  { bg: "var(--success)",  label: "R"   },
  };
  const m = map[p];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      width: 36, height: 22, borderRadius: 4,
      background: `oklch(from ${m.bg} l c h / 0.14)`,
      border: `1px solid oklch(from ${m.bg} l c h / 0.4)`,
      color: m.bg, fontSize: 10.5, fontFamily: "var(--font-mono)", fontWeight: 600,
    }}>{m.label}</span>
  );
};

Object.assign(window, { StateInspector, Compaction, Workflows, ErrorPolicyPage, RBACPage });
