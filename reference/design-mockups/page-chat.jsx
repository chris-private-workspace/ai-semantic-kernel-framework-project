/* global React, Icon, Button, Badge, Card, Tabs, Switch, RiskBadge */
const { useState: useCs, useEffect: useEcs, useRef: useRcs } = React;

// ============ Sessions ============
const SESSIONS = [
  { id: "sess_4tk2p", title: "payment-gateway 5xx spike", agent: "incident-responder", turns: 17, status: "running", time: "now", domain: "incident" },
  { id: "sess_91kxu", title: "Q4 compliance audit — PCI scope", agent: "compliance-auditor", turns: 42, status: "hitl", time: "8m ago", domain: "audit" },
  { id: "sess_2afpw", title: "Nightly patrol — APAC clusters", agent: "patrol-runner", turns: 28, status: "done", time: "1h ago", domain: "patrol" },
  { id: "sess_88vqc", title: "RCA: cache eviction storm 2026-05-12", agent: "rca-bot", turns: 64, status: "done", time: "yesterday", domain: "rca" },
  { id: "sess_kpw01", title: "Change request CHG-4821 review", agent: "change-reviewer", turns: 9, status: "done", time: "yesterday", domain: "incident" },
  { id: "sess_qqx88", title: "Anomaly: tenant_3kp9 token spike", agent: "compliance-auditor", turns: 12, status: "done", time: "2d ago", domain: "audit" },
];

// ============ Turn data — the hero conversation ============
// Realistic SRE incident investigation. Mix of thinking, tool calls, verification,
// memory ops, subagent fork, HITL pause.
const TURNS = [
  {
    role: "user", at: "10:42:18", id: "t0",
    text: "payment-gateway 5xx rate is at 3.4% over the last 10 minutes (SLO breach at 1%). Investigate, find root cause, and propose an action. You can run any read tool; writes need my approval.",
  },
  {
    role: "agent", at: "10:42:19", id: "t1", stopReason: "tool_use", duration: "1.42s",
    blocks: [
      { type: "thinking", text: "User flagged a P1 candidate. SLO at 1% breached. I need a parallel investigation: (1) check incidents table for prior similar, (2) pull logs from payment-gateway over the last 30m, (3) check downstream dependencies (auth-svc, ledger-db). Will fork three read subagents to do this concurrently — faster than serial." },
      { type: "tool", name: "incidents.list", status: "ok", duration: "82ms", input: '{ "service": "payment-gateway", "since": "30d", "kind": "5xx" }', output: '[{ "id": "INC-4012", "title": "5xx spike from idle DB connections", "resolved_at": "2026-04-19", "resolution": "increased pgbouncer pool from 50 → 200" }, { "id": "INC-3987", ... }]' },
    ],
  },
  {
    role: "agent", at: "10:42:21", id: "t2", stopReason: "subagent_fork", duration: "0.91s",
    blocks: [
      { type: "thinking", text: "INC-4012 from 27 days ago looks identical. Confirming with current metrics. Forking 3 subagents — fan-out concurrent." },
      { type: "subagent_fork", agents: [
        { id: "sa_log", name: "log-scanner", task: "Tail payment-gateway logs · last 30m · grep 5xx", status: "running", turns: 3 },
        { id: "sa_dep", name: "dep-checker", task: "Check auth-svc and ledger-db health", status: "running", turns: 2 },
        { id: "sa_met", name: "metrics-pull", task: "Pull pgbouncer pool utilization", status: "done", turns: 1 },
      ]},
    ],
  },
  {
    role: "agent", at: "10:42:24", id: "t3", stopReason: "tool_use", duration: "2.4s",
    blocks: [
      { type: "memory", op: "READ", scope: "user.jamie", entry: "preferences.rca_format = `5-whys + timeline`" },
      { type: "tool", name: "metrics.query", status: "ok", duration: "210ms", input: '{ "metric": "pgbouncer.pool.in_use", "service": "payment-gateway", "window": "30m" }', output: 'series: [{ "ts": "10:12", "v": 48 }, { "ts": "10:17", "v": 50 }, ..., { "ts": "10:40", "v": 50, "saturated": true }]\npool_max: 50 · saturation_since: 10:22 (20m)' },
      { type: "verification", ok: true, claim: "pgbouncer pool saturated at 50/50 since 10:22", evidence: "metrics.query series matches; saturation_since field is non-null" },
    ],
  },
  {
    role: "agent", at: "10:42:27", id: "t4", stopReason: "tool_use", duration: "1.1s",
    blocks: [
      { type: "thinking", text: "Confirmed: same failure mode as INC-4012. pgbouncer pool size never got bumped on payment-gateway-canary (deployed last week). Fix: raise pool size to 200, matching prod. This is a write action — requires HITL approval per policy." },
      { type: "memory", op: "WRITE", scope: "session.sess_4tk2p", entry: "root_cause = pgbouncer pool too small on canary" },
    ],
  },
  {
    role: "hitl", at: "10:42:28", id: "t5",
    title: "Approve write: kubectl set env on payment-gateway-canary",
    severity: "risk-high",
    tool: "k8s.set_env",
    payload: '{\n  "namespace": "prod-payments",\n  "deployment": "payment-gateway-canary",\n  "env": {\n    "PGBOUNCER_POOL_SIZE": "200"\n  },\n  "rolling": true\n}',
    rationale: "Match prod config; verified via INC-4012 fix and current pool saturation evidence.",
    countdown: "4m 12s",
  },
  {
    role: "agent", at: "10:46:40", id: "t6", stopReason: "end_turn", duration: "—", waiting: true,
    blocks: [
      { type: "thinking", text: "Waiting for operator decision. Cannot proceed without write approval." },
    ],
  },
];

// ============ Page: Chat V2 ============
const ChatV2 = () => {
  const [activeId, setActiveId] = useCs("sess_4tk2p");
  const [inspector, setInspector] = useCs("turn"); // turn | trace | memory | subagent
  const [listOpen, setListOpen] = useCs(true);
  const [inspOpen, setInspOpen] = useCs(true);
  return (
    <div className="chat-shell" data-list={listOpen ? "open" : "hidden"} data-insp={inspOpen ? "open" : "hidden"}>
      <SessionList active={activeId} onSelect={setActiveId} />
      <div className="chat-stream">
        <ChatHeader listOpen={listOpen} inspOpen={inspOpen} onToggleList={() => setListOpen(o => !o)} onToggleInsp={() => setInspOpen(o => !o)} />
        <div style={{ flex: 1, overflowY: "auto" }}>
          {TURNS.map(t => <TurnRender key={t.id} turn={t} />)}
        </div>
        <Composer />
      </div>
      <ChatInspector tab={inspector} onTab={setInspector} />
    </div>
  );
};

const ChatHeader = ({ listOpen, inspOpen, onToggleList, onToggleInsp }) => (
  <div style={{ padding: "10px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10, background: "var(--bg-1)" }}>
    <button className="panel-toggle" data-active={listOpen} onClick={onToggleList} title="Toggle session list">
      <Icon name="panel" size={14} />
    </button>
    <div style={{ width: 26, height: 26, borderRadius: 6, background: "linear-gradient(135deg, var(--danger), var(--warning))", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      <Icon name="warn" size={13} style={{ color: "white" }} />
    </div>
    <div style={{ minWidth: 0, overflow: "hidden" }}>
      <div style={{ fontWeight: 600, fontSize: 13, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>payment-gateway 5xx spike</div>
      <div className="row" style={{ gap: 6, marginTop: 2, flexWrap: "wrap" }}>
        <Badge>incident-responder</Badge>
        <Badge tone="thinking">claude-haiku-4-5</Badge>
        <span className="provider-neutral">provider: neutral</span>
        <span className="subtle" style={{ fontSize: 11 }}>· 17 turns</span>
      </div>
    </div>
    <div className="grow" />
    <span className="row" style={{ gap: 6 }}>
      <span className="live-dot" />
      <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>streaming</span>
    </span>
    <Button variant="ghost" size="sm" icon="loop" onClick={() => location.hash = "loop-debug"}>Loop</Button>
    <Button variant="ghost" size="sm" icon="audit">Audit</Button>
    <button className="panel-toggle" data-active={inspOpen} onClick={onToggleInsp} title="Toggle inspector">
      <Icon name="panel" size={14} style={{ transform: "scaleX(-1)" }} />
    </button>
  </div>
);

const SessionList = ({ active, onSelect }) => (
  <div className="chat-list">
    <div style={{ padding: "10px 12px 8px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 6 }}>
      <Button variant="primary" size="sm" icon="plus">New session</Button>
      <Button variant="ghost" size="sm" icon="filter" />
    </div>
    <div style={{ padding: "8px 12px 6px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <span className="mono" style={{ fontSize: 10.5, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Sessions</span>
      <span className="mono" style={{ fontSize: 10.5, color: "var(--fg-subtle)" }}>{SESSIONS.length}</span>
    </div>
    {SESSIONS.map(s => (
      <div key={s.id} className="session-item" data-active={active === s.id} onClick={() => onSelect(s.id)}>
        <div className="row" style={{ gap: 6, marginBottom: 4 }}>
          <DomainDot d={s.domain} />
          <span className="session-title grow">{s.title}</span>
          {s.status === "running" && <span className="live-dot" title="running" />}
          {s.status === "hitl" && <Badge tone="warning">HITL</Badge>}
        </div>
        <div className="session-meta">
          <span>{s.agent}</span>
          <span>·</span>
          <span>{s.turns} turns</span>
          <span>·</span>
          <span>{s.time}</span>
        </div>
      </div>
    ))}
  </div>
);

const DomainDot = ({ d }) => {
  const map = { incident: "var(--danger)", audit: "var(--memory)", patrol: "var(--tool)", rca: "var(--thinking)" };
  return <span style={{ width: 7, height: 7, borderRadius: 50, background: map[d] || "var(--fg-muted)", flexShrink: 0 }} />;
};

// ============ Turn renderer ============
const TurnRender = ({ turn }) => {
  if (turn.role === "user") return <UserTurn turn={turn} />;
  if (turn.role === "hitl") return <HITLTurn turn={turn} />;
  return <AgentTurn turn={turn} />;
};

const UserTurn = ({ turn }) => (
  <div className="turn" data-role="user">
    <div className="turn-rail" />
    <div className="turn-marker" />
    <div className="turn-head">
      <span className="role">Jamie Liu</span>
      <span className="route-pill">operator</span>
      <span className="mono subtle">{turn.at}</span>
    </div>
    <div className="turn-body" style={{ fontSize: 13 }}>{turn.text}</div>
  </div>
);

const AgentTurn = ({ turn }) => (
  <div className="turn" data-role="agent">
    <div className="turn-rail" />
    <div className="turn-marker" />
    <div className="turn-head">
      <span className="role">incident-responder</span>
      <Badge tone="primary">turn {turn.id.replace("t", "")}</Badge>
      {turn.stopReason && <Badge>stop: {turn.stopReason}</Badge>}
      {turn.duration && <span className="mono subtle">· {turn.duration}</span>}
      <span className="mono subtle">· {turn.at}</span>
      {turn.waiting && <span className="row" style={{ gap: 5, marginLeft: 6 }}>
        <span className="live-dot" style={{ background: "var(--warning)" }} />
        <span className="mono" style={{ fontSize: 11, color: "var(--warning)" }}>awaiting approval</span>
      </span>}
    </div>
    <div className="turn-body">
      {turn.blocks.map((b, i) => <Block key={i} b={b} />)}
    </div>
  </div>
);

const Block = ({ b }) => {
  if (b.type === "thinking") {
    return (
      <div className="block thinking">
        <div className="label"><Icon name="thinking" size={11} /> thinking</div>
        {b.text}
      </div>
    );
  }
  if (b.type === "tool") {
    return (
      <div className="block tool-call">
        <div className="block tool-call-head">
          <Icon name="tool" size={13} style={{ color: "var(--tool)" }} />
          <span className="name">{b.name}</span>
          <span className="row" style={{ marginLeft: "auto", gap: 6 }}>
            <Badge tone={b.status === "ok" ? "success" : "danger"} dot>{b.status === "ok" ? "success" : "error"}</Badge>
            <span className="mono subtle" style={{ fontSize: 10.5 }}>{b.duration}</span>
          </span>
        </div>
        <div className="block tool-call-body"><span style={{ color: "var(--fg-subtle)" }}>// input</span>{"\n"}{b.input}</div>
        <div className="block tool-call-body result"><span style={{ color: "var(--fg-subtle)" }}>// output</span>{"\n"}{b.output}</div>
      </div>
    );
  }
  if (b.type === "memory") {
    return (
      <div className="block memory-op">
        <Icon name="memory" size={12} style={{ color: "var(--memory)" }} />
        <span className="label">{b.op}</span>
        <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>scope: {b.scope}</span>
        <span className="mono subtle" style={{ marginLeft: "auto" }}>{b.entry}</span>
      </div>
    );
  }
  if (b.type === "verification") {
    return (
      <div className={`block verification ${!b.ok ? "failed" : ""}`}>
        <Icon name={b.ok ? "check" : "x"} size={13} style={{ color: b.ok ? "var(--success)" : "var(--danger)" }} />
        <div>
          <div style={{ fontWeight: 500 }}>{b.claim}</div>
          <div className="subtle" style={{ fontSize: 11, marginTop: 2 }}>evidence: {b.evidence}</div>
        </div>
      </div>
    );
  }
  if (b.type === "subagent_fork") {
    return (
      <div className="subagent-tree">
        <div className="row" style={{ padding: "4px 8px", fontSize: 11, color: "var(--fg-muted)" }}>
          <Icon name="fork" size={12} />
          <span className="mono" style={{ color: "var(--primary)", fontWeight: 600 }}>Fork · concurrent</span>
          <span className="mono subtle">spawned {b.agents.length} subagents</span>
        </div>
        {b.agents.map(a => (
          <div key={a.id} className="subagent-row">
            <Icon name="chevron_right" size={12} className="subtle" />
            <span style={{ color: "var(--primary)" }}>{a.name}</span>
            <span className="subtle">·</span>
            <span style={{ color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{a.task}</span>
            <Badge tone={a.status === "done" ? "success" : "info"} dot>{a.status}</Badge>
            <span className="subtle">{a.turns}t</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

// ============ HITL approval card (inline in chat) ============
const HITLTurn = ({ turn }) => (
  <div className="turn">
    <div className="turn-rail" />
    <div className="turn-marker" style={{ background: "var(--warning)", borderColor: "var(--warning)" }} />
    <div className="turn-head">
      <span className="role" style={{ color: "var(--warning)" }}>HITL approval required</span>
      <Badge tone="warning">always_ask</Badge>
      <span className="mono subtle">· {turn.at}</span>
    </div>
    <div className="turn-body">
      <div className="hitl-card" data-severity={turn.severity}>
        <div className="hitl-card-bar" />
        <div className="hitl-head">
          <span className="icon-ring"><Icon name="shield" size={13} /></span>
          {turn.title}
          <span className="hitl-countdown">
            <Icon name="clock" size={11} />
            SLA <span style={{ color: "var(--warning)" }}>{turn.countdown}</span>
          </span>
        </div>
        <div className="hitl-meta">
          <span className="row" style={{ gap: 5 }}>severity: <RiskBadge level="high" /></span>
          <span className="row" style={{ gap: 5 }}>tool: <span className="mono" style={{ color: "var(--tool)" }}>{turn.tool}</span></span>
          <span className="row" style={{ gap: 5 }}>policy: <Badge>always_ask</Badge></span>
          <span className="row" style={{ gap: 5 }}>scope: <Badge>tenant.acme-prod</Badge></span>
        </div>
        <div style={{ fontSize: 12.5, color: "var(--fg-muted)", marginBottom: 6 }}>
          <strong style={{ color: "var(--fg)", fontWeight: 600 }}>Rationale.</strong> {turn.rationale}
        </div>
        <div className="hitl-payload">{turn.payload}</div>
        <div className="hitl-actions">
          <Button variant="success" size="sm" icon="check">Approve & continue</Button>
          <Button variant="outline" size="sm">Approve with edits</Button>
          <Button variant="danger" size="sm" icon="x">Reject</Button>
          <Button variant="ghost" size="sm">Escalate to L2</Button>
          <span className="row subtle" style={{ marginLeft: "auto", fontSize: 11 }}>
            <Icon name="audit" size={12} />
            <span className="mono">audit_id: a8f3.k2p1</span>
          </span>
        </div>
      </div>
    </div>
  </div>
);

// ============ Composer ============
const Composer = () => {
  const [attachments, setAttachments] = useCs([]);
  const fileRef = useRcs(null);
  const onPick = (e) => {
    const files = [...(e.target.files || [])];
    setAttachments(a => [...a, ...files.map(f => ({ name: f.name, size: f.size, kind: f.type.startsWith("image/") ? "image" : f.type.includes("pdf") ? "pdf" : f.type.includes("text") ? "text" : "file" }))]);
    e.target.value = "";
  };
  const onDrop = (e) => { e.preventDefault(); onPick({ target: { files: e.dataTransfer.files, value: "" } }); };
  return (
    <div className="composer" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <div className="composer-inner">
        {attachments.length > 0 && (
          <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 4 }}>
            {attachments.map((a, i) => (
              <span key={i} style={{
                display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 8px",
                background: "var(--bg-3)", border: "1px solid var(--border)", borderRadius: 4,
                fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--fg)",
              }}>
                <Icon name={a.kind === "image" ? "eye" : a.kind === "pdf" ? "log" : a.kind === "text" ? "code" : "log"} size={11} style={{ color: a.kind === "image" ? "var(--memory)" : a.kind === "pdf" ? "var(--danger)" : "var(--info)" }} />
                <span>{a.name}</span>
                <span className="subtle">· {(a.size / 1024).toFixed(1)}KB</span>
                <button onClick={() => setAttachments(arr => arr.filter((_, j) => j !== i))} style={{ marginLeft: 2, color: "var(--fg-subtle)", cursor: "pointer", display: "flex", alignItems: "center" }}>
                  <Icon name="x" size={11} />
                </button>
              </span>
            ))}
          </div>
        )}
        <textarea
          className="composer-input"
          rows="2"
          placeholder={attachments.length ? "Add context or send…" : "Ask the agent — drag files in, paste images, or type. For example, “Investigate INC-4087 and propose an action plan”"}
        />
        <div className="composer-tools">
          <input ref={fileRef} type="file" multiple accept="image/*,.pdf,.txt,.md,.json,.yaml,.log,.csv" style={{ display: "none" }} onChange={onPick} />
          <Button variant="ghost" size="sm" icon="plus" onClick={() => fileRef.current?.click()}>Attach</Button>
          <Button variant="ghost" size="sm" icon="branch">Tools (24)</Button>
          <Button variant="ghost" size="sm" icon="memory">Memory scope</Button>
          <div className="grow" />
          <Badge>claude-haiku-4-5</Badge>
          <span className="provider-neutral">neutral</span>
          <Button variant="primary" size="sm" iconRight="send">Send</Button>
        </div>
      </div>
      <div className="subtle" style={{ fontSize: 10.5, marginTop: 4, paddingLeft: 4 }}>
        <Icon name="download" size={10} style={{ verticalAlign: "middle", marginRight: 4 }} />
        Drop files anywhere · accepts images / pdf / txt / md / json / yaml / log / csv · max 25MB each
      </div>
    </div>
  );
};

// ============ Right inspector ============
const ChatInspector = ({ tab, onTab }) => (
  <div className="chat-inspector">
    <div style={{ borderBottom: "1px solid var(--border)" }}>
      <Tabs
        value={tab}
        onChange={onTab}
        items={[
          { id: "turn", label: "Turn" },
          { id: "trace", label: "Trace" },
          { id: "memory", label: "Memory" },
          { id: "subagent", label: "Tree" },
        ]}
      />
    </div>
    {tab === "turn" && <InspectorTurn />}
    {tab === "trace" && <InspectorTrace />}
    {tab === "memory" && <InspectorMemory />}
    {tab === "subagent" && <InspectorTree />}
  </div>
);

const InspectorTurn = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontFamily: "var(--font-mono)" }}>Turn 4 · tool_use</div>
    <div className="col" style={{ gap: 8, fontSize: 12 }}>
      <KV k="stop_reason" v={<Badge>tool_use</Badge>} />
      <KV k="duration" v="2.41s" mono />
      <KV k="tokens.in" v="14,820" mono />
      <KV k="tokens.out" v="186" mono />
      <KV k="tokens.thinking" v="412" mono />
      <KV k="cost" v="$0.0142" mono />
      <KV k="trace_id" v="6f3a.…b2k1" mono />
      <KV k="span_id" v="a04.zp2" mono />
      <div className="thin-rule" />
      <div style={{ fontSize: 11, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: "var(--font-mono)" }}>Block sequence</div>
      <div className="col" style={{ gap: 3 }}>
        <EventLine type="thinking" text="thinking · 0.42s · 412 tok" tone="var(--thinking)" />
        <EventLine type="tool_call" text="metrics.query · 210ms" tone="var(--tool)" />
        <EventLine type="verification" text="claim verified · 18ms" tone="var(--success)" />
        <EventLine type="memory" text="WRITE session" tone="var(--memory)" />
      </div>
      <div className="thin-rule" />
      <Button variant="outline" size="sm" icon="audit">Open audit entry</Button>
      <Button variant="ghost" size="sm" icon="loop">Open in Loop Debug</Button>
    </div>
  </div>
);

const KV = ({ k, v, mono }) => (
  <div className="spread" style={{ fontSize: 12 }}>
    <span className="muted">{k}</span>
    <span className={mono ? "mono tnum" : ""}>{v}</span>
  </div>
);

const EventLine = ({ type, text, tone }) => (
  <div className="row" style={{ gap: 6, padding: "3px 0", fontFamily: "var(--font-mono)", fontSize: 11 }}>
    <span style={{ width: 6, height: 6, borderRadius: "50%", background: tone }} />
    <span style={{ color: tone, minWidth: 78 }}>{type}</span>
    <span className="subtle">{text}</span>
  </div>
);

const InspectorTrace = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontFamily: "var(--font-mono)" }}>Cat 12 · OTel spans · 17 turns</div>
    {[
      { name: "loop.iteration_0", d: 1.42, c: "var(--primary)", off: 0 },
      { name: "├─ tool.incidents.list", d: 0.08, c: "var(--tool)", off: 1 },
      { name: "loop.iteration_1", d: 0.91, c: "var(--primary)", off: 0 },
      { name: "├─ subagent.spawn", d: 0.04, c: "var(--thinking)", off: 1 },
      { name: "│  ├─ sa.log-scanner", d: 2.20, c: "var(--info)", off: 2 },
      { name: "│  ├─ sa.dep-checker", d: 1.86, c: "var(--info)", off: 2 },
      { name: "│  └─ sa.metrics-pull", d: 0.32, c: "var(--info)", off: 2 },
      { name: "loop.iteration_2", d: 2.40, c: "var(--primary)", off: 0 },
      { name: "├─ memory.read", d: 0.02, c: "var(--memory)", off: 1 },
      { name: "├─ tool.metrics.query", d: 0.21, c: "var(--tool)", off: 1 },
      { name: "└─ verification.check", d: 0.02, c: "var(--success)", off: 1 },
      { name: "loop.iteration_3", d: 1.10, c: "var(--primary)", off: 0 },
      { name: "├─ memory.write", d: 0.04, c: "var(--memory)", off: 1 },
      { name: "hitl.requested", d: 0.01, c: "var(--warning)", off: 0 },
    ].map((s, i) => {
      const max = 2.5;
      const w = Math.max(2, (s.d / max) * 100);
      return (
        <div key={i} className="row" style={{ gap: 8, padding: "2px 0", fontSize: 10.5, fontFamily: "var(--font-mono)" }}>
          <span style={{ width: 200, color: "var(--fg-muted)", paddingLeft: s.off * 10, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.name}</span>
          <span style={{ flex: 1, height: 8, background: "var(--bg-2)", borderRadius: 2, overflow: "hidden", position: "relative" }}>
            <span style={{ display: "block", width: w + "%", height: "100%", background: s.c, borderRadius: 2 }} />
          </span>
          <span style={{ width: 50, textAlign: "right", color: "var(--fg-subtle)" }}>{s.d.toFixed(2)}s</span>
        </div>
      );
    })}
  </div>
);

const InspectorMemory = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontFamily: "var(--font-mono)" }}>Memory ops · this session</div>
    {[
      { op: "READ", scope: "user.jamie", k: "preferences.rca_format", v: "5-whys + timeline", at: "10:42:24" },
      { op: "READ", scope: "tenant.acme-prod", k: "policies.hitl.risk_high", v: "always_ask", at: "10:42:26" },
      { op: "WRITE", scope: "session.sess_4tk2p", k: "root_cause", v: "pgbouncer pool too small", at: "10:42:27" },
      { op: "WRITE", scope: "session.sess_4tk2p", k: "evidence", v: "[metrics, INC-4012]", at: "10:42:27" },
    ].map((m, i) => (
      <div key={i} style={{ padding: "7px 0", borderBottom: "1px solid var(--border)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
        <div className="row" style={{ gap: 6 }}>
          <Badge tone="memory">{m.op}</Badge>
          <span style={{ color: "var(--fg-muted)" }}>{m.scope}</span>
          <span className="subtle" style={{ marginLeft: "auto" }}>{m.at}</span>
        </div>
        <div style={{ marginTop: 4, color: "var(--fg)" }}>{m.k} <span className="subtle">=</span> {m.v}</div>
      </div>
    ))}
  </div>
);

const InspectorTree = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8, fontFamily: "var(--font-mono)" }}>Subagent tree · live</div>
    <div className="subagent-tree">
      <div className="subagent-row">
        <Icon name="chat" size={12} style={{ color: "var(--primary)" }} />
        <span style={{ color: "var(--primary)", fontWeight: 600 }}>incident-responder</span>
        <span className="subtle">root</span>
        <Badge tone="warning" style={{ marginLeft: "auto" }}>hitl-paused</Badge>
      </div>
      <div className="indent">
        <div className="subagent-row">
          <Icon name="fork" size={11} style={{ color: "var(--thinking)" }} />
          <span style={{ color: "var(--thinking)" }}>fork · t1</span>
          <span className="subtle">·</span>
          <span style={{ color: "var(--fg-muted)" }}>3 children</span>
        </div>
        <div className="indent">
          {[
            { name: "log-scanner", task: "tail · grep 5xx", turns: 3, status: "done" },
            { name: "dep-checker", task: "auth-svc · ledger-db", turns: 2, status: "done" },
            { name: "metrics-pull", task: "pgbouncer pool", turns: 1, status: "done" },
          ].map(s => (
            <div key={s.name} className="subagent-row">
              <Icon name="chevron_right" size={11} className="subtle" />
              <span style={{ color: "var(--info)" }}>{s.name}</span>
              <span className="subtle" style={{ fontSize: 10 }}>· {s.turns}t</span>
              <span className="subtle grow" style={{ marginLeft: 4 }}>{s.task}</span>
              <Badge tone="success" dot>{s.status}</Badge>
            </div>
          ))}
        </div>
      </div>
    </div>
    <div className="thin-rule" />
    <div className="col" style={{ gap: 5, fontSize: 11, color: "var(--fg-muted)" }}>
      <div className="spread"><span>Mode</span><Badge>Fork concurrent</Badge></div>
      <div className="spread"><span>Depth</span><span className="mono">2</span></div>
      <div className="spread"><span>Concurrency</span><span className="mono">3 / 5</span></div>
      <div className="spread"><span>Tokens (subtree)</span><span className="mono">41,820</span></div>
    </div>
  </div>
);

Object.assign(window, { ChatV2 });
